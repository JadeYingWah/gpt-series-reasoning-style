"use strict";
// Node verification: extracts pure core from pomodoro.html and tests it live.
// No hand-copied logic — if HTML pure-core changes, these assertions run against it.
var fs = require("fs");
var path = require("path");
var vm = require("vm");

var htmlPath = path.join(__dirname, "pomodoro.html");
var html = fs.readFileSync(htmlPath, "utf8");

var start = html.indexOf("var MIN_MINUTES");
var end = html.indexOf("/* ========== browser shell");
if (start < 0 || end < 0 || end <= start) {
  console.log("FAIL cannot locate pure core markers in pomodoro.html");
  process.exit(1);
}
var pureCore = html.slice(start, end);

var sandbox = { console: console, Math: Math, String: String, parseInt: parseInt, isFinite: isFinite };
vm.createContext(sandbox);
vm.runInContext(
  pureCore +
    "\n;this.exports = {\n" +
    "  MIN_MINUTES: MIN_MINUTES,\n" +
    "  MAX_MINUTES: MAX_MINUTES,\n" +
    "  DEFAULT_MINUTES: DEFAULT_MINUTES,\n" +
    "  STATES: STATES,\n" +
    "  clampMinutes: clampMinutes,\n" +
    "  parseMinutes: parseMinutes,\n" +
    "  formatMs: formatMs,\n" +
    "  minutesToMs: minutesToMs,\n" +
    "  remainingFrom: remainingFrom,\n" +
    "  transition: transition\n" +
    "};",
  sandbox
);

var api = sandbox.exports;
var MIN_MINUTES = api.MIN_MINUTES;
var MAX_MINUTES = api.MAX_MINUTES;
var STATES = api.STATES;
var parseMinutes = api.parseMinutes;
var formatMs = api.formatMs;
var minutesToMs = api.minutesToMs;
var remainingFrom = api.remainingFrom;
var transition = api.transition;

var fail = 0;
function expect(label, got, want) {
  var ok = JSON.stringify(got) === JSON.stringify(want);
  if (!ok) {
    fail++;
    console.log("FAIL", label, "got", JSON.stringify(got), "want", JSON.stringify(want));
  } else {
    console.log("OK  ", label, "->", JSON.stringify(got));
  }
}

expect("MIN_MINUTES", MIN_MINUTES, 1);
expect("MAX_MINUTES", MAX_MINUTES, 60);
expect("DEFAULT_MINUTES", api.DEFAULT_MINUTES, 25);

// parseMinutes — accept
expect('parse "25"', parseMinutes("25"), 25);
expect('parse "1"', parseMinutes("1"), 1);
expect('parse "60"', parseMinutes("60"), 60);
expect('parse "  10  "', parseMinutes("  10  "), 10);
expect('parse "007"', parseMinutes("007"), 7);
// parseMinutes — reject
expect('parse "0"', parseMinutes("0"), null);
expect('parse "61"', parseMinutes("61"), null);
expect('parse "25.5"', parseMinutes("25.5"), null);
expect('parse "-5"', parseMinutes("-5"), null);
expect('parse "abc"', parseMinutes("abc"), null);
expect('parse ""', parseMinutes(""), null);
expect("parse null", parseMinutes(null), null);

// formatMs
expect("format 0", formatMs(0), "00:00");
expect("format -1", formatMs(-1), "00:00");
expect("format 1", formatMs(1), "00:01");
expect("format 999", formatMs(999), "00:01");
expect("format 60000", formatMs(60000), "01:00");
expect("format 25min", formatMs(25 * 60 * 1000), "25:00");
expect("format 59m58.5s remaining", formatMs(59 * 60 * 1000 + 58 * 1000 + 500), "59:59");
expect("format just under 60min", formatMs(60 * 60 * 1000 - 1), "60:00");

// remainingFrom
expect("remaining future", remainingFrom(10000, 8500), 1500);
expect("remaining past clamps 0", remainingFrom(10000, 12000), 0);
expect("remaining equal 0", remainingFrom(10000, 10000), 0);

// minutesToMs
expect("25min ms", minutesToMs(25), 1500000);

// state machine
expect("ready+start", transition(STATES.READY, "start", { remainingMs: 1500000 }).state, STATES.RUNNING);
expect("ready+start status", transition(STATES.READY, "start", { remainingMs: 1500000 }).status, "进行中");
expect("running+pause", transition(STATES.RUNNING, "pause").state, STATES.PAUSED);
expect("paused+start", transition(STATES.PAUSED, "start", { remainingMs: 1000 }).state, STATES.RUNNING);
expect("running+reset", transition(STATES.RUNNING, "reset").state, STATES.READY);
expect("paused+reset", transition(STATES.PAUSED, "reset").state, STATES.READY);
expect("running+tick0", transition(STATES.RUNNING, "tick", { remainingMs: 0 }).state, STATES.DONE);
expect("running+tick0 status", transition(STATES.RUNNING, "tick", { remainingMs: 0 }).status, "时间到");
expect("running+tick0 finished flag", transition(STATES.RUNNING, "tick", { remainingMs: 0 }).finished, true);
expect("running+tick>0 no-op", transition(STATES.RUNNING, "tick", { remainingMs: 100 }), null);
expect("done+start restarts", transition(STATES.DONE, "start", { remainingMs: 0 }).state, STATES.RUNNING);
expect("done+reset", transition(STATES.DONE, "reset").state, STATES.READY);
expect("done+setMinutes", transition(STATES.DONE, "setMinutes", { minutes: 5 }).state, STATES.READY);
expect("ready+start zero rejected", transition(STATES.READY, "start", { remainingMs: 0 }), null);
expect("ready+setMinutes", transition(STATES.READY, "setMinutes", { minutes: 10 }).state, STATES.READY);
expect("running+setMinutes ignored", transition(STATES.RUNNING, "setMinutes", { minutes: 10 }), null);

// wall-clock simulated countdown
var now = 1700000000000;
var endAt = now + 3000;
expect("sim remaining 3000", remainingFrom(endAt, now), 3000);
expect("sim remaining 1000", remainingFrom(endAt, now + 2000), 1000);
expect("sim remaining 0", remainingFrom(endAt, now + 3000), 0);
expect("sim format mid", formatMs(remainingFrom(endAt, now + 1000)), "00:02");
expect("sim format end", formatMs(remainingFrom(endAt, now + 3000)), "00:00");

// default full-cycle math
expect("default cycle ms", minutesToMs(api.DEFAULT_MINUTES), 1500000);
expect("default display", formatMs(minutesToMs(api.DEFAULT_MINUTES)), "25:00");

if (fail) {
  console.log("FAILURES:", fail);
  process.exit(1);
}
console.log("ALL PASS (extracted from pomodoro.html pure core)");
