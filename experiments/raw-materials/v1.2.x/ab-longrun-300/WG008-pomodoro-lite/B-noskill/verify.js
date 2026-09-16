"use strict";
/**
 * Node-side verification of pomodoro.html pure logic.
 * Extracts the script block and tests createTimer / formatTime / normalizeMinutes.
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");

// 1) No external resources
const externalPatterns = [
  /https?:\/\//i,
  /cdn\./i,
  /unpkg\.com/i,
  /jsdelivr/i,
  /googleapis/i,
  /bootstrapcdn/i,
  /<link[^>]+href\s*=/i,
  /<script[^>]+src\s*=/i
];
const fails = [];
const externalHits = externalPatterns
  .map((re) => ({ re: re.source, hit: re.test(html) }))
  .filter((x) => x.hit);
if (externalHits.length) {
  fails.push("external resources found: " + JSON.stringify(externalHits));
}

// 2) Extract last <script> block (inline logic)
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/i);
if (!scriptMatch) fails.push("no inline <script> found");
const script = scriptMatch ? scriptMatch[1] : "";

// 3) Evaluate pure logic in a sandbox with module.exports
const moduleObj = { exports: {} };
const sandbox = {
  module: moduleObj,
  exports: moduleObj.exports,
  console,
  Math,
  parseInt,
  isFinite,
  String,
  Number,
  Object,
  Array,
  Boolean
};
sandbox.global = sandbox;
vm.createContext(sandbox);
// Guard: strip browser-only DOM block if present — our code checks typeof document
// document is undefined in sandbox, so DOM IIFE is skipped.
vm.runInContext(script, sandbox, { filename: "pomodoro-extract.js" });

const api = moduleObj.exports;
if (!api || typeof api.createTimer !== "function") {
  fails.push("module.exports.createTimer not available after eval");
}

function assert(cond, msg) {
  if (!cond) fails.push("ASSERT FAIL: " + msg);
}

if (api && api.createTimer) {
  const { createTimer, formatTime, normalizeMinutes } = api;

  // formatTime
  assert(formatTime(1500) === "25:00", "formatTime(1500)==25:00 got " + formatTime(1500));
  assert(formatTime(0) === "00:00", "formatTime(0)==00:00 got " + formatTime(0));
  assert(formatTime(65) === "01:05", "formatTime(65)==01:05 got " + formatTime(65));
  assert(formatTime(599) === "09:59", "formatTime(599)==09:59 got " + formatTime(599));

  // normalizeMinutes
  assert(normalizeMinutes("25", 25) === 25, "normalize 25");
  assert(normalizeMinutes("1", 25) === 1, "normalize 1");
  assert(normalizeMinutes("60", 25) === 60, "normalize 60");
  assert(normalizeMinutes(0, 25) === 25, "normalize 0 → fallback");
  assert(normalizeMinutes(61, 25) === 25, "normalize 61 → fallback");
  assert(normalizeMinutes("abc", 25) === 25, "normalize abc → fallback");
  assert(normalizeMinutes(2.5, 25) === 25, "normalize 2.5 → fallback");
  assert(normalizeMinutes(-3, 10) === 10, "normalize -3 → fallback");

  // timer default 25 min
  let t = createTimer(25);
  let s = t.getState();
  assert(s.status === "idle", "initial status idle");
  assert(s.remainingSeconds === 1500, "initial remaining 1500, got " + s.remainingSeconds);
  assert(s.durationMinutes === 25, "duration 25");

  // start → running
  s = t.start();
  assert(s.status === "running", "start → running");

  // pause → paused
  s = t.pause();
  assert(s.status === "paused", "pause → paused");
  const remAfterPause = s.remainingSeconds;

  // tick while paused does not decrease
  s = t.tick();
  assert(s.remainingSeconds === remAfterPause, "tick while paused does not decrease");
  assert(s.status === "paused", "tick keeps paused");

  // resume
  s = t.start();
  assert(s.status === "running", "resume → running");

  // tick decreases
  s = t.tick();
  assert(s.remainingSeconds === remAfterPause - 1, "tick decreases by 1");
  assert(s.status === "running", "still running after tick");

  // reset
  s = t.reset();
  assert(s.status === "idle", "reset → idle");
  assert(s.remainingSeconds === 1500, "reset remaining 1500");

  // setDuration while idle
  s = t.setDuration(5);
  assert(s.status === "idle", "setDuration idle stays idle");
  assert(s.remainingSeconds === 300, "5 min = 300s");
  assert(s.durationMinutes === 5, "durationMinutes 5");
  assert(formatTime(s.remainingSeconds) === "05:00", "display 05:00");

  // setDuration ignored while running
  t.start();
  t.setDuration(10);
  s = t.getState();
  assert(s.durationMinutes === 5, "setDuration ignored while running");
  assert(s.remainingSeconds === 300, "remaining unchanged while running");

  // countdown to done
  t = createTimer(1); // 60 seconds
  t.start();
  for (let i = 0; i < 59; i++) t.tick();
  s = t.getState();
  assert(s.status === "running", "still running at 1s left");
  assert(s.remainingSeconds === 1, "1s left");
  s = t.tick();
  assert(s.status === "done", "done at 0");
  assert(s.remainingSeconds === 0, "remaining 0 when done");
  assert(formatTime(s.remainingSeconds) === "00:00", "display 00:00");

  // tick after done does not go negative
  s = t.tick();
  assert(s.remainingSeconds === 0, "tick after done stays 0");
  assert(s.status === "done", "still done");

  // start after done restarts full duration
  s = t.start();
  assert(s.status === "running", "start after done → running");
  assert(s.remainingSeconds === 60, "restarted full 60s");

  // reset with explicit minutes
  s = t.reset(30);
  assert(s.status === "idle", "reset(30) idle");
  assert(s.remainingSeconds === 1800, "reset(30) = 1800s");

  // boundary: 1 and 60
  assert(createTimer(1).getState().remainingSeconds === 60, "createTimer(1)");
  assert(createTimer(60).getState().remainingSeconds === 3600, "createTimer(60)");
  // invalid create falls back to 25
  assert(createTimer(0).getState().remainingSeconds === 1500, "createTimer(0) fallback 25");
}

// 4) Required strings present in HTML
assert(html.includes("时间到"), "HTML contains 时间到");
assert(html.includes("开始"), "HTML contains 开始");
assert(html.includes("暂停"), "HTML contains 暂停");
assert(html.includes("重置"), "HTML contains 重置");
assert(html.includes('id="display"'), "display element");
assert(html.includes('id="status"'), "status element");
assert(html.includes('id="minutes"'), "minutes input");
assert(html.includes('type="number"'), "number input");
assert(html.includes('min="1"') && html.includes('max="60"'), "min=1 max=60");

// Report
if (fails.length) {
  console.error("FAILURES:\n" + fails.map((f) => " - " + f).join("\n"));
  process.exit(1);
} else {
  console.log("ALL CHECKS PASSED");
  console.log(" - no external http(s)/cdn/script src/link href");
  console.log(" - formatTime / normalizeMinutes / createTimer extracted via vm");
  console.log(" - start/pause/reset/setDuration/tick/done verified");
  console.log(" - duration 1–60 bounds + fallback verified");
  console.log(" - countdown 60s → done + restart after done verified");
}
