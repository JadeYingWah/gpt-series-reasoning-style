// Pure logic extracted from pomodoro.html for Node verification.
// Mirrors: formatMs, applyDuration validation, tick end condition.

var MIN_MINUTES = 1;
var MAX_MINUTES = 60;

function pad(n) {
  return (n < 10 ? '0' : '') + n;
}

function formatMs(ms) {
  if (ms < 0) ms = 0;
  var totalSec = Math.ceil(ms / 1000);
  var m = Math.floor(totalSec / 60);
  var s = totalSec % 60;
  return pad(m) + ':' + pad(s);
}

function parseMinutes(raw) {
  raw = String(raw).trim();
  if (!/^\d+$/.test(raw)) return { ok: false, reason: 'not positive integer' };
  var n = parseInt(raw, 10);
  if (n < MIN_MINUTES || n > MAX_MINUTES) return { ok: false, reason: 'out of range 1-60' };
  return { ok: true, n: n };
}

// --- assertions ---
var fails = 0;
function assert(name, cond) {
  if (!cond) {
    console.log('FAIL: ' + name);
    fails++;
  } else {
    console.log('PASS: ' + name);
  }
}

// formatMs
assert('25:00 at 25min', formatMs(25 * 60 * 1000) === '25:00');
assert('00:00 at 0', formatMs(0) === '00:00');
assert('00:00 at negative', formatMs(-5) === '00:00');
assert('00:01 at 1ms (ceil)', formatMs(1) === '00:01');
assert('01:00 at 60s', formatMs(60 * 1000) === '01:00');
assert('09:59 at 599s', formatMs(599 * 1000) === '09:59');
assert('10:00 at 600s', formatMs(600 * 1000) === '10:00');

// parseMinutes validation
assert('reject empty', parseMinutes('').ok === false);
assert('reject zero', parseMinutes('0').ok === false);
assert('reject negative', parseMinutes('-5').ok === false);
assert('reject 61', parseMinutes('61').ok === false);
assert('reject float', parseMinutes('2.5').ok === false);
assert('reject alpha', parseMinutes('abc').ok === false);
assert('accept 1', parseMinutes('1').ok && parseMinutes('1').n === 1);
assert('accept 25', parseMinutes('25').ok && parseMinutes('25').n === 25);
assert('accept 60', parseMinutes('60').ok && parseMinutes('60').n === 60);
assert('accept padded spaces', parseMinutes('  30  ').ok && parseMinutes('  30  ').n === 30);

// tick end condition (remainingMs <= 0 -> finished)
function simulateTick(remainingMs) {
  // mirrors tick() decision branch
  if (remainingMs <= 0) return { running: false, finished: true, status: '时间到' };
  return { running: true, finished: false, status: null };
}
var endState = simulateTick(0);
assert('tick at 0 -> finished 时间到', endState.finished && endState.status === '时间到');
var midState = simulateTick(1000);
assert('tick at 1s -> still running', midState.running && !midState.finished);

// start/pause/reset state machine (pure model)
function makeTimer(totalMs) {
  return {
    totalMs: totalMs,
    remainingMs: totalMs,
    running: false,
    finished: false,
    timerId: null,
    endAt: 0
  };
}
function tStart(s) {
  if (s.running || s.finished) return s;
  s.running = true;
  s.endAt = 'NOW+' + s.remainingMs; // abstract clock
  return s;
}
function tPause(s, nowMs) {
  if (!s.running) return s;
  s.remainingMs = nowMs; // abstract: endAt - now
  s.running = false;
  return s;
}
function tReset(s) {
  s.running = false;
  s.finished = false;
  s.remainingMs = s.totalMs;
  s.endAt = 0;
  return s;
}

var s = makeTimer(25 * 60 * 1000);
s = tStart(s);
assert('start sets running', s.running === true);
s = tStart(s); // double start no-op
assert('double start no-op still running once', s.running === true);
s = tPause(s, 10 * 60 * 1000);
assert('pause freezes remaining', s.running === false && s.remainingMs === 10 * 60 * 1000);
s = tPause(s); // pause while paused no-op
assert('pause while paused no-op', s.running === false && s.remainingMs === 10 * 60 * 1000);
s = tReset(s);
assert('reset restores full total', s.remainingMs === 25 * 60 * 1000 && s.running === false);

console.log('');
if (fails === 0) {
  console.log('ALL CHECKS PASSED');
  process.exit(0);
} else {
  console.log(fails + ' CHECKS FAILED');
  process.exit(1);
}
