// 纯逻辑核对脚本：镜像 pomodoro.html 中的核心函数，用 Node 跑断言。
// 运行: node verify-logic.mjs

function clampMinutes(n) {
  if (!Number.isInteger(n)) return null;
  if (n < 1 || n > 60) return null;
  return n;
}

function parseMinutes(raw) {
  if (raw == null || raw === "") return null;
  var n = Number(raw);
  if (!Number.isFinite(n)) return null;
  if (!Number.isInteger(n)) return null;
  return clampMinutes(n);
}

function formatClock(ms) {
  if (ms < 0) ms = 0;
  var totalSec = Math.ceil(ms / 1000);
  var m = Math.floor(totalSec / 60);
  var s = totalSec % 60;
  return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
}

let failed = 0;
function assertEq(actual, expected, label) {
  const ok = Object.is(actual, expected);
  if (!ok) {
    failed++;
    console.error("FAIL", label, "expected=", expected, "actual=", actual);
  } else {
    console.log("OK  ", label, "=>", actual);
  }
}

// parseMinutes
assertEq(parseMinutes("25"), 25, 'parseMinutes("25")');
assertEq(parseMinutes("1"), 1, 'parseMinutes("1")');
assertEq(parseMinutes("60"), 60, 'parseMinutes("60")');
assertEq(parseMinutes("0"), null, 'parseMinutes("0") out of range');
assertEq(parseMinutes("61"), null, 'parseMinutes("61") out of range');
assertEq(parseMinutes("-5"), null, 'parseMinutes("-5")');
assertEq(parseMinutes("25.5"), null, 'parseMinutes("25.5") not integer');
assertEq(parseMinutes(""), null, 'parseMinutes("")');
assertEq(parseMinutes("abc"), null, 'parseMinutes("abc")');
assertEq(parseMinutes(null), null, 'parseMinutes(null)');

// formatClock
assertEq(formatClock(25 * 60 * 1000), "25:00", "formatClock(25min)");
assertEq(formatClock(0), "00:00", "formatClock(0)");
assertEq(formatClock(1000), "00:01", "formatClock(1s)");
assertEq(formatClock(599), "00:01", "formatClock(599ms) ceil");
assertEq(formatClock(60 * 1000), "01:00", "formatClock(1min)");
assertEq(formatClock(59 * 60 * 1000 + 59 * 1000), "59:59", "formatClock(59:59)");
assertEq(formatClock(-5), "00:00", "formatClock negative clamped");

// 状态机切换（与 HTML 一致的简化副本）
function createState(durationMs) {
  return {
    mode: "idle",
    durationMs,
    remainingMs: durationMs,
    endAtMs: null,
    timerId: null,
  };
}
function canStart(s) {
  return s.mode === "idle" || s.mode === "paused";
}
function applyDurationState(s, minutes) {
  if (s.mode === "running" || s.mode === "paused") return { ok: false, reason: "busy" };
  const m = parseMinutes(String(minutes));
  if (m == null) return { ok: false, reason: "invalid" };
  s.durationMs = m * 60 * 1000;
  s.remainingMs = s.durationMs;
  s.mode = "idle";
  s.endAtMs = null;
  return { ok: true, minutes: m };
}

{
  const s = createState(25 * 60 * 1000);
  assertEq(canStart(s), true, "idle can start");
  s.mode = "running";
  assertEq(canStart(s), false, "running cannot start again");
  assertEq(applyDurationState(s, 10).ok, false, "cannot apply while running");
  s.mode = "paused";
  assertEq(applyDurationState(s, 10).ok, false, "cannot apply while paused");
  s.mode = "idle";
  assertEq(applyDurationState(s, 10).ok, true, "apply 10 while idle");
  assertEq(s.durationMs, 10 * 60 * 1000, "duration applied");
  assertEq(s.remainingMs, 10 * 60 * 1000, "remaining reset to new duration");
  assertEq(applyDurationState(s, 0).ok, false, "apply 0 rejected");
  assertEq(applyDurationState(s, 61).ok, false, "apply 61 rejected");
}

// 倒计时到 0 应进入 done
{
  const s = createState(1000);
  s.mode = "running";
  // 模拟 endAt 已过
  s.endAtMs = Date.now() - 1;
  let remaining = s.endAtMs - Date.now();
  if (remaining <= 0) {
    s.remainingMs = 0;
    s.mode = "done";
  }
  assertEq(s.mode, "done", "mode -> done when remaining<=0");
  assertEq(s.remainingMs, 0, "remaining zero");
}

if (failed > 0) {
  console.error("\n" + failed + " assertion(s) failed");
  process.exit(1);
}
console.log("\nAll assertions passed.");
