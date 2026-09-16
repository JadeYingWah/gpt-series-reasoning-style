/**
 * WG005 A-skill 浏览器交互核对（Playwright + Chromium）
 * 用法: node verify-ui.js
 */
const path = require("path");
const { chromium } = require("playwright");

const FILE_URL = "file:///" + path.join(__dirname, "pomodoro.html").replace(/\\/g, "/");

function assert(cond, msg) {
  if (!cond) throw new Error("ASSERT: " + msg);
  console.log("PASS  " + msg);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push("console: " + msg.text());
  });

  await page.goto(FILE_URL);
  await page.waitForSelector("#display");

  // 初始状态
  assert((await page.textContent("#display")) === "25:00", "initial display 25:00");
  assert((await page.textContent("#status")) === "就绪", "initial status 就绪");
  assert(await page.isDisabled("#pauseBtn"), "pause disabled when idle");
  assert(!(await page.isDisabled("#startBtn")), "start enabled when idle");

  // 配置时长 1 分钟 → 再改成测试用短时长？先测配置
  await page.fill("#minutesInput", "15");
  await page.click("#applyBtn");
  assert((await page.textContent("#display")) === "15:00", "apply 15min -> 15:00");
  assert((await page.textContent("#status")) === "就绪", "apply resets status 就绪");

  // 非法输入
  await page.fill("#minutesInput", "0");
  await page.click("#applyBtn");
  const err0 = await page.textContent("#errorMsg");
  assert(err0.includes("1–60") || err0.includes("1-60"), "reject 0 with range error: " + err0);
  assert((await page.textContent("#display")) === "15:00", "invalid input keeps 15:00");

  await page.fill("#minutesInput", "25.5");
  await page.click("#applyBtn");
  const errF = await page.textContent("#errorMsg");
  assert(errF.includes("正整数"), "reject 25.5 as non-integer: " + errF);

  await page.fill("#minutesInput", "61");
  await page.click("#applyBtn");
  assert((await page.textContent("#display")) === "15:00", "reject 61 keeps previous");

  // 恢复 1 分钟用于较快完整周期
  await page.fill("#minutesInput", "1");
  await page.click("#applyBtn");
  assert((await page.textContent("#display")) === "01:00", "apply 1min -> 01:00");

  // 开始
  await page.click("#startBtn");
  assert((await page.textContent("#status")) === "进行中", "start -> 进行中");
  assert(await page.isDisabled("#startBtn"), "start disabled while running");
  assert(!(await page.isDisabled("#pauseBtn")), "pause enabled while running");

  // 等待倒计时至少减少 1 秒
  await page.waitForFunction(() => {
    const t = document.getElementById("display").textContent;
    return t !== "01:00";
  }, { timeout: 5000 });
  const mid = await page.textContent("#display");
  assert(/^\d{2}:\d{2}$/.test(mid) && mid !== "01:00", "countdown ticking: " + mid);

  // 暂停
  await page.click("#pauseBtn");
  assert((await page.textContent("#status")) === "已暂停", "pause -> 已暂停");
  const pausedDisplay = await page.textContent("#display");
  // 再等 800ms，显示应不变
  await page.waitForTimeout(800);
  assert((await page.textContent("#display")) === pausedDisplay, "paused display frozen at " + pausedDisplay);

  // 继续
  await page.click("#startBtn");
  assert((await page.textContent("#status")) === "进行中", "resume -> 进行中");

  // 重置
  await page.click("#resetBtn");
  assert((await page.textContent("#display")) === "01:00", "reset -> 01:00");
  assert((await page.textContent("#status")) === "就绪", "reset -> 就绪");

  // 完整 1 分钟倒计时到时间到（用假时钟加速：直接改页面内部不可行；
  // 改为把时长设为 1 分钟后 start，再用 page clock 或等待。
  // Playwright 1.63 支持 clock API；若不可用则缩短测试：注入 Date。
  // 这里用 page.clock.install 加速。
  await page.clock.install({ time: new Date("2026-01-01T00:00:00Z") });
  await page.click("#startBtn");
  assert((await page.textContent("#status")) === "进行中", "clock: start running");
  // 快进 61 秒，覆盖 setInterval tick
  await page.clock.runFor(61000);
  await page.waitForTimeout(100);
  assert((await page.textContent("#status")) === "时间到", "after 61s status 时间到");
  assert((await page.textContent("#display")) === "00:00", "after 61s display 00:00");
  const statusClass = await page.getAttribute("#status", "class");
  assert((statusClass || "").includes("is-done"), "status has is-done class");

  // 完成后再点开始 = 再来一轮
  const btnText = await page.textContent("#startBtn");
  assert(btnText.includes("再来一轮"), "start button text 再来一轮 after done");
  await page.click("#startBtn");
  assert((await page.textContent("#status")) === "进行中", "restart after done");
  assert((await page.textContent("#display")) !== "00:00", "restart display non-zero");
  await page.click("#resetBtn");

  // 检查无外链网络请求
  const external = [];
  page.on("request", (req) => {
    const u = req.url();
    if (/^https?:/i.test(u)) external.push(u);
  });
  await page.reload();
  await page.waitForTimeout(300);
  assert(external.length === 0, "no http(s) network requests on load, got: " + external.join(","));

  assert(errors.length === 0, "no page errors: " + errors.join(" | "));

  // 截图留证
  const shotPath = path.join(__dirname, "ui-verify.png");
  await page.fill("#minutesInput", "25");
  await page.click("#applyBtn");
  await page.screenshot({ path: shotPath, fullPage: true });
  console.log("SCREENSHOT", shotPath);

  await browser.close();
  console.log("\nUI VERIFY ALL PASSED");
})().catch((err) => {
  console.error("UI FAIL:", err.message);
  process.exit(1);
});
