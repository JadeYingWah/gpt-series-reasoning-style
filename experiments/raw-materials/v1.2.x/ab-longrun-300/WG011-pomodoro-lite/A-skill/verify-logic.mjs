/**
 * Node 核对：mock 最小 DOM 后执行 pomodoro.html 内联脚本，断言纯逻辑。
 * 用法：node verify-logic.mjs
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "pomodoro.html"), "utf8");

const httpRefs = html.match(/https?:\/\/[^\s"'<>]+/gi) || [];
const hrefs = html.match(/(?:src|href)\s*=\s*["'][^"']+["']/gi) || [];
console.log("EXTERNAL http(s) refs:", httpRefs.length === 0 ? "NONE" : httpRefs);
console.log("src/href attrs:", hrefs.length === 0 ? "NONE" : hrefs);
console.log("script tags:", (html.match(/<script/gi) || []).length);
console.log("link tags:", (html.match(/<link/gi) || []).length);

const m = html.match(/<script>([\s\S]*?)<\/script>/i);
if (!m) {
  console.error("FAIL: no inline <script>");
  process.exit(1);
}
const script = m[1];

function el(id) {
  return {
    id,
    textContent: "",
    value: id === "minutes" ? "25" : "",
    disabled: false,
    classList: { add() {}, remove() {}, contains() { return false; } },
    addEventListener() {},
    click() {},
  };
}

const elements = {
  display: el("display"),
  status: el("status"),
  btnStart: el("btnStart"),
  btnPause: el("btnPause"),
  btnReset: el("btnReset"),
  minutes: el("minutes"),
  btnApply: el("btnApply"),
  errMsg: el("errMsg"),
};

const sandbox = {
  module: { exports: {} },
  exports: {},
  window: {},
  document: {
    getElementById(id) {
      return elements[id] || el(id);
    },
  },
  setInterval,
  clearInterval,
  Date,
  Math,
  Number,
  console,
  AudioContext: undefined,
  webkitAudioContext: undefined,
};
sandbox.window = sandbox;

vm.runInNewContext(script, sandbox, { filename: "pomodoro-inline.js" });

const api = sandbox.window.__pomodoroLite || sandbox.module.exports;
const { parseMinutes, formatTime, createTimer } = api;
if (!parseMinutes || !formatTime || !createTimer) {
  console.error("FAIL: exports missing", Object.keys(api || {}));
  process.exit(1);
}

let pass = 0;
let fail = 0;
function assert(cond, msg) {
  if (cond) {
    pass++;
    console.log("PASS:", msg);
  } else {
    fail++;
    console.log("FAIL:", msg);
  }
}

// 1. 可配置时长
assert(parseMinutes(25).ok && parseMinutes(25).minutes === 25, "parseMinutes 25");
assert(parseMinutes("1").ok && parseMinutes("1").minutes === 1, "parseMinutes min 1");
assert(parseMinutes("60").ok && parseMinutes("60").minutes === 60, "parseMinutes max 60");
assert(!parseMinutes(0).ok, "reject 0");
assert(!parseMinutes(61).ok, "reject 61");
assert(!parseMinutes(2.5).ok, "reject non-integer");
assert(!parseMinutes("abc").ok, "reject non-number");

// 2. 显示格式
assert(formatTime(1500) === "25:00", "format 1500 → 25:00");
assert(formatTime(0) === "00:00", "format 0 → 00:00");
assert(formatTime(59) === "00:59", "format 59 → 00:59");
assert(formatTime(60) === "01:00", "format 60 → 01:00");

// 3. 开始/暂停/重置
let doneCalled = 0;
const t = createTimer(3, () => {}, () => { doneCalled++; });
assert(t.getState() === "idle", "init idle");
assert(t.start() === true && t.getState() === "running", "start → running");
assert(t.start() === false, "no double-start");
assert(t.pause() === true && t.getState() === "paused", "pause → paused");
assert(t.pause() === false, "no double-pause");
assert(t.start() === true && t.getState() === "running", "resume");
assert(t.reset() === true && t.getState() === "idle", "reset → idle");
assert(t.getRemaining() === 3, "reset restores remaining");

// 4. 到时
const t2 = createTimer(1, () => {}, () => { doneCalled++; });
t2.start();
await new Promise((r) => setTimeout(r, 1300));
assert(t2.getState() === "done", "elapsed → done");
assert(doneCalled >= 1, "onDone fired");
assert(t2.start() === false, "cannot start after done");

// 5. setTotal
const t3 = createTimer(25 * 60, () => {}, () => {});
assert(t3.setTotal(5 * 60) === true && t3.getRemaining() === 300, "setTotal when idle");
t3.start();
assert(t3.setTotal(10) === false, "setTotal blocked while running");
t3.pause();
assert(t3.setTotal(10) === true, "setTotal allowed when paused");

// 6. 状态文案常量存在
assert(elements.display.textContent === formatTime(t.getRemaining()) || elements.display.textContent === "03:00" || elements.display.textContent === "00:00" || elements.display.textContent === "01:00" || elements.display.textContent.length >= 5, "display rendered");
assert(typeof elements.status.textContent === "string" && elements.status.textContent.length > 0, "status rendered");

console.log("\nSUMMARY: pass=" + pass + " fail=" + fail);
process.exit(fail === 0 ? 0 : 1);
