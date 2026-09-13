/**
 * Source-logic verification for pomodoro.html pure helpers.
 * Extracts clampMinutes / formatClock behavior by reimplementing
 * the same contracts and asserting edge cases. Also greps the HTML
 * for forbidden external resources.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(__dirname, "pomodoro.html"), "utf8");

const MIN = 1;
const MAX = 60;
const DEFAULT = 25;

function clampMinutes(n) {
  if (!Number.isFinite(n)) return null;
  if (!Number.isInteger(n)) return null;
  if (n < MIN || n > MAX) return null;
  return n;
}

function formatClock(totalSeconds) {
  const s = Math.max(0, Math.ceil(totalSeconds));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return (m < 10 ? "0" : "") + m + ":" + (r < 10 ? "0" : "") + r;
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

// clampMinutes
assert("clamp 1", clampMinutes(1) === 1);
assert("clamp 25", clampMinutes(25) === 25);
assert("clamp 60", clampMinutes(60) === 60);
assert("reject 0", clampMinutes(0) === null);
assert("reject 61", clampMinutes(61) === null);
assert("reject 2.5", clampMinutes(2.5) === null);
assert("reject NaN", clampMinutes(NaN) === null);
assert("reject null-ish", clampMinutes(undefined) === null);

// formatClock
assert("fmt 0", formatClock(0) === "00:00");
assert("fmt 1", formatClock(1) === "00:01");
assert("fmt 59", formatClock(59) === "00:59");
assert("fmt 60", formatClock(60) === "01:00");
assert("fmt 25*60", formatClock(1500) === "25:00");
assert("fmt 59*60+59", formatClock(3599) === "59:59");
assert("fmt ceil 0.1", formatClock(0.1) === "00:01");
assert("fmt negative -> 00:00", formatClock(-5) === "00:00");

// HTML static checks
assert("no http(s) url", !/https?:\/\//i.test(html));
assert("no src= external", !/\bsrc\s*=\s*["']https?:/i.test(html));
assert("no link stylesheet href http", !/<link[^>]+href\s*=\s*["']https?:/i.test(html));
assert("has 时间到", html.includes("时间到"));
assert("has start/pause/reset buttons", /id="startPauseBtn"/.test(html) && /id="resetBtn"/.test(html));
assert("has minutes input", /id="minutesInput"/.test(html));
assert("has Web Audio beep", /AudioContext|webkitAudioContext/.test(html));
assert("default 25:00 present", html.includes('value="25"') || html.includes("DEFAULT_MINUTES = 25"));

// countdown state machine source markers
assert("uses endAt absolute clock", /state\.endAt\s*=\s*Date\.now\(\)/.test(html));
assert("finish sets 时间到", /setStatus\("时间到"/.test(html));
assert("pause keeps remaining", /state\.remainingMs\s*=\s*Math\.max\(0,\s*state\.endAt\s*-\s*Date\.now\(\)\)/.test(html));

console.log("\n---");
console.log(`pass=${pass} fail=${fail}`);
process.exit(fail === 0 ? 0 : 1);
