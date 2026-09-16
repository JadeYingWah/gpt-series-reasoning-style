// Node harness for A-skill pomodoro core.
// Extracts <script id="core"> from pomodoro.html and asserts acceptance rules.
// Run: node verify-pomodoro.js

const fs = require("fs");
const path = require("path");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");

let failed = 0;
let passed = 0;

function assert(cond, label) {
  if (!cond) {
    failed += 1;
    console.error("FAIL:", label);
    return false;
  }
  passed += 1;
  console.log("PASS:", label);
  return true;
}

// --- extract and load core ---
const match = html.match(/<script id="core">([\s\S]*?)<\/script>/);
if (!assert(!!match, "found <script id=\"core\">")) {
  console.error("RESULT: FAIL");
  process.exit(1);
}

const coreSrc = match[1];
const moduleShim = { exports: {} };
const loader = new Function("module", "exports", coreSrc + "\nreturn module.exports;");
const mod = loader(moduleShim, moduleShim.exports);
if (!assert(mod && typeof mod.createPomodoro === "function", "createPomodoro exported")) {
  console.error("RESULT: FAIL");
  process.exit(1);
}
const { createPomodoro } = mod;

// --- fake clock ---
let fakeNow = 1_700_000_000_000;
const now = () => fakeNow;
const advance = (ms) => { fakeNow += ms; };

// 1) default 25:00
{
  const p = createPomodoro({ totalSeconds: 25 * 60, now });
  assert(p.getState().totalSeconds === 1500, "default totalSeconds = 1500");
  assert(p.format() === "25:00", "default format 25:00");
  assert(p.getState().status === "就绪", "initial status 就绪");
  assert(p.getState().running === false, "initial not running");
  assert(p.getState().done === false, "initial not done");
}

// 2) start / tick / pause / resume
{
  const p = createPomodoro({ totalSeconds: 60, now });
  assert(p.start() === true, "start() returns true when idle");
  assert(p.getState().running === true, "running after start");
  assert(p.getState().status === "进行中", "status 进行中 after start");
  advance(3000);
  p.tick();
  assert(p.getState().remaining === 57, "3s elapsed => remaining 57");
  assert(p.format() === "00:57", "format 00:57 after 3s");
  advance(1500);
  p.pause();
  assert(p.getState().running === false, "pause clears running");
  // 3s already settled by tick; pause settles another 1.5s => 1 more second (57 -> 56)
  assert(p.getState().remaining === 56, "pause settles remaining to 56");
  assert(p.getState().status === "已暂停", "status 已暂停 after pause");
  const held = p.getState().remaining;
  advance(10_000);
  p.tick();
  assert(p.getState().remaining === held, "tick while paused does not decrement");
  assert(p.start() === true, "can start again after pause");
  advance(5000);
  p.tick();
  assert(p.getState().remaining === 51, "resume continues from paused remaining");
}

// 3) reset
{
  const p = createPomodoro({ totalSeconds: 60, now });
  p.start();
  advance(10_000);
  p.tick();
  p.reset();
  assert(p.getState().remaining === 60, "reset restores remaining");
  assert(p.getState().status === "就绪", "reset status 就绪");
  assert(p.getState().done === false, "reset clears done");
  assert(p.getState().running === false, "reset clears running");
}

// 4) completion edge
{
  const p = createPomodoro({ totalSeconds: 60, now });
  let doneEvents = 0;
  p.onChange(function (s) { if (s.done) doneEvents += 1; });
  p.start();
  advance(59_000);
  assert(p.tick() === false, "not complete at 59s");
  assert(p.getState().remaining === 1, "remaining 1 at 59s");
  advance(1000);
  assert(p.tick() === true, "tick returns true on completion edge");
  assert(p.getState().done === true, "done true after full duration");
  assert(p.getState().remaining === 0, "remaining 0");
  assert(p.getState().status === "时间到", "status 文案 = 时间到");
  assert(p.format() === "00:00", "format 00:00 at completion");
  assert(doneEvents === 1, "completion emits once");
  assert(p.start() === false, "cannot start after done");
  advance(5000);
  assert(p.tick() === false, "tick after done is no-op");
}

