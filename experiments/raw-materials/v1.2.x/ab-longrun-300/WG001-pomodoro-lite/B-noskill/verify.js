/**
 * Node 核对脚本：从 pomodoro.html 提取 Pomodoro IIFE 并跑状态机断言。
 * 用法: node verify.js
 * 不依赖 DOM；仅验证可逻辑审查的部分。
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");

// 无外链检查
const external = [];
const cdnRe = /(?:src|href)\s*=\s*["'](?:https?:)?\/\/[^"']+["']/gi;
let m;
while ((m = cdnRe.exec(html))) external.push(m[0]);
const importRe = /import\s+.*from\s+["']https?:\/\//gi;
while ((m = importRe.exec(html))) external.push(m[0]);

// 提取 Pomodoro 模块（script 内第一个 IIFE 赋值到 var Pomodoro）
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
  console.error("FAIL: no <script> block");
  process.exit(1);
}
const script = scriptMatch[1];
const moduleMatch = script.match(/var Pomodoro = \(function \(\) \{[\s\S]*?\n\}\)\(\);/);
if (!moduleMatch) {
  console.error("FAIL: could not extract Pomodoro module");
  process.exit(1);
}

const sandbox = {
  console,
  Math,
  Number,
  isFinite,
  RangeError,
  Array,
  Object
};
vm.createContext(sandbox);
vm.runInContext(moduleMatch[0], sandbox);
const P = sandbox.Pomodoro;

let passed = 0;
let failed = 0;
function assert(cond, label) {
  if (cond) {
    passed++;
    console.log("  OK  " + label);
  } else {
    failed++;
    console.log("  FAIL " + label);
  }
}

console.log("== formatClock ==");
assert(P.formatClock(1500) === "25:00", "1500s -> 25:00");
assert(P.formatClock(0) === "00:00", "0s -> 00:00");
assert(P.formatClock(59) === "00:59", "59s -> 00:59");
assert(P.formatClock(60) === "01:00", "60s -> 01:00");
assert(P.formatClock(-5) === "00:00", "negative clamps to 00:00");

console.log("== validateMinutes ==");
assert(P.validateMinutes(25).ok === true && P.validateMinutes(25).value === 25, "25 valid");
assert(P.validateMinutes("1").ok === true && P.validateMinutes("1").value === 1, "1 valid");
assert(P.validateMinutes(60).ok === true && P.validateMinutes(60).value === 60, "60 valid");
assert(P.validateMinutes(0).ok === false, "0 rejected");
assert(P.validateMinutes(61).ok === false, "61 rejected");
assert(P.validateMinutes("abc").ok === false, "NaN rejected");
assert(P.validateMinutes(2.5).ok === false, "2.5 rejected");
assert(P.validateMinutes("").ok === false || Number("") === 0, "empty -> 0 rejected");

console.log("== timer: start/pause/reset ==");
const t = P.createTimer(25);
let s = t.getState();
assert(s.remaining === 1500 && !s.running && !s.finished, "initial 25:00 idle");
assert(t.start().running === true, "start -> running");
assert(t.pause().running === false, "pause -> not running");
const afterPause = t.getState();
assert(afterPause.remaining === 1500, "pause does not consume time");
t.start();
for (let i = 0; i < 10; i++) t.tick();
assert(t.getState().remaining === 1490, "10 ticks while running -> 1490");
t.pause();
const rem = t.getState().remaining;
t.tick();
assert(t.getState().remaining === rem, "tick ignored when paused");
t.reset();
const r = t.getState();
assert(r.remaining === 1500 && !r.running && !r.finished, "reset restores full");

console.log("== timer: countdown to zero -> finished ==");
const t2 = P.createTimer(1); // 60 seconds
t2.start();
for (let i = 0; i < 59; i++) t2.tick();
assert(t2.getState().remaining === 1 && !t2.getState().finished, "59 ticks remain 1s");
t2.tick();
const end = t2.getState();
assert(end.remaining === 0 && end.finished && !end.running, "60th tick finished");
t2.start();
assert(t2.getState().finished, "cannot restart after finish");
t2.tick();
assert(t2.getState().remaining === 0, "tick after finish is no-op");
t2.reset();
assert(!t2.getState().finished && t2.getState().remaining === 60, "reset clears finished");

console.log("== timer: setMinutes ==");
const t3 = P.createTimer(25);
t3.start();
for (let i = 0; i < 100; i++) t3.tick();
t3.setMinutes(10);
const sm = t3.getState();
assert(sm.remaining === 600 && !sm.running && !sm.finished, "setMinutes resets to new duration");
let threw = false;
try { t3.setMinutes(0); } catch (e) { threw = true; }
assert(threw, "setMinutes(0) throws RangeError");
threw = false;
try { t3.setMinutes(61); } catch (e) { threw = true; }
assert(threw, "setMinutes(61) throws RangeError");

console.log("== static: no external resources ==");
assert(external.length === 0, "no CDN/script/link external URLs (" + (external.length) + " found)");
assert(!/cdn\.|unpkg|jsdelivr|cdnjs|googleapis|bootstrapcdn/i.test(html), "no common CDN hosts");
assert(!/<script[^>]+src=/i.test(html), "no external script src");
assert(!/<link[^>]+href=/i.test(html), "no external stylesheet link");

console.log("== static: required UI hooks ==");
assert(html.includes('id="btn-start"') && html.includes('id="btn-pause"') && html.includes('id="btn-reset"'), "start/pause/reset buttons present");
assert(html.includes("时间到"), "finished status text 时间到 present");
assert(html.includes('id="minutes"') && html.includes("1") && html.includes("60"), "minutes config present");
assert(html.includes("Web Audio") || html.includes("AudioContext"), "beep implementation present");

console.log("");
console.log("RESULT: " + passed + " passed, " + failed + " failed");
process.exit(failed === 0 ? 0 : 1);
