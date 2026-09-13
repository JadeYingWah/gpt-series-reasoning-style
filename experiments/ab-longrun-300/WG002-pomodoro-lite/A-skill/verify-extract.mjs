/**
 * Extract pure helpers from pomodoro.html and assert against them.
 * Discriminative check: execute the shipped source, not a reimplementation.
 * Uses a controllable clock so finish() is actually reached.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const __dirname = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(__dirname, "pomodoro.html"), "utf8");

const scriptMatch = html.match(/<script>\s*([\s\S]*?)\s*<\/script>/);
if (!scriptMatch) {
  console.error("FAIL no <script> block");
  process.exit(1);
}
const body = scriptMatch[1];

function makeEl(id) {
  const listeners = {};
  return {
    id,
    textContent: "",
    value: "",
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c); },
      remove(c) { this._s.delete(c); },
      contains(c) { return this._s.has(c); }
    },
    addEventListener(type, fn) {
      listeners[type] = listeners[type] || [];
      listeners[type].push(fn);
    },
    _emit(type) {
      (listeners[type] || []).forEach((fn) => fn({ target: this }));
    }
  };
}

const els = {
  time: makeEl("time"),
  status: makeEl("status"),
  startPauseBtn: makeEl("startPauseBtn"),
  resetBtn: makeEl("resetBtn"),
  minutesInput: makeEl("minutesInput")
};
els.minutesInput.value = "25";

let now = 1_000_000;
class MockDate {
  static now() { return now; }
  constructor(...args) {
    if (args.length) this._d = new Date(...args);
    else this._d = new Date(now);
  }
  valueOf() { return this._d.valueOf(); }
}

const intervals = new Map();
let nextId = 1;
const sandbox = {
  window: {},
  document: {
    getElementById(id) {
      if (!els[id]) throw new Error("missing el " + id);
      return els[id];
    }
  },
  setInterval(fn, ms) {
    const id = nextId++;
    intervals.set(id, { fn, ms });
    return id;
  },
  clearInterval(id) { intervals.delete(id); },
  Date: MockDate,
  Math,
  Number,
  parseInt,
  console,
  AudioContext: undefined
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;

function pumpTicks(n) {
  for (let i = 0; i < n; i++) {
    for (const { fn } of intervals.values()) fn();
  }
}

vm.createContext(sandbox);
vm.runInContext(body, sandbox);

const Logic = sandbox.window.PomodoroLogic;
if (!Logic) {
  console.error("FAIL PomodoroLogic not exported");
  process.exit(1);
}

let pass = 0;
let fail = 0;
function assert(name, cond, detail) {
  if (cond) {
    pass++;
    console.log("PASS", name);
  } else {
    fail++;
    console.log("FAIL", name, detail ?? "");
  }
}

assert("export clampMinutes", typeof Logic.clampMinutes === "function");
assert("export formatClock", typeof Logic.formatClock === "function");
assert("DEFAULT 25", Logic.DEFAULT_MINUTES === 25);
assert("MIN 1", Logic.MIN_MINUTES === 1);
assert("MAX 60", Logic.MAX_MINUTES === 60);

assert("clamp 1", Logic.clampMinutes(1) === 1);
assert("clamp 25", Logic.clampMinutes(25) === 25);
assert("clamp 60", Logic.clampMinutes(60) === 60);
assert("reject 0", Logic.clampMinutes(0) === null);
assert("reject 61", Logic.clampMinutes(61) === null);
assert("reject 2.5", Logic.clampMinutes(2.5) === null);
assert("reject NaN", Logic.clampMinutes(NaN) === null);

assert("fmt 0", Logic.formatClock(0) === "00:00");
assert("fmt 1", Logic.formatClock(1) === "00:01");
assert("fmt 25*60", Logic.formatClock(1500) === "25:00");
assert("fmt 59*60+59", Logic.formatClock(3599) === "59:59");
assert("fmt ceil", Logic.formatClock(0.1) === "00:01");
assert("fmt neg", Logic.formatClock(-5) === "00:00");

assert("initial time 25:00", els.time.textContent === "25:00", els.time.textContent);
assert("initial status 就绪", els.status.textContent === "就绪");
assert("initial button 开始", els.startPauseBtn.textContent === "开始");

els.startPauseBtn._emit("click");
assert("start -> 进行中", els.status.textContent === "进行中");
assert("start button -> 暂停", els.startPauseBtn.textContent === "暂停");

els.startPauseBtn._emit("click");
assert("pause -> 已暂停", els.status.textContent === "已暂停");
assert("pause button -> 开始", els.startPauseBtn.textContent === "开始");

els.resetBtn._emit("click");
assert("reset time", els.time.textContent === "25:00");
assert("reset status 就绪", els.status.textContent === "就绪");

els.minutesInput.value = "1";
els.minutesInput._emit("change");
assert("config 1 min -> 01:00", els.time.textContent === "01:00", els.time.textContent);

els.minutesInput.value = "0";
els.minutesInput._emit("change");
assert("reject 0 stays/clamps", els.minutesInput.value === "1" || els.time.textContent === "01:00",
  "input=" + els.minutesInput.value + " time=" + els.time.textContent);

els.minutesInput.value = "7";
els.minutesInput._emit("change");
assert("config 7 min -> 07:00", els.time.textContent === "07:00", els.time.textContent);

// 1-minute session, then advance wall clock past end to hit finish()
els.minutesInput.value = "1";
els.minutesInput._emit("change");
assert("reset to 01:00 before finish path", els.time.textContent === "01:00");
els.startPauseBtn._emit("click");
assert("running before advance", els.status.textContent === "进行中");
now += 61_000;
pumpTicks(1);
assert("finish status 时间到", els.status.textContent === "时间到", els.status.textContent);
assert("finish class done", els.status.classList.contains("done"));
assert("finish time 00:00", els.time.textContent === "00:00", els.time.textContent);
assert("finish button 开始", els.startPauseBtn.textContent === "开始");
assert("ticker cleared", intervals.size === 0, String(intervals.size));

// start again after finish should restart full duration
els.startPauseBtn._emit("click");
assert("restart after finish 01:00", els.time.textContent === "01:00", els.time.textContent);
assert("restart status 进行中", els.status.textContent === "进行中");

console.log("\n---");
console.log(`pass=${pass} fail=${fail}`);
process.exit(fail === 0 ? 0 : 1);
