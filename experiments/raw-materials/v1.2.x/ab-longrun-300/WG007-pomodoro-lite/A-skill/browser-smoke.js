"use strict";
// Browser smoke test via playwright-core + system Chrome/Edge if available.
// Writes evidence to browser-smoke.json and shots/*.png.
const fs = require("fs");
const path = require("path");

function writeResult(obj) {
  fs.writeFileSync(path.join(__dirname, "browser-smoke.json"), JSON.stringify(obj, null, 2));
  console.log(JSON.stringify(obj, null, 2));
}

async function main() {
  let chromium;
  try {
    ({ chromium } = require("playwright-core"));
  } catch (e) {
    writeResult({ ok: false, reason: "playwright-core not installed", error: String(e) });
    process.exit(2);
  }

  const htmlPath = path.join(__dirname, "pomodoro.html");
  const url = "file:///" + htmlPath.replace(/\\/g, "/");
  const channels = ["chrome", "msedge"];
  let browser = null;
  let launched = null;
  for (const channel of channels) {
    try {
      browser = await chromium.launch({ channel, headless: true });
      launched = channel;
      break;
    } catch (e) {
      // try next
    }
  }
  if (!browser) {
    try {
      browser = await chromium.launch({ headless: true });
      launched = "bundled-or-default";
    } catch (e) {
      writeResult({
        ok: false,
        reason: "no browser launchable",
        tried: channels,
        error: String(e && e.message ? e.message : e)
      });
      process.exit(2);
    }
  }

  const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
  const requests = [];
  page.on("request", (req) => requests.push(req.url()));

  const shotsDir = path.join(__dirname, "shots");
  if (!fs.existsSync(shotsDir)) fs.mkdirSync(shotsDir);

  const readUi = async () =>
    page.evaluate(() => ({
      clock: document.getElementById("clock").textContent,
      state: document.getElementById("stateText").textContent,
      primary: document.getElementById("btnPrimary").textContent,
      minutes: document.getElementById("minutesInput").value,
      minutesDisabled: document.getElementById("minutesInput").disabled,
      note: document.getElementById("note").textContent
    }));

  const steps = [];
  const snap = async (label) => {
    const ui = await readUi();
    steps.push({ label, ui });
    return ui;
  };

  await page.goto(url);
  await page.waitForTimeout(150);
  await snap("initial");
  await page.screenshot({ path: path.join(shotsDir, "01-ready.png") });

  // --- start ---
  await page.click("#btnPrimary");
  // wait >1s so ceil-based display drops a second
  await page.waitForTimeout(1300);
  const running = await snap("after-start-1.3s");
  await page.screenshot({ path: path.join(shotsDir, "02-running.png") });

  // --- pause ---
  await page.click("#btnPrimary");
  await page.waitForTimeout(80);
  const paused = await snap("after-pause");
  await page.screenshot({ path: path.join(shotsDir, "03-paused.png") });
  const pausedClock = paused.clock;
  await page.waitForTimeout(400);
  const stillPaused = await readUi();

  // --- resume ---
  await page.click("#btnPrimary");
  await page.waitForTimeout(80);
  await snap("after-resume");

  // --- reset ---
  await page.click("#btnReset");
  await page.waitForTimeout(50);
  const reset = await snap("after-reset");
  await page.screenshot({ path: path.join(shotsDir, "04-reset.png") });

  // --- set minutes ---
  await page.fill("#minutesInput", "5");
  await page.press("#minutesInput", "Enter");
  await page.waitForTimeout(50);
  const fiveMin = await snap("after-set-5min");

  await page.fill("#minutesInput", "0");
  await page.press("#minutesInput", "Enter");
  await page.waitForTimeout(50);
  const invalid0 = await snap("after-invalid-0");

  await page.fill("#minutesInput", "61");
  await page.press("#minutesInput", "Enter");
  await page.waitForTimeout(50);
  const invalid61 = await snap("after-invalid-61");

  // type=number rejects non-numeric fill in Playwright; set value + Enter via DOM
  await page.evaluate(() => {
    var el = document.getElementById("minutesInput");
    el.value = "abc";
    el.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  });
  await page.waitForTimeout(50);
  const invalidAbc = await snap("after-invalid-abc");

  // restore 1 minute and finish via clock fast-forward
  await page.fill("#minutesInput", "1");
  await page.press("#minutesInput", "Enter");
  await page.waitForTimeout(50);
  await snap("before-finish-run");
  await page.click("#btnPrimary");
  await page.waitForTimeout(50);
  const locked = await snap("finish-run-locked");

  // Fast-forward wall clock past end. Date.now is used by the timer.
  const ff = await page.evaluate(() => {
    // Shift Date.now forward by 61s so next tick sees remaining<=0
    var realNow = Date.now;
    var offset = 61 * 1000;
    Date.now = function () {
      return realNow.call(Date) + offset;
    };
    return { offsetApplied: offset };
  });
  // wait for interval tick (~200ms)
  await page.waitForTimeout(400);
  const finished = await snap("after-clock-ffinish");
  await page.screenshot({ path: path.join(shotsDir, "05-finished.png") });

  const external = requests.filter((u) => /^https?:/i.test(u));

  const checks = {
    initialClock25: steps.find((s) => s.label === "initial").ui.clock === "25:00",
    initialReady: steps.find((s) => s.label === "initial").ui.state === "就绪",
    startRunning: running.state === "进行中" && running.primary === "暂停",
    startLocksConfig: running.minutesDisabled === true,
    clockTickedWithin1_3s: running.clock !== "25:00",
    pausePaused: paused.state === "已暂停" && paused.primary === "继续",
    pauseFreezesClock: stillPaused.clock === pausedClock,
    resumeRunning: steps.find((s) => s.label === "after-resume").ui.state === "进行中",
    resetReady25: reset.state === "就绪" && reset.clock === "25:00",
    setFiveMin: fiveMin.clock === "05:00" && fiveMin.minutes === "5",
    reject0: invalid0.note.indexOf("正整数") !== -1 && invalid0.clock === "05:00",
    reject61: invalid61.note.indexOf("正整数") !== -1 && invalid61.clock === "05:00",
    rejectAbc: invalidAbc.note.indexOf("正整数") !== -1 && invalidAbc.clock === "05:00",
    finishLocksDuringRun: locked.minutesDisabled === true,
    finishStatusTimeUp: finished.state === "时间到",
    finishClockZero: finished.clock === "00:00",
    finishPrimaryStart: finished.primary === "开始",
    finishUnlocksConfig: finished.minutesDisabled === false,
    noHttpExternal: external.length === 0,
    clockFastForward: ff.offsetApplied === 61000
  };

  const allOk = Object.keys(checks).every((k) => checks[k]);
  const failed = Object.keys(checks).filter((k) => !checks[k]);

  await browser.close();

  writeResult({
    ok: allOk,
    failedChecks: failed,
    launched,
    url,
    checks,
    steps,
    externalRequests: requests,
    screenshots: [
      "shots/01-ready.png",
      "shots/02-running.png",
      "shots/03-paused.png",
      "shots/04-reset.png",
      "shots/05-finished.png"
    ],
    methods: [
      "playwright-core headless " + launched,
      "real clicks on #btnPrimary / #btnReset",
      "fill+Enter on #minutesInput",
      "Date.now offset +61s to reach finish without waiting 60s wall time",
      "screenshots captured under shots/"
    ]
  });

  process.exit(allOk ? 0 : 1);
}

main().catch((e) => {
  writeResult({ ok: false, reason: "exception", error: String(e && e.stack ? e.stack : e) });
  process.exit(2);
});
