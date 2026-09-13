/**
 * Node verification for pomodoro.html core logic.
 * Extracts PomodoroCore from the HTML and runs acceptance checks.
 * Usage: node verify-core.js
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");

// --- static checks ---
const checks = [];
function pass(name, ok, detail) {
  checks.push({ name, ok, detail: detail || "" });
}

const hasDoctype = /<!DOCTYPE html>/i.test(html);
pass("file exists & has doctype", hasDoctype);

const cdnPatterns = [
  /https?:\/\/(cdn|unpkg|jsdelivr|cdnjs)\./i,
  /src\s*=\s*["']https?:\/\//i,
  /href\s*=\s*["']https?:\/\/(?!www\.w3\.org)/i,
  /@import\s+url\(["']?https?:\/\//i,
];
const hasCdn = cdnPatterns.some((re) => re.test(html));
pass("no CDN / external script-or-css links", !hasCdn, hasCdn ? "found external URL" : "none");

const hasScript = /<script[\s>]/i.test(html);
pass("inline script present", hasScript);

// --- extract PomodoroCore ---
const startMarker = "const PomodoroCore = (() => {";
const endMarker = "})();";
const si = html.indexOf(startMarker);
if (si < 0) {
  pass("extract PomodoroCore", false, "start marker missing");
  report();
  process.exit(1);
}
// Find matching close: the IIFE ends with "})();" after the return block.
// Safer: take from start marker to the first "\n})();" after it that closes the IIFE.
const sliceFrom = html.slice(si);
const endIdx = sliceFrom.indexOf("\n})();");
if (endIdx < 0) {
  pass("extract PomodoroCore", false, "end marker missing");
  report();
  process.exit(1);
}
const coreSrc = sliceFrom.slice(0, endIdx + "\n})();".length);

const sandbox = { globalThis: {} };
vm.createContext(sandbox);
vm.runInContext(coreSrc + "\nglobalThis.PomodoroCore = PomodoroCore;", sandbox);
const core = sandbox.globalThis.PomodoroCore;
pass("PomodoroCore extracted & evaluated in VM", !!core && typeof core.tick === "function");

// --- behavioral tests ---
function assert(name, cond, detail) {
  pass(name, !!cond, detail || "");
}

assert("formatTime(1500) === 25:00", core.formatTime(1500) === "25:00", core.formatTime(1500));
assert("formatTime(0) === 00:00", core.formatTime(0) === "00:00", core.formatTime(0));
assert("formatTime(59) === 00:59", core.formatTime(59) === "00:59", core.formatTime(59));
assert("formatTime(60) === 01:00", core.formatTime(60) === "01:00", core.formatTime(60));

assert("clampMinutes(25) === 25", core.clampMinutes(25) === 25);
assert("clampMinutes(1) === 1", core.clampMinutes(1) === 1);
assert("clampMinutes(60) === 60", core.clampMinutes(60) === 60);
assert("clampMinutes(0) === null", core.clampMinutes(0) === null);
assert("clampMinutes(61) === null", core.clampMinutes(61) === null);
assert("clampMinutes('abc') === null", core.clampMinutes("abc") === null);
assert("clampMinutes(25.9) floors to 25", core.clampMinutes(25.9) === 25, String(core.clampMinutes(25.9)));

// start / pause / reset cycle
let s = core.reset(25);
assert("reset(25) remaining === 1500", s.remaining === 1500, String(s.remaining));
assert("reset not running", s.running === false);
assert("reset not finished", s.finished === false);

s = core.start(s);
assert("start sets running", s.running === true);
const s2 = core.start(s);
assert("start when already running is no-op (still running)", s2.running === true);

s = core.pause(s);
assert("pause clears running", s.running === false);
assert("pause keeps remaining", s.remaining === 1500, String(s.remaining));

// tick countdown
s = core.reset(1); // 60 seconds
s = core.start(s);
for (let i = 0; i < 59; i++) s = core.tick(s);
assert("after 59 ticks remaining === 1", s.remaining === 1, String(s.remaining));
assert("not finished yet", s.finished === false);
s = core.tick(s);
assert("after 60th tick remaining === 0", s.remaining === 0, String(s.remaining));
assert("finished flag true", s.finished === true);
assert("running false when finished", s.running === false);
const s3 = core.tick(s);
assert("tick after finished is no-op", s3.remaining === 0 && s3.finished === true);

// pause mid-way then resume
s = core.reset(2);
s = core.start(s);
s = core.tick(s);
s = core.tick(s);
s = core.pause(s);
const rem = s.remaining;
assert("pause mid-way remaining === 118", rem === 118, String(rem));
s = core.start(s);
s = core.tick(s);
assert("resume continues countdown", s.remaining === rem - 1, String(s.remaining));

// reset after finish restores full duration
s = core.reset(25);
s = core.start(s);
s = { remaining: 0, running: false, finished: true };
s = core.reset(25);
assert("reset after finish restores 1500", s.remaining === 1500 && !s.finished && !s.running);

// default minutes
assert("DEFAULT_MINUTES === 25", core.DEFAULT_MINUTES === 25);
assert("MIN === 1 MAX === 60", core.MIN_MINUTES === 1 && core.MAX_MINUTES === 60);

// HTML contains status string 时间到
pass("status string 时间到 present in source", html.includes("时间到"));
pass("start/pause/reset buttons present", /id="btnStart"/.test(html) && /id="btnPause"/.test(html) && /id="btnReset"/.test(html));
pass("minutes input present", /id="minutes"/.test(html));

function report() {
  const failed = checks.filter((c) => !c.ok);
  for (const c of checks) {
    const mark = c.ok ? "PASS" : "FAIL";
    console.log(`${mark}  ${c.name}${c.detail ? "  [" + c.detail + "]" : ""}`);
  }
  console.log("---");
  console.log(`${checks.length - failed.length}/${checks.length} passed`);
  if (failed.length) process.exitCode = 1;
}

report();
