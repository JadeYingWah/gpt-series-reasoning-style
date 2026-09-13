// Extract shipped source from pomodoro.html, stub DOM + clock, run real handlers.
// Path: A-skill/verify-extract.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, 'pomodoro.html');
const html = fs.readFileSync(htmlPath, 'utf8');

const m = html.match(/<script>\s*([\s\S]*?)\s*<\/script>/i);
if (!m) {
  console.error('FAIL: no inline <script> block');
  process.exit(1);
}
const source = m[1];

let pass = 0;
let fail = 0;
function assert(name, cond) {
  if (cond) {
    pass++;
    console.log('PASS: ' + name);
  } else {
    fail++;
    console.log('FAIL: ' + name);
  }
}

// --- controllable clock ---
let mockNow = 1_000_000_000_000;
const RealDate = Date;
class MockDate extends RealDate {
  constructor(...args) {
    if (args.length === 0) super(mockNow);
    else super(...args);
  }
  static now() {
    return mockNow;
  }
}

// --- minimal DOM stub ---
function makeEl(id) {
  return {
    id,
    textContent: '',
    className: '',
    disabled: false,
    value: '',
    listeners: {},
    addEventListener(type, fn) {
      (this.listeners[type] ||= []).push(fn);
    },
    click() {
      for (const fn of this.listeners.click || []) fn();
    },
    keydown(key) {
      for (const fn of this.listeners.keydown || []) fn({ key });
    }
  };
}

const els = {
  display: makeEl('display'),
  status: makeEl('status'),
  btnStart: makeEl('btnStart'),
  btnPause: makeEl('btnPause'),
  btnReset: makeEl('btnReset'),
  minutes: makeEl('minutes'),
  btnApply: makeEl('btnApply')
};

const intervals = new Map();
let nextIntervalId = 1;
const windowStub = {
  PomodoroLite: undefined
};

const sandboxGlobals = {
  window: windowStub,
  document: {
    getElementById(id) {
      if (!els[id]) throw new Error('unknown id ' + id);
      return els[id];
    }
  },
  setInterval(fn, ms) {
    const id = nextIntervalId++;
    intervals.set(id, { fn, ms });
    return id;
  },
  clearInterval(id) {
    intervals.delete(id);
  },
  Date: MockDate,
  console
};

// Run shipped IIFE in sandbox via Function constructor (ES5 source).
const factory = new Function(
  'window',
  'document',
  'setInterval',
  'clearInterval',
  'Date',
  'console',
  source + '\n//# sourceURL=pomodoro-inline.js'
);
factory(
  windowStub,
  sandboxGlobals.document,
  sandboxGlobals.setInterval,
  sandboxGlobals.clearInterval,
  MockDate,
  console
);

const api = windowStub.PomodoroLite;
assert('PomodoroLite exported', !!api && typeof api.formatMs === 'function');
assert('MIN=1 MAX=60 DEFAULT=25', api.MIN_MINUTES === 1 && api.MAX_MINUTES === 60 && api.DEFAULT_MINUTES === 25);

// formatMs
assert('formatMs 25min -> 25:00', api.formatMs(25 * 60 * 1000) === '25:00');
assert('formatMs 0 -> 00:00', api.formatMs(0) === '00:00');
assert('formatMs negative -> 00:00', api.formatMs(-5) === '00:00');
assert('formatMs 1ms -> 00:01 (ceil)', api.formatMs(1) === '00:01');
assert('formatMs 60s -> 01:00', api.formatMs(60 * 1000) === '01:00');
assert('formatMs 599s -> 09:59', api.formatMs(599 * 1000) === '09:59');
assert('formatMs 3599s -> 59:59', api.formatMs(3599 * 1000) === '59:59');

// parseMinutes
assert('reject empty', api.parseMinutes('').ok === false);
assert('reject zero', api.parseMinutes('0').ok === false);
assert('reject 61', api.parseMinutes('61').ok === false);
assert('reject float', api.parseMinutes('2.5').ok === false);
assert('reject alpha', api.parseMinutes('abc').ok === false);
assert('accept 1', api.parseMinutes('1').ok && api.parseMinutes('1').n === 1);
assert('accept 25', api.parseMinutes('25').ok && api.parseMinutes('25').n === 25);
assert('accept 60', api.parseMinutes('60').ok && api.parseMinutes('60').n === 60);
assert('accept padded', api.parseMinutes('  30  ').ok && api.parseMinutes('  30  ').n === 30);

