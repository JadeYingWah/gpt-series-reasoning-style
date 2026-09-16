/** 稳定性检查：连续跑 N 次浏览器实操验收，确认结论不抖动（非偶发通过） */
const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const N = 3;
const out = [];
for (let i = 1; i <= N; i++) {
  const r = spawnSync(process.execPath, [path.join(__dirname, "browser-verify.js")], { cwd: __dirname, encoding: "utf8", maxBuffer: 32 * 1024 * 1024 });
  const rep = fs.readFileSync(path.join(__dirname, "browser-report.txt"), "utf8");
  const sum = rep.split("\n").filter(l => /通过:|失败:|结论:/.test(l)).map(s => s.trim()).join("  ");
  out.push("run#" + i + "  status=" + r.status + "  " + sum);
}
fs.writeFileSync(path.join(__dirname, "_stability.txt"), out.join("\n") + "\n", "utf8");
