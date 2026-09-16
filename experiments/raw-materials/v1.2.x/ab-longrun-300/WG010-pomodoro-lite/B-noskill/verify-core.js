// Node verification for pomodoro.html pure core (extract + unit checks).
// Usage: node verify-core.js
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");

// 1) No external resources (CDN / remote scripts / images / fonts)
const externalPatterns = [
  /https?:\/\//gi,
  /\/\/cdn\./gi,
  /integrity\s*=/gi,
];
const hits = [];
for (const re of externalPatterns) {
  const m = html.match(re);
  if (m) hits.push({ pattern: String(re), matches: m });
}
// Allow only if nothing found. Note: our HTML intentionally has zero http(s) URLs.
const externalOk = hits.length === 0;

// 2) Extract the pure core script (between markers)
const startMark = "/* ---------- pure core";
const endMark = "/* Expose for Node source extraction";
const si = html.indexOf(startMark);
const ei = html.indexOf(endMark);
if (si < 0 || ei < 0) {
  console.error("FAIL: could not locate pure-core markers in HTML");
  process.exit(1);
}
// Include from startMark through the module.exports block
const exportMark = "window.PomodoroCore = PomodoroCore;";
const exportEnd = html.indexOf(exportMark, ei);
if (exportEnd < 0) {
  console.error("FAIL: could not locate export block");
  process.exit(1);
}
const afterExport = html.slice(exportEnd + exportMark.length);
const closeMatch = afterExport.match(/^\s*\}/);
const coreSrc = html.slice(
  si,
  exportEnd + exportMark.length + (closeMatch ? closeMatch[0].length : 0)
);

// 3) Eval core in isolated sandbox
const sandbox = {
  module: { exports: {} },
  exports: {},
  console,
  setInterval,
  clearInterval,
  Date,
  Number,
  Math,
  String,
};
sandbox.global = sandbox;
vm.createContext(sandbox);
vm.runInContext(coreSrc, sandbox);
const PomodoroCore = sandbox.module.exports;

let passed = 0;
let failed = 0;
function check(name, cond, detail) {
  if (cond) {
    passed += 1;
    console.log("PASS  " + name);
  } else {
    failed += 1;
    console.log("FAIL  " + name + (detail ? " — " + detail : ""));
  }
}

// parseMinutes
check("parse 25 -> 25", PomodoroCore.parseMinutes(25) === 25);
check("parse 1 -> 1", PomodoroCore.parseMinutes(1) === 1);
check("parse 60 -> 60", PomodoroCore.parseMinutes(60) === 60);
check("parse 0 -> null", PomodoroCore.parseMinutes(0) === null);
check("parse 61 -> null", PomodoroCore.parseMinutes(61) === null);
check("parse 1.5 -> null", PomodoroCore.parseMinutes(1.5) === null);
check("parse 'abc' -> null", PomodoroCore.parseMinutes("abc") === null);
check("parse '25' -> 25", PomodoroCore.parseMinutes("25") === 25);

// format
check("format 1500 = 25:00", PomodoroCore.format(1500) === "25:00");
check("format 0 = 00:00", PomodoroCore.format(0) === "00:00");
check("format 65 = 01:05", PomodoroCore.format(65) === "01:05");
check("format 59 = 00:59", PomodoroCore.format(59) === "00:59");

// create + start/pause/reset with fake clock
let fakeNow = 1_000_000;
const ticks = [];
let doneFired = 0;
const t = PomodoroCore.create(1, {
  now: () => fakeNow,
  onTick: (r) => ticks.push(r),
  onDone: () => { doneFired += 1; },
});
check("initial remaining = 60", t.remaining === 60);
check("initial running = false", t.running === false);
check("start returns true", t.start() === true);
check("running after start", t.running === true);

// start() calls immediate tick; remaining should still be 60
check("first tick 60", ticks[0] === 60);

// advance 10s and force interval tick via pause/start boundary
fakeNow += 10_000;
// pause computes remaining from endAt
t.pause();
check("pause remaining 50", t.remaining === 50, "got " + t.remaining);
check("not running after pause", t.running === false);

// resume and jump to end
t.start();
check("running after resume", t.running === true);
fakeNow += 50_000;
// call pause to sample, or start's internal interval may not fire in sync tests.
// Directly use pause after jump: endAt should be in the past -> remaining 0, but
// onDone only fires from tick(). So invoke start's path: pause then create new tick.
// Better: re-start after pause already done; use reset + manual finish path:
t.pause();
// remaining may be 0
check("after 50s more remaining <= 0", t.remaining <= 0, "got " + t.remaining);

// reset restores full
const t2 = PomodoroCore.create(2, { now: () => fakeNow });
check("2min remaining 120", t2.remaining === 120);
t2.start();
fakeNow += 30_000;
t2.pause();
check("2min after 30s = 90", t2.remaining === 90, "got " + t2.remaining);
const r = t2.reset();
check("reset back to 120", r === 120 && t2.remaining === 120);
check("reset not running", t2.running === false);

// onDone path: 1 second timer, advance past end, use start then force tick by
// creating with a controllable now and calling start which does tick immediately;
// we need the interval. Use real short interval for onDone.
const realDone = new Promise((resolve) => {
  const rt = PomodoroCore.create(1, {
    // force tiny total by monkey... can't. Instead use 1 min and mock now.
    now: () => Date.now(),
    onDone: () => resolve(true),
  });
  // Not waiting 60s. Use mock approach instead:
  rt.destroy();
  let n = 1_000;
  let id = null;
  const timers = [];
  const mockTimer = PomodoroCore.create(1, {
    now: () => n,
    onTick: (rem) => {
      // when remaining hits 0, onDone should fire inside create's tick
    },
    onDone: () => {
      resolve("done");
    },
  });
  mockTimer.start();
  n += 61 * 1000; // jump past end
  // Force a tick by pause (computes remaining) — but onDone only in tick().
  // tick is bound to interval; in Node setInterval still runs. Wait for it.
  // Actually create() uses setInterval(tick, 250). After start, interval is live.
  // Advancing mock `n` means next interval tick will see endAt past.
  // endAt was set at start to n0 + 60s. After n += 61s, tick fires onDone.
});

realDone.then((val) => {
  check("onDone fires after end", val === "done" || val === true);

  // HTML structural checks
  check("has 开始 button id", html.includes('id="startPause"'));
  check("has 重置 button id", html.includes('id="reset"'));
  check("has minutes input", html.includes('id="minutes"'));
  check("has apply button", html.includes('id="apply"'));
  check("status text 时间到 present", html.includes("时间到"));
  check("display default 25:00", html.includes("25:00"));
  check("no external URLs", externalOk, externalOk ? "" : JSON.stringify(hits).slice(0, 200));
  check("single html file (no script src)", !/<script\s+[^>]*src=/i.test(html));
  check("no link rel stylesheet remote", !/<link[^>]+href=["']https?:/i.test(html));

  console.log("\n---");
  console.log("passed=" + passed + " failed=" + failed);
  process.exit(failed === 0 ? 0 : 1);
}).catch((err) => {
  console.error("FAIL onDone path", err);
  process.exit(1);
});
