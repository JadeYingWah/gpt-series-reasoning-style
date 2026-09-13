"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");
const m = html.match(/const PomodoroCore = \{[\s\S]*?\n    \};/);
if (!m) {
  console.error("EXTRACT FAIL");
  process.exit(1);
}
const src = m[0] + "\nmodule.exports = PomodoroCore;";
const tmp = path.join(os.tmpdir(), "pomodoro-core-a.js");
fs.writeFileSync(tmp, src);
delete require.cache[tmp];
const Core = require(tmp);

let pass = 0;
let fail = 0;
function ok(name, cond, detail) {
  if (cond) {
    pass++;
    console.log("PASS", name);
  } else {
    fail++;
    console.log("FAIL", name, detail || "");
  }
}

// parseMinutes
ok("parse 25", Core.parseMinutes(25) === 25);
ok("parse 1", Core.parseMinutes(1) === 1);
ok("parse 60", Core.parseMinutes(60) === 60);
ok('parse "10"', Core.parseMinutes("10") === 10);
ok("reject 0", Core.parseMinutes(0) === null);
ok("reject 61", Core.parseMinutes(61) === null);
ok("reject 2.5", Core.parseMinutes(2.5) === null);
ok("reject -1", Core.parseMinutes(-1) === null);
ok("reject abc", Core.parseMinutes("abc") === null);
ok("reject empty", Core.parseMinutes("") === null);
ok("reject null", Core.parseMinutes(null) === null);

// format
ok("format 0", Core.format(0) === "00:00");
ok("format 25*60", Core.format(1500) === "25:00");
ok("format 65", Core.format(65) === "01:05");
ok("format 59", Core.format(59) === "00:59");
ok("format clamp neg", Core.format(-5) === "00:00");

// timer with fake clock
let t = 0;
const fakeNow = function () {
  return t;
};
const ticks = [];
let doneCalled = 0;
const timer = Core.create(1, {
  now: fakeNow,
  onTick: function (r) {
    ticks.push(r);
  },
  onDone: function () {
    doneCalled++;
  },
});

ok("init remaining 60", timer.remaining === 60);
ok("init not running", timer.running === false);
ok("totalSeconds 60", timer.totalSeconds === 60);

ok("start true", timer.start() === true);
ok("running after start", timer.running === true);
ok("remaining still 60 at t=0", timer.remaining === 60);
ok("double start false", timer.start() === false);

t = 30000;
ok("pause true", timer.pause() === true);
ok("remaining after 30s", timer.remaining === 30, "got " + timer.remaining);
ok("not running after pause", timer.running === false);
ok("pause again false", timer.pause() === false);

t = 30000;
ok("start after pause", timer.start() === true);
t = 60000;

setTimeout(function () {
  ok("done called", doneCalled === 1, "got " + doneCalled);
  ok("remaining 0", timer.remaining === 0, "got " + timer.remaining);
  ok("not running after done", timer.running === false);
  ok("start after done false", timer.start() === false);

  t = 999999;
  const afterReset = timer.reset();
  ok("reset returns full", afterReset === 60);
  ok("remaining after reset", timer.remaining === 60);
  ok("not running after reset", timer.running === false);

  const links = html.match(/https?:\/\//g);
  ok("no http(s) URLs", !links, links && links.join(","));
  const cdn = /cdn|googleapis|unpkg|jsdelivr|cdnjs|fonts\.google/i.test(html);
  ok("no CDN refs", !cdn);

  ok("has 时间到", html.includes("时间到"));
  ok("has 开始", html.includes("开始"));
  ok("has 暂停", html.includes("暂停"));
  ok("has 重置", html.includes("重置"));
  ok("has min=1 max=60", /min="1"/.test(html) && /max="60"/.test(html));

  // destroy does not throw
  timer.destroy();
  ok("destroy ok", true);

  console.log("---");
  console.log("PASS", pass, "FAIL", fail);
  process.exit(fail ? 1 : 0);
}, 350);
