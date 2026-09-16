/**
 * Source-level check for pomodoro.html pure helpers and static constraints.
 * Run: node check.js
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlPath = path.join(__dirname, "pomodoro.html");
const html = fs.readFileSync(htmlPath, "utf8");

const results = [];
function ok(name, pass, detail) {
  results.push({ name, pass, detail: detail || "" });
}

// 1. No external network resources
const urlRe = /(?:src|href)\s*=\s*["']([^"']+)["']/gi;
const externals = [];
let m;
while ((m = urlRe.exec(html)) !== null) {
  const u = m[1].trim();
  if (/^(https?:)?\/\//i.test(u) || /^cdn\./i.test(u)) externals.push(u);
}
ok("无 CDN/外链 src/href", externals.length === 0, externals.join(", ") || "none");

// 2. Extract pure helper functions via a minimal sandbox from the page IIFE
// We re-implement by evaluating the two functions copied from source for unit check.
// Prefer parsing: pull formatTime and clampInt function bodies from the script.
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
  ok("script 标签存在", false);
} else {
  ok("script 标签存在", true);
  const script = scriptMatch[1];

  // Eval only the helper definitions in isolation
  const helperSrc = `
    var MIN_MINUTES = 1;
    var MAX_MINUTES = 60;
    ${script.match(/function clampInt[\s\S]*?\n      }/)[0]}
    ${script.match(/function formatTime[\s\S]*?\n      }/)[0]}
  `;
  const sandbox = {};
  vm.createContext(sandbox);
  vm.runInContext(helperSrc, sandbox);

  // formatTime
  ok("formatTime(25*60*1000) === 25:00", sandbox.formatTime(25 * 60 * 1000) === "25:00", sandbox.formatTime(25 * 60 * 1000));
  ok("formatTime(0) === 00:00", sandbox.formatTime(0) === "00:00", sandbox.formatTime(0));
  ok("formatTime(999) === 00:01", sandbox.formatTime(999) === "00:01", sandbox.formatTime(999)); // ceil
  ok("formatTime(61*1000) === 01:01", sandbox.formatTime(61000) === "01:01", sandbox.formatTime(61000));
  ok("formatTime(-5) === 00:00", sandbox.formatTime(-5) === "00:00", sandbox.formatTime(-5));

  // clampInt
  ok("clampInt(25,1,60) === 25", sandbox.clampInt(25, 1, 60) === 25, String(sandbox.clampInt(25, 1, 60)));
  ok("clampInt(1,1,60) === 1", sandbox.clampInt(1, 1, 60) === 1);
  ok("clampInt(60,1,60) === 60", sandbox.clampInt(60, 1, 60) === 60);
  ok("clampInt(0,1,60) === null", sandbox.clampInt(0, 1, 60) === null);
  ok("clampInt(61,1,60) === null", sandbox.clampInt(61, 1, 60) === null);
  ok("clampInt(25.9,1,60) === 25", sandbox.clampInt(25.9, 1, 60) === 25);
  ok("clampInt('abc',1,60) === null", sandbox.clampInt("abc", 1, 60) === null);

  // Required UI ids / status string
  ok("含 开始/暂停 按钮 id", /id="startPause"/.test(script) || /id="startPause"/.test(html));
  ok("含 重置 按钮 id", /id="reset"/.test(html));
  ok("状态文案「时间到」", script.includes("时间到"));
  ok("默认 25 分钟", /value="25"/.test(html));
  ok("min=1 max=60 输入约束", /min="1"/.test(html) && /max="60"/.test(html));

  // Countdown uses wall-clock endAtMs + setInterval (self-consistent start/pause/reset)
  ok("使用 wall-clock endAtMs", script.includes("endAtMs"));
  ok("start 设置 endAtMs", /endAtMs\s*=\s*Date\.now\(\)\s*\+\s*remainingMs/.test(script));
  ok("pause 从 endAtMs 回写 remainingMs", /remainingMs\s*=\s*Math\.max\(0,\s*endAtMs\s*-\s*Date\.now\(\)\)/.test(script));
  ok("reset 恢复 totalSeconds", /remainingMs\s*=\s*totalSeconds\s*\*\s*1000/.test(script));
  ok("结束时 finished=true 且文案", /finished\s*=\s*true/.test(script) && /时间到/.test(script));
  ok("无框架库（无 react/vue/jquery）", !/react|vue|jquery/i.test(html));
}

let failed = 0;
for (const r of results) {
  const mark = r.pass ? "PASS" : "FAIL";
  if (!r.pass) failed++;
  console.log(`${mark}  ${r.name}${r.detail ? "  → " + r.detail : ""}`);
}
console.log(`\n${results.length - failed}/${results.length} passed`);
process.exit(failed ? 1 : 0);