// --- initial DOM state after init ---
let s = api.getState();
assert('init display 25:00', els.display.textContent === '25:00' && s.display === '25:00');
assert('init status 就绪', s.status === '就绪' && s.statusClass === '');
assert('init start enabled, pause disabled', s.startDisabled === false && s.pauseDisabled === true);
assert('init remaining = 25min', s.remainingMs === 25 * 60 * 1000 && s.running === false && s.finished === false);
assert('init minutes input 25', els.minutes.value === '25');
assert('no interval before start', intervals.size === 0);

// --- start ---
els.btnStart.click();
s = api.getState();
assert('start -> running', s.running === true && s.status === '进行中' && s.statusClass === 'running');
assert('start creates ticker', intervals.size === 1);
assert('start disables start, enables pause', s.startDisabled === true && s.pauseDisabled === false);

// double start no-op (still one ticker)
els.btnStart.click();
assert('double start no-op', intervals.size === 1 && api.getState().running === true);

// advance 10 minutes, tick
mockNow += 10 * 60 * 1000;
for (const { fn } of intervals.values()) fn();
s = api.getState();
assert('remainingMs after 10min', s.remainingMs === 15 * 60 * 1000 && s.display === '15:00');

// --- pause ---
els.btnPause.click();
s = api.getState();
assert('pause freezes remaining', s.running === false && s.remainingMs === 15 * 60 * 1000);
assert('pause status', s.status === '已暂停' && s.statusClass === 'paused');
assert('pause clears ticker', intervals.size === 0);
assert('pause re-enables start', s.startDisabled === false && s.pauseDisabled === true);

// pause while paused no-op
els.btnPause.click();
assert('pause while paused no-op', api.getState().remainingMs === 15 * 60 * 1000);

// resume continues from remaining
els.btnStart.click();
s = api.getState();
assert('resume running', s.running === true && s.remainingMs === 15 * 60 * 1000);
assert('resume creates ticker', intervals.size === 1);

// --- reset mid-run ---
els.btnReset.click();
s = api.getState();
assert('reset restores 25:00', s.remainingMs === 25 * 60 * 1000 && s.display === '25:00');
assert('reset ready', s.running === false && s.finished === false && s.status === '就绪');
assert('reset clears ticker', intervals.size === 0);

// --- finish path ---
els.btnStart.click();
mockNow += 25 * 60 * 1000 + 1;
for (const { fn } of [...intervals.values()]) fn();
s = api.getState();
assert('finish status 时间到', s.status === '时间到' && s.statusClass === 'done');
assert('finish display 00:00', s.display === '00:00' && s.remainingMs === 0);
assert('finish flags', s.finished === true && s.running === false);
assert('finish clears ticker', intervals.size === 0);
assert('finish disables start', s.startDisabled === true);

// --- reset after finish ---
els.btnReset.click();
s = api.getState();
assert('reset after finish ready 25:00', s.finished === false && s.display === '25:00' && s.status === '就绪');

// --- apply duration 1 ---
els.minutes.value = '1';
els.btnApply.click();
s = api.getState();
assert('apply 1 -> 01:00', s.display === '01:00' && s.remainingMs === 60 * 1000 && s.totalMs === 60 * 1000);
assert('apply 1 ready', s.status === '就绪' && s.running === false);

// apply 7 while conceptually "running" — apply resets
els.btnStart.click();
els.minutes.value = '7';
els.btnApply.click();
s = api.getState();
assert('apply 7 resets timer', s.display === '07:00' && s.running === false && s.finished === false);
assert('apply 7 stops ticker', intervals.size === 0);

// finish at 1-minute length
els.minutes.value = '1';
els.btnApply.click();
els.btnStart.click();
mockNow += 61_000;
for (const { fn } of [...intervals.values()]) fn();
s = api.getState();
assert('1min finish -> 时间到 00:00', s.status === '时间到' && s.display === '00:00');

// invalid apply
els.btnReset.click();
els.minutes.value = '0';
els.btnApply.click();
s = api.getState();
assert('reject 0 keeps prior length', s.display === '01:00' && s.totalMs === 60 * 1000);
assert('reject 0 shows error status', s.status.indexOf('1–60') !== -1 || s.status.indexOf('正整数') !== -1);
assert('input restored to valid', els.minutes.value === '1');

els.minutes.value = '61';
els.btnApply.click();
s = api.getState();
assert('reject 61 keeps prior', s.totalMs === 60 * 1000 && els.minutes.value === '1');

els.minutes.value = '60';
els.btnApply.click();
s = api.getState();
assert('accept 60 -> 60:00', s.display === '60:00' && s.totalMs === 60 * 60 * 1000);

// Enter key applies
els.minutes.value = '25';
els.minutes.keydown('Enter');
s = api.getState();
assert('Enter applies duration', s.display === '25:00' && s.totalMs === 25 * 60 * 1000);

console.log('');
console.log('pass=' + pass + ' fail=' + fail);
process.exit(fail ? 1 : 0);
