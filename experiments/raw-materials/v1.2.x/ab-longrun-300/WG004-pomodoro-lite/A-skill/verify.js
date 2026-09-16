"use strict";
/**
 * Node verification for pomodoro.html pure logic.
 * Extracts <script> and runs assertions against createTimer / formatTime / parseMinutes.
 * Run: node verify.js
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");

const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) {
  console.error("FAIL: no <script> block found in pomodoro.html");
  process.exit(1);
}
const code = m[1];

const sandbox = {
  module: { exports: {} },
  exports: {},
  console,
  setInterval,
  clearInterval,
  setTimeout,
  clearTimeout
};
sandbox.exports = sandbox.module.exports;
vm.createContext(sandbox);
vm.runInContext(code, sandbox);

const { createTimer, formatTime, parseMinutes } = sandbox.module.exports;

let passed = 0;
let failed = 0;

function assert(cond, label) {
  if (cond) {
    passed += 1;
    console.log("PASS  " + label);
  } else {
    failed += 1;
    console.log("FAIL  " + label);
  }
}

function assertThrows(fn, label) {
  try {
    fn();
    failed += 1;
    console.log("FAIL  " + label + " (no throw)");
  } catch (e) {
    passed += 1;
    console.log("PASS  " + label);
  }
}

/* ---- formatTime ---- */
assert(formatTime(0) === "00:00", "formatTime(0) = 00:00");
assert(formatTime(59) === "00:59", "formatTime(59) = 00:59");
assert(formatTime(60) === "01:00", "formatTime(60) = 01:00");
assert(formatTime(25 * 60) === "25:00", "formatTime(1500) = 25:00");
assert(formatTime(60 * 60) === "60:00", "formatTime(3600) = 60:00");
assertThrows(() => formatTime(-1), "formatTime(-1) throws");
assertThrows(() => formatTime(1.5), "formatTime(1.5) throws");

/* ---- parseMinutes ---- */
assert(parseMinutes("25").ok && parseMinutes("25").minutes === 25, 'parseMinutes("25") → 25');
assert(parseMinutes("1").ok && parseMinutes("1").minutes === 1, 'parseMinutes("1") → 1');
assert(parseMinutes("60").ok && parseMinutes("60").minutes === 60, 'parseMinutes("60") → 60');
assert(!parseMinutes("0").ok, 'parseMinutes("0") rejected');
assert(!parseMinutes("61").ok, 'parseMinutes("61") rejected');
assert(!parseMinutes("-5").ok, 'parseMinutes("-5") rejected');
assert(!parseMinutes("2.5").ok, 'parseMinutes("2.5") rejected');
assert(!parseMinutes("abc").ok, 'parseMinutes("abc") rejected');
assert(!parseMinutes("").ok, 'parseMinutes("") rejected');
assert(!parseMinutes("  ").ok, 'parseMinutes("  ") rejected');
assert(parseMinutes(" 10 ").ok && parseMinutes(" 10 ").minutes === 10, 'parseMinutes(" 10 ") trims');

/* ---- createTimer validation ---- */
assertThrows(() => createTimer(0), "createTimer(0) throws");
assertThrows(() => createTimer(-1), "createTimer(-1) throws");
assertThrows(() => createTimer(1.5), "createTimer(1.5) throws");

/* ---- createTimer state machine (sync parts) ---- */
const ticks = [];
const t = createTimer(3, {
  onTick: (r, running) => ticks.push({ r, running }),
  onComplete: () => ticks.push({ complete: true })
});

assert(t.remaining === 3 && t.running === false, "initial remaining=3, not running");
assert(t.start() === true, "start returns true");
assert(t.running === true, "running after start");
assert(t.start() === false, "second start returns false (already running)");
assert(t.pause() === true, "pause returns true");
assert(t.running === false, "not running after pause");
assert(t.pause() === false, "second pause returns false");
assert(t.remaining === 3, "remaining unchanged while paused (before first tick)");
assert(t.start() === true, "resume after pause returns true");
assert(t.reset() === true, "reset returns true");
assert(t.running === false && t.remaining === 3, "reset restores full duration");

assert(t.reset(10) === true, "reset(10) returns true");
assert(t.remaining === 10, "remaining=10 after reset(10)");
assertThrows(() => t.reset(0), "reset(0) throws");
assertThrows(() => t.reset(2.2), "reset(2.2) throws");

/* ---- createTimer async tick to zero ---- */
const doneTicks = [];
let completed = false;
const t2 = createTimer(1, {
  onTick: (r, running) => doneTicks.push(r),
  onComplete: () => { completed = true; }
});

t2.start();

setTimeout(() => {
  assert(completed === true, "onComplete fires after last second");
  assert(t2.remaining === 0, "remaining=0 after completion");
  assert(t2.running === false, "not running after completion");
  assert(doneTicks.indexOf(0) !== -1 || completed, "tick saw remaining 0 (or onComplete)");
  assert(t2.start() === false, "start after completion returns false");

  console.log("");
  console.log("----");
  console.log("passed=" + passed + " failed=" + failed);
  if (failed > 0) process.exit(1);
}, 1300);
