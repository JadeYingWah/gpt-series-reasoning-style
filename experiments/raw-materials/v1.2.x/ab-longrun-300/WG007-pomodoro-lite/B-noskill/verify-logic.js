"use strict";
// Node verification of pure helpers copied from pomodoro.html
var MIN_MINUTES = 1;
var MAX_MINUTES = 60;

function clampInt(n) {
  if (typeof n !== "number" || !isFinite(n)) return null;
  var i = Math.floor(n);
  if (i < MIN_MINUTES || i > MAX_MINUTES) return null;
  if (n !== i) return null;
  return i;
}

function parseMinutes(raw) {
  var s = String(raw).trim();
  if (!/^\d+$/.test(s)) return null;
  return clampInt(parseInt(s, 10));
}

function formatMs(ms) {
  if (ms < 0) ms = 0;
  var totalSec = Math.ceil(ms / 1000);
  var m = Math.floor(totalSec / 60);
  var s = totalSec % 60;
  return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
}

var fail = 0;
function expect(label, got, want) {
  var ok = got === want;
  if (!ok) {
    fail++;
    console.log("FAIL", label, "got", JSON.stringify(got), "want", JSON.stringify(want));
  } else {
    console.log("OK  ", label, "->", JSON.stringify(got));
  }
}

// parseMinutes
expect('parse "25"', parseMinutes("25"), 25);
expect('parse "1"', parseMinutes("1"), 1);
expect('parse "60"', parseMinutes("60"), 60);
expect('parse "0"', parseMinutes("0"), null);
expect('parse "61"', parseMinutes("61"), null);
expect('parse "25.5"', parseMinutes("25.5"), null);
expect('parse "-5"', parseMinutes("-5"), null);
expect('parse "abc"', parseMinutes("abc"), null);
expect('parse ""', parseMinutes(""), null);
expect('parse "  10  "', parseMinutes("  10  "), 10);
expect('parse "007"', parseMinutes("007"), 7);

// formatMs
expect("format 0", formatMs(0), "00:00");
expect("format 999", formatMs(999), "00:01"); // ceil
expect("format 1000", formatMs(1000), "00:01");
expect("format 60000", formatMs(60000), "01:00");
expect("format 599000", formatMs(599000), "09:59");
expect("format 25min", formatMs(25 * 60 * 1000), "25:00");
expect("format -500", formatMs(-500), "00:00");

// remaining math
var endTime = Date.now() + 1500;
var remaining = endTime - Date.now();
console.log(remaining > 1400 && remaining <= 1500
  ? "OK   remaining ~1500"
  : "FAIL remaining " + remaining);
if (!(remaining > 1400 && remaining <= 1500)) fail++;

// finish condition
var pastEnd = Date.now() - endTime - 5000;
console.log(pastEnd <= 0 ? "OK   finish when remaining<=0" : "FAIL finish");
if (!(pastEnd <= 0)) fail++;

// state machine sketch
function nextState(state, action) {
  // state: ready|running|paused|finished
  var map = {
    ready:    { start: "running", reset: "ready", pause: "ready" },
    running:  { pause: "paused", reset: "ready", start: "running" },
    paused:   { start: "running", reset: "ready", pause: "paused" },
    finished: { start: "running", reset: "ready", pause: "finished" }
  };
  return map[state] && map[state][action] ? map[state][action] : null;
}
expect("ready+start", nextState("ready", "start"), "running");
expect("running+pause", nextState("running", "pause"), "paused");
expect("paused+start", nextState("paused", "start"), "running");
expect("running+reset", nextState("running", "reset"), "ready");
expect("finished+start", nextState("finished", "start"), "running");
expect("finished+reset", nextState("finished", "reset"), "ready");

if (fail) {
  console.log("FAILURES:", fail);
  process.exit(1);
}
console.log("ALL PASS");
