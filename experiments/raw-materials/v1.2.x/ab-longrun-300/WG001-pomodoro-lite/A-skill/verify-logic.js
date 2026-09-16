"use strict";
const fs = require("fs");
const path = require("path");
const assert = require("assert");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");

const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) {
  console.error("NO_SCRIPT");
  process.exit(1);
}
const code = m[1];
// new Function keeps `var Pomodoro` function-scoped; return it explicitly.
// bootstrap() no-ops when document is undefined.
const Pomodoro = new Function(code + "\n;return Pomodoro;")();
if (!Pomodoro) {
  console.error("Pomodoro module not extracted");
  process.exit(1);
}

let pass = 0;
let fail = 0;
const failures = [];

function t(name, fn) {
  try {
    fn();
    console.log("PASS", name);
    pass++;
  } catch (e) {
    console.log("FAIL", name, e.message);
    fail++;
    failures.push(name + ": " + e.message);
  }
}

t("formatClock 25:00", () => assert.strictEqual(Pomodoro.formatClock(1500), "25:00"));
t("formatClock 0", () => assert.strictEqual(Pomodoro.formatClock(0), "00:00"));
t("formatClock 65", () => assert.strictEqual(Pomodoro.formatClock(65), "01:05"));

t("clampMinutes 25 ok", () => assert.deepStrictEqual(Pomodoro.clampMinutes(25), { ok: true, value: 25 }));
t("clampMinutes 1 ok", () => assert.deepStrictEqual(Pomodoro.clampMinutes(1), { ok: true, value: 1 }));
t("clampMinutes 60 ok", () => assert.deepStrictEqual(Pomodoro.clampMinutes(60), { ok: true, value: 60 }));
t("clampMinutes 0 reject", () => assert.strictEqual(Pomodoro.clampMinutes(0).ok, false));
t("clampMinutes 61 reject", () => assert.strictEqual(Pomodoro.clampMinutes(61).ok, false));
t("clampMinutes 1.5 reject", () => assert.strictEqual(Pomodoro.clampMinutes(1.5).ok, false));
t("clampMinutes abc reject", () => assert.strictEqual(Pomodoro.clampMinutes("abc").ok, false));

t("initial 25:00 ready", () => {
  const tm = Pomodoro.createTimer(25);
  const s = tm.getState();
  assert.strictEqual(s.remaining, 1500);
  assert.strictEqual(s.phase, "ready");
  assert.strictEqual(s.running, false);
  assert.strictEqual(s.finished, false);
});

t("start -> running", () => {
  const tm = Pomodoro.createTimer(25);
  tm.start();
  assert.strictEqual(tm.getState().phase, "running");
  assert.strictEqual(tm.getState().running, true);
});

t("pause -> paused, remaining held", () => {
  const tm = Pomodoro.createTimer(1);
  tm.start();
  tm.tick();
  tm.tick();
  const before = tm.getState().remaining;
  tm.pause();
  assert.strictEqual(tm.getState().phase, "paused");
  assert.strictEqual(tm.getState().remaining, before);
});

t("tick while paused is no-op", () => {
  const tm = Pomodoro.createTimer(1);
  tm.start();
  tm.pause();
  const before = tm.getState().remaining;
  tm.tick();
  assert.strictEqual(tm.getState().remaining, before);
});

t("tick while ready is no-op", () => {
  const tm = Pomodoro.createTimer(1);
  const before = tm.getState().remaining;
  tm.tick();
  assert.strictEqual(tm.getState().remaining, before);
});

t("reset restores full and ready", () => {
  const tm = Pomodoro.createTimer(2);
  tm.start();
  for (let i = 0; i < 10; i++) tm.tick();
  tm.reset();
  const s = tm.getState();
  assert.strictEqual(s.remaining, 120);
  assert.strictEqual(s.phase, "ready");
});

t("full countdown 1min -> finished", () => {
  const tm = Pomodoro.createTimer(1);
  tm.start();
  for (let i = 0; i < 60; i++) tm.tick();
  const s = tm.getState();
  assert.strictEqual(s.remaining, 0);
  assert.strictEqual(s.phase, "finished");
  assert.strictEqual(s.finished, true);
  assert.strictEqual(s.running, false);
});

t("start after finished is no-op", () => {
  const tm = Pomodoro.createTimer(1);
  tm.start();
  for (let i = 0; i < 60; i++) tm.tick();
  tm.start();
  assert.strictEqual(tm.getState().phase, "finished");
});

t("setMinutes mid-run resets to ready", () => {
  const tm = Pomodoro.createTimer(25);
  tm.start();
  tm.tick();
  tm.setMinutes(10);
  const s = tm.getState();
  assert.strictEqual(s.remaining, 600);
  assert.strictEqual(s.phase, "ready");
});

t("setMinutes invalid throws", () => {
  const tm = Pomodoro.createTimer(25);
  assert.throws(() => tm.setMinutes(0), RangeError);
  assert.throws(() => tm.setMinutes(61), RangeError);
});

t("createTimer invalid throws", () => {
  assert.throws(() => Pomodoro.createTimer(0), RangeError);
  assert.throws(() => Pomodoro.createTimer(100), RangeError);
});

t("onChange notifies on start+tick", () => {
  const tm = Pomodoro.createTimer(1);
  let calls = 0;
  tm.onChange(() => {
    calls++;
  });
  tm.start();
  tm.tick();
  assert.ok(calls >= 2, "expected at least 2 notifications, got " + calls);
});

t("status text mapping covers 时间到", () => {
  // Source-level: finished phase maps to 时间到 in render()
  assert.ok(html.indexOf('text = "时间到"') !== -1 || html.indexOf("'时间到'") !== -1);
  assert.ok(/时间到/.test(html));
});

t("no external URL attributes", () => {
  const re = /(?:href|src)\s*=\s*["']([^"']+)["']/gi;
  const hrefs = [];
  let mm;
  while ((mm = re.exec(html)) !== null) hrefs.push(mm[1]);
  const external = hrefs.filter(function (u) {
    return /^(https?:)?\/\//i.test(u);
  });
  assert.deepStrictEqual(external, [], "external refs: " + external.join(","));
});

t("no CDN load tags", () => {
  // Ignore Chinese hint text "无 CDN"; only flag real resource loads.
  assert.ok(!/<\s*script\b[^>]*\bsrc\s*=/i.test(html));
  assert.ok(!/<\s*link\b/i.test(html));
  assert.ok(!/<\s*img\b/i.test(html));
  assert.ok(!/<\s*iframe\b/i.test(html));
});

t("default display 25:00 in markup", () => {
  assert.ok(/id="time"[^>]*>25:00</.test(html) || html.indexOf('id="time"') !== -1);
  assert.ok(html.indexOf("25:00") !== -1);
});

console.log("---");
console.log("RESULT pass=" + pass + " fail=" + fail);
process.exit(fail ? 1 : 0);
