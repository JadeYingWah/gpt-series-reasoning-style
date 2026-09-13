"use strict";
/**
 * A 臂 Node 核对脚本：从 pomodoro.html 抽出内联逻辑做断言。
 * 用法：node verify.js
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");
const fails = [];

function assert(cond, msg) {
  if (!cond) fails.push("ASSERT FAIL: " + msg);
}

/* 1) 无外链 */
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
for (const re of externalPatterns) {
  if (re.test(html)) fails.push("external resource pattern hit: " + re.source);
}

/* 2) 抽出 script 块 */
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/i);
if (!scriptMatch) fails.push("no inline <script> found");
const script = scriptMatch ? scriptMatch[1] : "";

/* 3) vm 沙箱求值纯逻辑 */
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
vm.runInContext(script, sandbox, { filename: "pomodoro-a-extract.js" });

const api = moduleObj.exports;
if (!api || typeof api.createTimer !== "function") {
  fails.push("module.exports.createTimer missing after vm eval");
}

if (api && api.createTimer) {
  const { createTimer, formatTime, normalizeMinutes } = api;

  assert(typeof formatTime === "function", "formatTime is function");
  assert(typeof normalizeMinutes === "function", "normalizeMinutes is function");

  /* formatTime */
  assert(formatTime(1500) === "25:00", "formatTime(1500)");
  assert(formatTime(0) === "00:00", "formatTime(0)");
  assert(formatTime(65) === "01:05", "formatTime(65)");
  assert(formatTime(599) === "09:59", "formatTime(599)");
  assert(formatTime(-5) === "00:00", "formatTime clamps negative");

  /* normalizeMinutes */
  assert(normalizeMinutes("25", 25) === 25, "norm 25");
  assert(normalizeMinutes("1", 25) === 1, "norm 1");
  assert(normalizeMinutes("60", 25) === 60, "norm 60");
  assert(normalizeMinutes(0, 25) === 25, "norm 0 fallback");
  assert(normalizeMinutes(61, 25) === 25, "norm 61 fallback");
  assert(normalizeMinutes("abc", 25) === 25, "norm abc fallback");
  assert(normalizeMinutes(2.5, 25) === 25, "norm 2.5 fallback");
  assert(normalizeMinutes(-3, 10) === 10, "norm -3 fallback");
  assert(normalizeMinutes("  15  ", 25) === 15, "norm trims whitespace");

  /* 初始态 */
  let t = createTimer(25);
  let s = t.getState();
  assert(s.status === "idle", "initial idle");
  assert(s.remainingSeconds === 1500, "initial 1500s");
  assert(s.durationMinutes === 25, "duration 25");

  /* start / pause / tick / resume / reset */
  s = t.start();
  assert(s.status === "running", "start → running");

  s = t.pause();
  assert(s.status === "paused", "pause → paused");
  const remAfterPause = s.remainingSeconds;

  s = t.tick();
  assert(s.remainingSeconds === remAfterPause, "paused tick no decrease");
  assert(s.status === "paused", "paused tick keeps paused");

  s = t.start();
  assert(s.status === "running", "resume → running");

  s = t.tick();
  assert(s.remainingSeconds === remAfterPause - 1, "running tick -1");

  s = t.reset();
  assert(s.status === "idle", "reset → idle");
  assert(s.remainingSeconds === 1500, "reset remaining 1500");

  /* setDuration */
  s = t.setDuration(5);
  assert(s.status === "idle", "setDuration idle");
  assert(s.remainingSeconds === 300, "5min=300s");
  assert(s.durationMinutes === 5, "durationMinutes 5");
  assert(formatTime(s.remainingSeconds) === "05:00", "display 05:00");

  t.start();
  t.setDuration(10);
  s = t.getState();
  assert(s.durationMinutes === 5, "setDuration ignored while running");
  assert(s.remainingSeconds === 300, "remaining unchanged while running");

  /* 倒计时到 done */
  t = createTimer(1);
  t.start();
  for (let i = 0; i < 59; i++) t.tick();
  s = t.getState();
  assert(s.status === "running", "still running at 1s");
  assert(s.remainingSeconds === 1, "1s left");
  s = t.tick();
  assert(s.status === "done", "done at 0");
  assert(s.remainingSeconds === 0, "remaining 0");
  assert(formatTime(s.remainingSeconds) === "00:00", "display 00:00");

  s = t.tick();
  assert(s.remainingSeconds === 0, "tick after done stays 0");
  assert(s.status === "done", "still done");

  s = t.start();
  assert(s.status === "running", "start after done → running");
  assert(s.remainingSeconds === 60, "restart full 60s");

  s = t.reset(30);
  assert(s.status === "idle", "reset(30) idle");
  assert(s.remainingSeconds === 1800, "reset(30)=1800s");

  assert(createTimer(1).getState().remainingSeconds === 60, "createTimer(1)");
  assert(createTimer(60).getState().remainingSeconds === 3600, "createTimer(60)");
  assert(createTimer(0).getState().remainingSeconds === 1500, "createTimer(0) fallback");
}

/* 4) UI 锚点与文案 */
assert(html.includes("时间到"), "contains 时间到");
assert(html.includes("开始") && html.includes("暂停") && html.includes("重置"), "button labels");
assert(html.includes('id="display"'), "display id");
assert(html.includes('id="status"'), "status id");
assert(html.includes('id="minutes"'), "minutes id");
assert(html.includes('type="number"'), "number input");
assert(html.includes('min="1"') && html.includes('max="60"'), "min=1 max=60");
assert(html.includes("STATUS_TEXT"), "STATUS_TEXT map present");
assert(/STATUS_TEXT\s*=\s*\{[\s\S]*?done:\s*"时间到"/.test(html), "STATUS_TEXT.done = 时间到");

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
  console.log(" - STATUS_TEXT.done is 时间到");
}
