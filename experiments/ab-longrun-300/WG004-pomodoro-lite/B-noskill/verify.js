// Extract script body from pomodoro.html and run unit checks.
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");

// No external resources check
const external = html.match(/https?:\/\/[^\s"'<>]+/g) || [];
const cdnLike = external.filter((u) => !u.includes("localhost") && !u.includes("127.0.0.1"));
if (cdnLike.length > 0) {
  console.error("FAIL: external URLs found:", cdnLike);
  process.exit(1);
}
if (/<script[^>]+src=/i.test(html) || /<link[^>]+href=/i.test(html)) {
  console.error("FAIL: external script/link tags found");
  process.exit(1);
}
console.log("PASS: no CDN / external links / src-link tags");

// Extract inline script (single script tag)
const m = html.match(/<script>\r?\n([\s\S]*?)\r?\n<\/script>/);
if (!m) {
  console.error("FAIL: could not extract script");
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
  clearTimeout,
};
sandbox.global = sandbox;
sandbox.window = undefined; // force DOM branch off
vm.createContext(sandbox);
vm.runInContext(code, sandbox, { filename: "pomodoro.inline.js" });

const { createTimer, formatTime, parseMinutes } = sandbox.module.exports;

function assert(cond, msg) {
  if (!cond) {
    console.error("FAIL:", msg);
    process.exit(1);
  }
  console.log("PASS:", msg);
}

// formatTime
assert(formatTime(0) === "00:00", "formatTime(0) === 00:00");
assert(formatTime(1500) === "25:00", "formatTime(1500) === 25:00");
assert(formatTime(59) === "00:59", "formatTime(59) === 00:59");
assert(formatTime(3600) === "60:00", "formatTime(3600) === 60:00");

// parseMinutes
assert(parseMinutes("25") === 25, "parseMinutes('25') === 25");
assert(parseMinutes("1") === 1, "parseMinutes('1') === 1");
assert(parseMinutes("60") === 60, "parseMinutes('60') === 60");
assert(parseMinutes("0") === null, "parseMinutes('0') === null");
assert(parseMinutes("61") === null, "parseMinutes('61') === null");
assert(parseMinutes("1.5") === null, "parseMinutes('1.5') === null");
assert(parseMinutes("-5") === null, "parseMinutes('-5') === null");
assert(parseMinutes("abc") === null, "parseMinutes('abc') === null");
assert(parseMinutes("") === null, "parseMinutes('') === null");

// Timer lifecycle with fake short total
{
  let ticks = [];
  let completed = false;
  const t = createTimer(3, (r, running) => ticks.push({ r, running }), () => {
    completed = true;
  });
  assert(t.remaining === 3 && !t.running, "initial remaining=3, not running");
  assert(t.start() === true, "start returns true");
  assert(t.running === true, "running after start");
  assert(t.start() === false, "second start is no-op");
  // wait for completion ~3.2s
  setTimeout(() => {
    assert(completed === true, "onComplete fired after countdown");
    assert(t.remaining === 0, "remaining is 0 at end");
    assert(t.running === false, "not running after complete");

    // reset after done
    assert(t.reset() === true, "reset after done");
    assert(t.remaining === 3, "reset restores remaining");
    assert(!t.running, "reset clears running");

    // pause mid-run
    t.start();
    setTimeout(() => {
      assert(t.pause() === true, "pause returns true while running");
      assert(t.running === false, "not running after pause");
      const pausedAt = t.remaining;
      assert(pausedAt < 3, "elapsed before pause");
      assert(t.pause() === false, "second pause is no-op");
      // resume
      assert(t.start() === true, "start resumes from paused");
      t.destroy();
      assert(t.running === false, "destroy stops timer");

    // reset with new duration
    t.reset(10);
    assert(t.remaining === 10, "reset(10) sets remaining=10");
    try {
      t.reset(0);
      assert(false, "reset(0) should throw");
    } catch (e) {
      assert(true, "reset(0) throws (must be positive integer)");
    }
    try {
      createTimer(1.5);
      assert(false, "createTimer(1.5) should throw");
    } catch (e) {
      assert(true, "createTimer(1.5) throws");
    }

      console.log("ALL TIMER LOGIC CHECKS PASSED");
      process.exit(0);
    }, 1100);
  }, 3300);
}
