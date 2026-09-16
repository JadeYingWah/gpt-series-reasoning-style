/**
 * WG013-pomodoro-lite · A-skill logic verification
 * Extracts pure core from pomodoro.html and asserts state-machine behavior.
 *
 * Usage: node verify-logic.mjs
 * Exit 0 = all assertions passed; non-zero = at least one failed.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const __dirname = dirname(fileURLToPath(import.meta.url));
const htmlPath = join(__dirname, 'pomodoro.html');
const html = readFileSync(htmlPath, 'utf8');

// --- extract first <script> body ---
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
  console.error('FAIL: no <script> block found in pomodoro.html');
  process.exit(1);
}
const scriptSrc = scriptMatch[1];

// Run pure core in a sandbox without document/window (UI layer must not run)
const sandbox = { module: { exports: {} }, console };
vm.createContext(sandbox);
try {
  vm.runInContext(scriptSrc, sandbox, { filename: 'pomodoro.core.js' });
} catch (e) {
  console.error('FAIL: script threw when document is undefined:', e.message);
  process.exit(1);
}

const core = sandbox.module.exports;
if (!core || typeof core.createPomodoro !== 'function') {
  console.error('FAIL: PomodoroCore not exported via module.exports');
  process.exit(1);
}

// --- assertion helpers ---
let passed = 0;
let failed = 0;
const failures = [];

function assert(cond, label) {
  if (cond) {
    passed += 1;
    console.log('  PASS  ' + label);
  } else {
    failed += 1;
    failures.push(label);
    console.log('  FAIL  ' + label);
  }
}

function assertEq(actual, expected, label) {
  const ok = Object.is(actual, expected);
  if (ok) {
    passed += 1;
    console.log('  PASS  ' + label);
  } else {
    failed += 1;
    failures.push(label + '  (expected=' + JSON.stringify(expected) + ' actual=' + JSON.stringify(actual) + ')');
    console.log('  FAIL  ' + label + '  expected=' + JSON.stringify(expected) + ' actual=' + JSON.stringify(actual));
  }
}

console.log('=== WG013 A-skill · pomodoro core verification ===');
console.log('Source: ' + htmlPath);
console.log('---');

// 1. clampDurationMinutes
console.log('[clampDurationMinutes]');
assertEq(core.clampDurationMinutes(25), 25, 'accepts 25');
assertEq(core.clampDurationMinutes(1), 1, 'accepts lower bound 1');
assertEq(core.clampDurationMinutes(60), 60, 'accepts upper bound 60');
assertEq(core.clampDurationMinutes(0), null, 'rejects 0');
assertEq(core.clampDurationMinutes(61), null, 'rejects 61');
assertEq(core.clampDurationMinutes(-5), null, 'rejects negative');
assertEq(core.clampDurationMinutes(1.5), null, 'rejects non-integer 1.5');
assertEq(core.clampDurationMinutes('25'), 25, 'accepts numeric string "25"');
assertEq(core.clampDurationMinutes(''), null, 'rejects empty string');
assertEq(core.clampDurationMinutes('abc'), null, 'rejects non-numeric');
assertEq(core.clampDurationMinutes(null), null, 'rejects null');

// 2. formatClock
console.log('[formatClock]');
assertEq(core.formatClock(0), '00:00', '0ms → 00:00');
assertEq(core.formatClock(-1), '00:00', 'negative clamped → 00:00');
assertEq(core.formatClock(1), '00:01', '1ms → 00:01 (ceil to second)');
assertEq(core.formatClock(1000), '00:01', '1000ms → 00:01');
assertEq(core.formatClock(25 * 60 * 1000), '25:00', '25min → 25:00');
assertEq(core.formatClock(59 * 1000), '00:59', '59s → 00:59');
assertEq(core.formatClock(60 * 1000), '01:00', '60s → 01:00');
assertEq(core.formatClock(61 * 60 * 1000), '61:00', '61min → 61:00 (no hour wrap)');

// 3. create defaults
console.log('[createPomodoro]');
{
  const s = core.createPomodoro(25);
  assertEq(s.status, 'idle', 'default status idle');
  assertEq(s.remainingMs, 25 * 60 * 1000, 'default remaining = 25min');
  assertEq(s.endAt, null, 'default endAt null');
  assertEq(s.durationMs, 25 * 60 * 1000, 'default durationMs = 25min');
}

// 4. start / tick / finish
console.log('[start → tick → done]');
{
  const t0 = 1_000_000;
  const s = core.createPomodoro(25);
  core.start(s, t0);
  assertEq(s.status, 'running', 'start → running');
  assertEq(s.endAt, t0 + 25 * 60 * 1000, 'endAt = now + remaining');

  core.tick(s, t0 + 5000);
  assertEq(s.remainingMs, 25 * 60 * 1000 - 5000, 'tick advances remaining');
  assertEq(s.status, 'running', 'still running mid-timer');

  core.tick(s, t0 + 25 * 60 * 1000);
  assertEq(s.status, 'done', 'tick at end → done');
  assertEq(s.remainingMs, 0, 'remaining is 0 at done');
  assertEq(core.formatClock(s.remainingMs), '00:00', 'display 00:00 at done');
  assertEq(core.statusLabel(s.status), '时间到', 'status label 时间到');

  // overshot tick stays done at 0
  core.tick(s, t0 + 30 * 60 * 1000);
  assertEq(s.status, 'done', 'overshoot stays done');
  assertEq(s.remainingMs, 0, 'overshoot remaining clamped 0');
}

// 5. pause / resume
// NOTE: pause time is later than last tick — same-instant pause cannot detect a
// "does not freeze remaining" bug (mutation m03 survived that weak case).
console.log('[pause / resume]');
{
  const t0 = 2_000_000;
  const s = core.createPomodoro(25);
  core.start(s, t0);
  core.tick(s, t0 + 10_000);
  // user hits pause 3s after the last tick
  core.pause(s, t0 + 13_000);
  assertEq(s.status, 'paused', 'pause → paused');
  assertEq(s.remainingMs, 25 * 60 * 1000 - 13_000, 'pause freezes remaining at pause instant (not last tick)');
  assertEq(s.endAt, null, 'pause clears endAt');
  assert(
    s.remainingMs !== 25 * 60 * 1000 - 10_000,
    'pause remaining is NOT the stale last-tick value'
  );

  // frozen: tick while paused does nothing
  core.tick(s, t0 + 999_999);
  assertEq(s.remainingMs, 25 * 60 * 1000 - 13_000, 'tick while paused does not change remaining');

  core.start(s, t0 + 100_000);
  assertEq(s.status, 'running', 'resume → running');
  assertEq(s.endAt, t0 + 100_000 + (25 * 60 * 1000 - 13_000), 'resume endAt from frozen remaining');
}

// 6. reset
console.log('[reset]');
{
  const t0 = 3_000_000;
  const s = core.createPomodoro(25);
  core.start(s, t0);
  core.tick(s, t0 + 30_000);
  core.reset(s);
  assertEq(s.status, 'idle', 'reset → idle');
  assertEq(s.remainingMs, 25 * 60 * 1000, 'reset restores full duration');
  assertEq(s.endAt, null, 'reset clears endAt');
}

// 7. setDuration
console.log('[setDuration]');
{
  const s = core.createPomodoro(25);
  let r = core.setDuration(s, 15);
  assertEq(r.ok, true, 'setDuration 15 ok');
  assertEq(s.durationMs, 15 * 60 * 1000, 'durationMs updated to 15');
  assertEq(s.remainingMs, 15 * 60 * 1000, 'remaining updated to 15');
  assertEq(s.status, 'idle', 'stays idle after setDuration');

  r = core.setDuration(s, 0);
  assertEq(r.ok, false, 'setDuration 0 rejected');
  assertEq(s.durationMs, 15 * 60 * 1000, 'reject leaves duration unchanged');

  r = core.setDuration(s, 61);
  assertEq(r.ok, false, 'setDuration 61 rejected');

  r = core.setDuration(s, 2.5);
  assertEq(r.ok, false, 'setDuration 2.5 rejected (non-integer)');

  // running lock
  const t0 = 4_000_000;
  core.start(s, t0);
  r = core.setDuration(s, 30);
  assertEq(r.ok, false, 'setDuration while running rejected');
  assertEq(r.reason, 'running', 'reason=running');
  assertEq(s.durationMs, 15 * 60 * 1000, 'running reject leaves duration');

  core.pause(s, t0 + 1000);
  r = core.setDuration(s, 30);
  assertEq(r.ok, true, 'setDuration while paused ok');
  assertEq(s.remainingMs, 30 * 60 * 1000, 'paused setDuration resets remaining to new full duration');
}

// 8. restart after done uses configured duration
console.log('[restart after done]');
{
  const t0 = 5_000_000;
  const s = core.createPomodoro(25);
  core.start(s, t0);
  core.tick(s, t0 + 25 * 60 * 1000);
  assertEq(s.status, 'done', 'finished');
  core.start(s, t0 + 25 * 60 * 1000 + 1);
  assertEq(s.status, 'running', 'start after done → running');
  assertEq(s.remainingMs, 25 * 60 * 1000, 'restart remaining = full configured duration');
}

// 9. start while already running is no-op on endAt (does not re-anchor)
console.log('[double start]');
{
  const t0 = 6_000_000;
  const s = core.createPomodoro(10);
  core.start(s, t0);
  const end1 = s.endAt;
  core.start(s, t0 + 1000);
  assertEq(s.endAt, end1, 'second start does not re-anchor endAt');
  assertEq(s.status, 'running', 'still running');
}

// 10. pause when not running is no-op
console.log('[pause when idle]');
{
  const s = core.createPomodoro(25);
  core.pause(s, 123);
  assertEq(s.status, 'idle', 'pause on idle stays idle');
}

// 11. status labels
console.log('[statusLabel]');
assertEq(core.statusLabel('idle'), '就绪', 'idle → 就绪');
assertEq(core.statusLabel('running'), '计时中', 'running → 计时中');
assertEq(core.statusLabel('paused'), '已暂停', 'paused → 已暂停');
assertEq(core.statusLabel('done'), '时间到', 'done → 时间到');

// 12. static HTML checks (no external resources)
console.log('[static HTML]');
const external = html.match(/https?:\/\//gi);
assert(!external, 'no http(s) URLs in pomodoro.html');
assert(!/<script[^>]+src=/i.test(html), 'no external <script src>');
assert(!/<link[^>]+href=/i.test(html), 'no external <link href>');
assert(!/@import/i.test(html), 'no CSS @import');
assert(html.includes('时间到'), 'HTML contains 时间到 string (via statusLabel path)');
assert(html.includes('开始') && html.includes('暂停') && html.includes('重置'), 'has 开始/暂停/重置 controls');

// Mutation kill probes: prove assertions would fail if logic were wrong
// (documented separately — these are meta-checks that the *expectations* are hard-coded, not self-derived)
console.log('[meta · assertion independence]');
assert(
  core.formatClock(25 * 60 * 1000) !== core.formatClock(24 * 60 * 1000),
  'format distinguishes 25:00 vs 24:00'
);
assert(
  core.clampDurationMinutes(61) !== core.clampDurationMinutes(60),
  'clamp distinguishes valid 60 vs invalid 61'
);
assert(
  core.statusLabel('done') !== core.statusLabel('idle'),
  'status labels distinguish done vs idle'
);

// --- summary ---
console.log('---');
console.log(`RESULT: ${passed} passed, ${failed} failed`);
if (failed > 0) {
  console.log('Failures:');
  for (const f of failures) console.log('  - ' + f);
  process.exit(1);
}
process.exit(0);
