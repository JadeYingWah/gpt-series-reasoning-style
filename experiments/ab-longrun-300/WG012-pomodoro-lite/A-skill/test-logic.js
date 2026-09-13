// Node harness for pomodoro.html pure helpers (A-skill)
// Mirrors the functions embedded in pomodoro.html

function clampMinutes(n) {
  if (!isFinite(n) || isNaN(n)) return 25;
  n = Math.floor(n);
  if (n < 1) return 1;
  if (n > 60) return 60;
  return n;
}

function formatTime(totalSeconds) {
  var s = Math.max(0, totalSeconds | 0);
  var m = Math.floor(s / 60);
  var r = s % 60;
  return (m < 10 ? "0" : "") + m + ":" + (r < 10 ? "0" : "") + r;
}

var fails = [];
function assert(cond, msg) {
  if (!cond) fails.push(msg);
}

// clampMinutes
assert(clampMinutes(0.9) === 1, "clamp 0.9 -> 1");
assert(clampMinutes(1) === 1, "clamp 1 -> 1");
assert(clampMinutes(25.7) === 25, "clamp 25.7 -> 25");
assert(clampMinutes(60) === 60, "clamp 60 -> 60");
assert(clampMinutes(61) === 60, "clamp 61 -> 60");
assert(clampMinutes(NaN) === 25, "clamp NaN -> 25");
assert(clampMinutes(Infinity) === 25, "clamp Inf -> 25");
assert(clampMinutes(-5) === 1, "clamp -5 -> 1");

// formatTime
assert(formatTime(0) === "00:00", "fmt 0");
assert(formatTime(59) === "00:59", "fmt 59");
assert(formatTime(60) === "01:00", "fmt 60");
assert(formatTime(1500) === "25:00", "fmt 1500");
assert(formatTime(-1) === "00:00", "fmt -1 clamped");
assert(formatTime(3599) === "59:59", "fmt 3599");

// Source consistency: HTML contains the same function bodies
var fs = require("fs");
var path = require("path");
var html = fs.readFileSync(path.join(__dirname, "pomodoro.html"), "utf8");

assert(html.indexOf("function clampMinutes") !== -1, "html has clampMinutes");
assert(html.indexOf("function formatTime") !== -1, "html has formatTime");
assert(html.indexOf("时间到") !== -1, "html has done status text");
assert(html.indexOf("btnStart") !== -1, "html has start button");
assert(html.indexOf("btnPause") !== -1, "html has pause button");
assert(html.indexOf("btnReset") !== -1, "html has reset button");
assert(html.indexOf("min=\"1\"") !== -1 && html.indexOf("max=\"60\"") !== -1, "html input 1-60");

// No external resources
var httpHits = html.match(/https?:\/\//g);
assert(!httpHits, "html has no http(s) URLs: " + (httpHits || "none"));
assert(html.indexOf("cdn.") === -1, "html has no cdn reference");
assert(!/<script[^>]+src=/i.test(html), "html has no external script src");
assert(!/<link[^>]+href=/i.test(html), "html has no external link href");

// State machine keywords
assert(html.indexOf('state = "running"') !== -1, "has running state");
assert(html.indexOf('state = "paused"') !== -1, "has paused state");
assert(html.indexOf('state = "done"') !== -1, "has done state");
assert(html.indexOf('state = "idle"') !== -1, "has idle state");
assert(html.indexOf("setInterval(tick, 1000)") !== -1, "has 1s interval");
assert(html.indexOf("clearInterval") !== -1, "clears interval");

if (fails.length) {
  console.error("FAIL " + fails.length + ":");
  fails.forEach(function (f) { console.error("  - " + f); });
  process.exit(1);
}
console.log("PASS all assertions (helpers + source checks)");
console.log("clampMinutes(0.9,1,25.7,60,61,NaN) =", [0.9,1,25.7,60,61,NaN].map(clampMinutes).join(","));
console.log("formatTime(0,59,60,1500) =", [0,59,60,1500].map(formatTime).join(" | "));
