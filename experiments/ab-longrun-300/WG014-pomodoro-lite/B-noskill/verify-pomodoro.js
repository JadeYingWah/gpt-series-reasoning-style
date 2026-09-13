// Node harness for pomodoro core — no DOM required.
// Extracts <script id="core"> from pomodoro.html and asserts acceptance behaviors.

const fs = require("fs");
const path = require("path");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");

// --- extract core script ---
const m = html.match(/<script id="core">([\s\S]*?)<\/script>/);
if (!m) {
  console.error("FAIL: could not find <script id=\"core\"> in pomodoro.html");
  process.exit(1);
}
const coreSrc = m[1];

// Evaluate core into a sandbox-like module scope
const module_ = { exports: {} };
const fn = new Function("module", "exports", coreSrc + "\nreturn module.exports;");
const mod = fn(module_, module_.exports);
if (!mod || typeof mod.createPomodoro !== "function") {
  console.error("FAIL: createPomodoro not exported");
  process.exit(1);
}
const { createPomodoro } = mod;

// --- controllable clock ---
let fakeNow = 1_000_000;
const now = () => fakeNow;

function advance(ms) {
  fakeNow += ms;
}

function assert(cond, label) {
  if (!cond) {
    console.error("FAIL:", label);
    process.exitCode = 1;
    return false;
  }
  console.log("PASS:", label);
  return true;
}

// 1) default total is 25:00
{
  const p = createPomodoro({ totalSeconds: 25 * 60, now });
  assert(p.getState().totalSeconds === 1500, "default totalSeconds = 1500 (25:00)");
  assert(p.format() === "25:00", "format() === 25:00");
  assert(p.getState().status === "就绪", "initial status 就绪");
  assert(p.getState().running === false, "initial not running");
}

// 2) start -> running; tick reduces remaining
{
  const p = createPomodoro({ totalSeconds: 60, now });
  p.start();
  assert(p.getState().running === true && p.getState().status === "进行中", "start() sets running/进行中");
  advance(3000);
  p.tick();
  assert(p.getState().remaining === 57, "after 3s remaining=57");
  assert(p.format() === "00:57", "format 00:57 after 3s");
}

// 3) pause settles remaining and stops
{
  const p = createPomodoro({ totalSeconds: 60, now });
  p.start();
  advance(5000);
  p.pause();
  assert(p.getState().running === false, "pause() clears running");
  assert(p.getState().remaining === 55, "pause settles remaining to 55");
  assert(p.getState().status === "已暂停", "status 已暂停");
  const before = p.getState().remaining;
  advance(10_000);
  p.tick();
  assert(p.getState().remaining === before, "tick while paused does not change remaining");
}

// 4) reset restores full duration
{
  const p = createPomodoro({ totalSeconds: 60, now });
  p.start();
  advance(10_000);
  p.tick();
  p.reset();
  assert(p.getState().remaining === 60, "reset restores remaining");
  assert(p.getState().status === "就绪", "reset status 就绪");
  assert(p.getState().done === false, "reset clears done");
}

// 5) completion edge: remaining 0, done, status 时间到
{
  const p = createPomodoro({ totalSeconds: 60, now });
  let events = 0;
  p.onChange((s) => {
    if (s.done) events += 1;
  });
  p.start();
  advance(60_000);
  const completed = p.tick();
  assert(completed === true, "tick returns true on completion edge");
  assert(p.getState().done === true, "done === true after full duration");
  assert(p.getState().remaining === 0, "remaining === 0");
  assert(p.getState().status === "时间到", "status 文案 = 时间到");
  assert(events === 1, "completion emits once");
  // further start/tick should no-op
  assert(p.start() === false, "cannot start after done");
  advance(5000);
  assert(p.tick() === false, "tick after done is no-op");
}

// 6) duration config 1–60 minutes
{
  const p = createPomodoro({ totalSeconds: 60, now });
  assert(p.setDuration(1) === true, "setDuration(1) ok");
  assert(p.getState().totalSeconds === 60, "1 minute => 60s");
  assert(p.setDuration(60) === true, "setDuration(60) ok");
  assert(p.getState().totalSeconds === 3600, "60 minutes => 3600s");
  assert(p.setDuration(0) === true, "setDuration(0) clamps to min");
  assert(p.getState().totalSeconds === 60, "0 clamps to 60s");
  assert(p.setDuration(61) === true, "setDuration(61) clamps to max");
  assert(p.getState().totalSeconds === 3600, "61 clamps to 3600s");
  assert(p.setDuration(25.9) === true, "setDuration(25.9) floors");
  assert(p.getState().totalSeconds === 25 * 60, "25.9 floors to 25 min");
}

// 7) setDuration rejected while running
{
  const p = createPomodoro({ totalSeconds: 60, now });
  p.start();
  assert(p.setDuration(30) === false, "setDuration blocked while running");
  p.pause();
  assert(p.setDuration(30) === true, "setDuration allowed after pause");
  assert(p.getState().totalSeconds === 1800, "duration applied after pause");
}

// 8) reset(newTotal) accepts minutes-as-seconds total
{
  const p = createPomodoro({ totalSeconds: 60, now });
  p.reset(15 * 60);
  assert(p.getState().totalSeconds === 900, "reset(900) sets 15 min");
  assert(p.format() === "15:00", "format 15:00");
}

// 9) no external URLs in html
{
  const htmlBody = html;
  const ext = htmlBody.match(/(?:src|href)\s*=\s*["']https?:\/\//gi);
  assert(!ext, "no http(s) src/href attributes (no CDN/外链)");
  const urlish = htmlBody.match(/https?:\/\//gi);
  // allow none — comments shouldn't need URLs either
  assert(!urlish, "no absolute http(s) URLs anywhere in file");
}

// 10) required UI element ids present
{
  for (const id of ["time", "status", "startBtn", "pauseBtn", "resetBtn", "minutes", "applyBtn"]) {
    assert(html.includes(`id="${id}"`), `UI element #${id} present`);
  }
  assert(html.includes("时间到"), "completion 文案 时间到 present in source");
}

console.log("\n--- harness finished ---");
if (process.exitCode) {
  console.log("RESULT: FAIL");
} else {
  console.log("RESULT: ALL PASS");
}
