/**
 * WG005 A-skill 番茄钟核心逻辑核对脚本（Node）
 * 从 pomodoro.html 抽取 IIFE 工厂并跑行为断言。
 * 用法: node verify-core.js
 */
const fs = require("fs");
const path = require("path");
const assert = require("assert");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");

// 抽取 core IIFE（从 createTimer 工厂注释起到 UI 绑定前）
const startMarker = "(function (root, factory) {";
const endMarker = "/* ---------- 浏览器 UI 绑定";
const s = html.indexOf(startMarker);
const e = html.indexOf(endMarker);
assert(s !== -1 && e !== -1 && e > s, "无法从 HTML 抽取 core 脚本");
const coreSrc = html.slice(s, e);

// 在干净沙箱里求值，拿到 PomodoroCore
const sandbox = { module: { exports: {} }, exports: {} };
sandbox.module.exports = sandbox.exports;
const fn = new Function("module", "exports", "globalThis", coreSrc + "\n;return module.exports;");
const core = fn(sandbox.module, sandbox.exports, {});

let passed = 0;
function ok(name, cond, extra) {
  assert(cond, name + (extra ? " | " + extra : ""));
  passed++;
  console.log("PASS  " + name);
}

// --- formatClock ---
ok("format 0 -> 00:00", core.formatClock(0) === "00:00");
ok("format 60 -> 01:00", core.formatClock(60) === "01:00");
ok("format 1500 -> 25:00", core.formatClock(1500) === "25:00");
ok("format 59 -> 00:59", core.formatClock(59) === "00:59");
ok("format negative clamps to 0", core.formatClock(-5) === "00:00");

// --- parseMinutes ---
ok("parse 25", core.parseMinutes(25).ok === true && core.parseMinutes(25).seconds === 1500);
ok("parse '25'", core.parseMinutes("25").ok === true);
ok("parse '25.0' integer value ok", core.parseMinutes("25.0").ok === true && core.parseMinutes("25.0").minutes === 25);
ok("parse 1", core.parseMinutes(1).ok === true && core.parseMinutes(1).seconds === 60);
ok("parse 60", core.parseMinutes(60).ok === true && core.parseMinutes(60).seconds === 3600);
ok("parse 0 rejected", core.parseMinutes(0).ok === false);
ok("parse 61 rejected", core.parseMinutes(61).ok === false);
ok("parse -1 rejected", core.parseMinutes(-1).ok === false);
ok("parse 25.5 rejected", core.parseMinutes("25.5").ok === false);
ok("parse empty rejected", core.parseMinutes("").ok === false);
ok("parse abc rejected", core.parseMinutes("abc").ok === false);

// --- 状态机：idle -> running -> paused -> running -> done ---
// Node 下 createTimer 使用真实 setInterval；配合注入假时钟 now() 推进。
async function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function testLifecycle() {
  const events = [];
  let fakeNow = 1_000_000;
  const clock = { now: () => fakeNow };

  // 用注入时钟：1 秒倒计时
  const t1 = core.createTimer({
    initialSeconds: 1,
    now: clock.now,
    onTick: (v) => events.push(["tick", v.status, v.remainingSeconds]),
    onComplete: (v) => events.push(["done", v.status, v.remainingSeconds, v.display])
  });

  ok("initial idle 00:01", t1.getState().status === "idle" && t1.getState().display === "00:01");

  t1.start();
  ok("start -> running", t1.getState().status === "running");

  // 立即 pause：剩余应仍约 1 秒
  t1.pause();
  ok("pause -> paused", t1.getState().status === "paused");
  const pausedRem = t1.getState().remainingSeconds;
  ok("paused remaining >= 1 (still full if instant)", pausedRem === 1);

  t1.start();
  ok("resume -> running", t1.getState().status === "running");

  // 推进假时钟超过 1s，下一次 interval tick 会 settle
  fakeNow += 1100;
  await sleep(350); // 等待 setInterval(250) 触发
  ok("after clock past end -> done", t1.getState().status === "done");
  const doneDisplay = t1.getState().display;
  ok("done display 00:00", doneDisplay === "00:00");
  const doneEvents = events.filter((e) => e[0] === "done");
  ok("onComplete fired once", doneEvents.length === 1 && doneEvents[0][1] === "done");
  ok("onComplete payload 时间到语义: status done + display 00:00", doneEvents[0][1] === "done" && doneEvents[0][3] === "00:00");

  // done 后 start 再来一轮
  t1.start();
  ok("restart after done -> running full", t1.getState().status === "running" && t1.getState().remainingSeconds === 1);
  t1.destroy();

  // reset
  let fakeNow2 = 2_000_000;
  const t2 = core.createTimer({
    initialSeconds: 25 * 60,
    now: () => fakeNow2
  });
  t2.start();
  fakeNow2 += 10_000;
  t2.pause(); // pause 会 tick 对齐
  ok("pause aligns remaining after 10s", t2.getState().remainingSeconds === 25 * 60 - 10);
  t2.reset();
  ok("reset -> idle full 25:00", t2.getState().status === "idle" && t2.getState().display === "25:00");
  t2.destroy();

  // setDurationMinutes
  const t3 = core.createTimer({ initialSeconds: 25 * 60, now: () => 0 });
  const r = t3.setDurationMinutes("15");
  ok("setDuration 15 ok", r.ok === true && r.minutes === 15);
  ok("after setDuration display 15:00 idle", t3.getState().display === "15:00" && t3.getState().status === "idle");
  const rBad = t3.setDurationMinutes("0");
  ok("setDuration 0 rejected keeps previous", rBad.ok === false && t3.getState().display === "15:00");
  const rBig = t3.setDurationMinutes("61");
  ok("setDuration 61 rejected", rBig.ok === false);
  t3.destroy();

  // 开始/暂停/重置互斥性：pause 在 idle 不改变状态
  const t4 = core.createTimer({ initialSeconds: 60, now: () => 0 });
  t4.pause();
  ok("pause on idle stays idle", t4.getState().status === "idle");
  t4.start();
  t4.pause();
  ok("pause on running -> paused", t4.getState().status === "paused");
  const view = t4.getState();
  ok("paused display is mm:ss", /^\d{2}:\d{2}$/.test(view.display));
  t4.reset();
  t4.destroy();
}

testLifecycle()
  .then(() => {
    // 无外链检查
    const html2 = fs.readFileSync(htmlPath, "utf8");
    const bad = [];
    const linkRe = /<link\b[^>]*href\s*=/gi;
    const scriptSrcRe = /<script\b[^>]*src\s*=/gi;
    const urlRe = /https?:\/\//gi;
    if (linkRe.test(html2)) bad.push("has <link href>");
    if (scriptSrcRe.test(html2)) bad.push("has <script src>");
    // 允许注释中出现 http 说明？任务要求无 CDN/外链资源。检查资源型外链。
    const resourceUrls = html2.match(/(?:src|href)\s*=\s*["']https?:\/\/[^"']+/gi) || [];
    ok("no external src/href", resourceUrls.length === 0, resourceUrls.join(","));
    ok("no <script src>", !/<script\b[^>]*\bsrc\s*=/i.test(html2));
    ok("no <link rel stylesheet>", !/<link\b[^>]*rel\s*=\s*["']?stylesheet/i.test(html2));

    console.log("\nALL PASSED:", passed, "assertions");
    process.exit(0);
  })
  .catch((err) => {
    console.error("FAIL:", err.message);
    process.exit(1);
  });
