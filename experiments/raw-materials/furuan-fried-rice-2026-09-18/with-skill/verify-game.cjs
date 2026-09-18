const path = require("path");
const { pathToFileURL } = require("url");
const {
  chromium,
} = require("C:/Users/yutia/AppData/Roaming/npm/node_modules/@playwright/cli/node_modules/playwright");

const gamePath = "C:/Users/yutia/Desktop/弗糯糯炒饭/index.html";
const outDir = "C:/Users/yutia/Desktop/弗糯糯炒饭";

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath:
      "C:/Users/yutia/AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe",
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });

  await page.goto(pathToFileURL(gamePath).href);
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(outDir, "verify-title.png") });

  // title visible?
  const titleActive = await page.evaluate(
    () => document.getElementById("screen-title").classList.contains("active")
  );

  await page.click("#btn-start");
  await page.waitForTimeout(500);
  const gameActive = await page.evaluate(
    () => document.getElementById("screen-game").classList.contains("active")
  );
  await page.screenshot({ path: path.join(outDir, "verify-game.png") });

  // Play: repeatedly press space when marker is near perfect zone
  // Hook into marker via DOM
  async function hitWhenReady(maxMs) {
    const start = Date.now();
    while (Date.now() - start < maxMs) {
      const ready = await page.evaluate(() => {
        const track = document.getElementById("timing-track");
        const marker = document.getElementById("marker");
        const zone = document.getElementById("zone-perfect");
        if (!track || !marker || !zone) return false;
        const tr = track.getBoundingClientRect();
        const mr = marker.getBoundingClientRect();
        const zr = zone.getBoundingClientRect();
        if (zr.width < 1) return false;
        const mc = mr.left + mr.width / 2;
        const zc = zr.left + zr.width / 2;
        return Math.abs(mc - zc) < zr.width * 0.55;
      });
      if (ready) {
        await page.keyboard.press("Space");
        await page.waitForTimeout(120);
        return true;
      }
      await page.waitForTimeout(16);
    }
    return false;
  }

  // Run through steps (max ~60s)
  const stepLog = [];
  for (let i = 0; i < 40; i++) {
    const phase = await page.evaluate(() => {
      const result = document.getElementById("screen-result");
      const game = document.getElementById("screen-game");
      if (result.classList.contains("active")) return "result";
      if (!game.classList.contains("active")) return "other";
      return document.getElementById("hud-step-name").textContent;
    });
    stepLog.push(phase);
    if (phase === "result") break;

    // toss steps may need multiple hits
    for (let t = 0; t < 5; t++) {
      const still = await page.evaluate(() => {
        const result = document.getElementById("screen-result");
        if (result.classList.contains("active")) return "result";
        return document.getElementById("hud-step-name").textContent;
      });
      if (still === "result") break;
      const ok = await hitWhenReady(2500);
      if (!ok) {
        // force miss path by waiting for auto miss
        await page.waitForTimeout(400);
      }
      await page.waitForTimeout(450);
    }
  }

  await page.waitForTimeout(800);
  const finalScreen = await page.evaluate(() => {
    if (document.getElementById("screen-result").classList.contains("active")) {
      return {
        screen: "result",
        title: document.getElementById("result-title").textContent,
        score: document.getElementById("result-score").textContent,
        combo: document.getElementById("result-combo").textContent,
        perfect: document.getElementById("result-perfect").textContent,
        miss: document.getElementById("result-miss").textContent,
        stars: document.getElementById("result-stars").textContent,
      };
    }
    return {
      screen: "game",
      step: document.getElementById("hud-step-name").textContent,
      score: document.getElementById("hud-score").textContent,
    };
  });

  await page.screenshot({ path: path.join(outDir, "verify-final.png") });

  // retry button
  if (finalScreen.screen === "result") {
    await page.click("#btn-retry");
    await page.waitForTimeout(400);
    const afterRetry = await page.evaluate(() =>
      document.getElementById("screen-game").classList.contains("active")
    );
    finalScreen.retryWorks = afterRetry;
  }

  console.log(
    JSON.stringify(
      { titleActive, gameActive, finalScreen, stepLog: stepLog.slice(0, 20), errors },
      null,
      2
    )
  );
  await browser.close();
})().catch((e) => {
  console.error("FAIL", e);
  process.exit(1);
});