// 5) setDuration 1–60 integer minutes
{
  const p = createPomodoro({ totalSeconds: 25 * 60, now });
  assert(p.setDuration(1) === true, "setDuration(1) accepted");
  assert(p.getState().totalSeconds === 60 && p.getState().remaining === 60, "1 min => 60s");
  assert(p.format() === "01:00", "format 01:00 for 1 min");
  assert(p.setDuration(60) === true, "setDuration(60) accepted");
  assert(p.getState().totalSeconds === 3600, "60 min => 3600s");
  assert(p.setDuration(25) === true, "setDuration(25) accepted");
  assert(p.getState().totalSeconds === 1500, "25 min => 1500s");
}

// 6) invalid / clamped durations
{
  const p = createPomodoro({ totalSeconds: 1500, now });
  assert(p.setDuration(0) === true, "setDuration(0) clamps to min");
  assert(p.getState().totalSeconds === 60, "0 clamps to 60s");
  assert(p.setDuration(61) === true, "setDuration(61) clamps to max");
  assert(p.getState().totalSeconds === 3600, "61 clamps to 3600s");
  assert(p.setDuration(25.9) === true, "setDuration(25.9) floors");
  assert(p.getState().totalSeconds === 1500, "25.9 floors to 25 min");
  assert(p.setDuration("abc") === false, "setDuration(abc) rejected");
  assert(p.setDuration(null) === false, "setDuration(null) rejected");
  assert(p.setDuration(undefined) === false, "setDuration(undefined) rejected");
  assert(p.setDuration("") === false, "setDuration(empty string) rejected");
}

// 7) setDuration blocked while running / done; allowed while paused
{
  const p = createPomodoro({ totalSeconds: 60, now });
  p.start();
  assert(p.setDuration(30) === false, "setDuration blocked while running");
  p.pause();
  assert(p.setDuration(30) === true, "setDuration allowed while paused");
  assert(p.getState().totalSeconds === 1800, "paused duration applied");
  assert(p.getState().remaining === 1800, "apply resets remaining to new duration");
  p.start();
  advance(1_800_000);
  p.tick();
  assert(p.getState().done === true, "done after advancing full new duration");
  assert(p.setDuration(10) === false, "setDuration blocked after done");
}

// 8) reset accepts new total seconds
{
  const p = createPomodoro({ totalSeconds: 60, now });
  p.reset(15 * 60);
  assert(p.getState().totalSeconds === 900, "reset(900) sets 15 min");
  assert(p.format() === "15:00", "format 15:00 after reset(900)");
}

// 9) no external resources
{
  const extAttr = html.match(/(?:src|href)\s*=\s*["']https?:\/\//gi);
  assert(!extAttr, "no http(s) src/href attributes");
  const anyHttp = html.match(/https?:\/\//gi);
  assert(!anyHttp, "no absolute http(s) URLs in file");
  assert(!/\bcdn\b/i.test(html) || html.includes("无 CDN"), "no CDN dependency claimed/used");
  assert(!/<script[^>]+src=/i.test(html), "no external script src");
  assert(!/<link[^>]+href=/i.test(html), "no external stylesheet link");
}

// 10) required UI ids + completion copy present
{
  for (const id of ["time", "status", "startBtn", "pauseBtn", "resetBtn", "minutes", "applyBtn", "core", "ui"]) {
    assert(html.includes(`id="${id}"`), `UI/core element #${id} present`);
  }
  assert(html.includes("时间到"), "completion copy 时间到 present in source");
  assert(html.includes("就绪"), "idle copy 就绪 present");
  assert(html.includes("进行中"), "running copy 进行中 present");
  assert(html.includes("已暂停"), "paused copy 已暂停 present");
}

// 11) source shape: no framework markers
{
  assert(!/react|vue\.|angular|jquery/i.test(html), "no framework markers in source");
}

console.log("\n--- harness finished ---");
console.log("PASSED:", passed, "FAILED:", failed);
if (failed > 0) {
  console.log("RESULT: FAIL");
  process.exitCode = 1;
} else {
  console.log("RESULT: ALL PASS");
}
