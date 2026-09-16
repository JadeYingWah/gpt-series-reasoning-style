/**
 * 变异杀伤检查（mutation kill test）
 * 目的：证明「全过」不是空转——把被防的错误人为制造一次，看断言是否变红。
 * 做法：备份 app.html → 注入变异 → 跑两套验证 → 收集失败断言 → 还原 → 校验哈希一致。
 */
"use strict";
const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const DIR = __dirname;
const APP = path.join(DIR, "app.html");
const sha = s => crypto.createHash("sha256").update(s, "utf8").digest("hex").slice(0, 16);

const baseline = fs.readFileSync(APP, "utf8");
const baseHash = sha(baseline);

const MUTANTS = [
  {
    name: "M1 回退「解析失败清空结果」修复",
    from: `          // 解析失败时清空结果区，避免把上一次的成功结果误读成本次结果
          output.value = "";
          outMetric.textContent = "无结果（解析失败）";
          showError(res, raw);`,
    to: `          showError(res, raw);
          updateOutputMetric();`,
    expect: "不残留"
  },
  {
    name: "M2 缩进 2 空格 → 4 空格",
    from: `var indent = mode === "minify" ? null : 2;`,
    to: `var indent = mode === "minify" ? null : 4;`,
    expect: "2 空格"
  }
];

function run(file) {
  const r = spawnSync(process.execPath, [path.join(DIR, file)], { cwd: DIR, encoding: "utf8", maxBuffer: 32 * 1024 * 1024 });
  const rep = file === "verify-json-tool.js" ? "verify-report.txt" : "browser-report.txt";
  const txt = fs.readFileSync(path.join(DIR, rep), "utf8");
  const fails = txt.split("\n").filter(l => l.trim().startsWith("[FAIL]")).map(l => l.trim());
  const sum = txt.split("\n").filter(l => /通过:|失败:/.test(l)).map(s => s.trim()).join("  ");
  return { status: r.status, fails, sum };
}

const out = [];
out.push("基线 app.html sha256(前16) = " + baseHash);
out.push("");

const results = [];
for (const m of MUTANTS) {
  if (baseline.indexOf(m.from) === -1) { out.push("!! 变异点未命中，跳过: " + m.name); continue; }
  fs.writeFileSync(APP, baseline.replace(m.from, m.to), "utf8");
  const mutatedHash = sha(fs.readFileSync(APP, "utf8"));
  let killed = false, detail = [];
  try {
    const u = run("verify-json-tool.js");
    const b = run("browser-verify.js");
    detail.push("单元: " + u.sum);
    detail.push("浏览器: " + b.sum);
    const all = u.fails.concat(b.fails);
    detail.push("失败断言: " + (all.length ? all.join(" || ") : "(无)"));
    killed = all.some(f => f.indexOf(m.expect) !== -1);
    if (!killed) detail.push("!! 未命中预期关键字「" + m.expect + "」");
  } finally {
    fs.writeFileSync(APP, baseline, "utf8");
  }
  results.push({ name: m.name, mutatedHash, killed, detail });
  out.push("【" + m.name + "】 变异体 hash=" + mutatedHash + "  被检出=" + (killed ? "是（断言变红）" : "否（危险：断言无鉴别力）"));
  detail.forEach(d => out.push("    " + d));
  out.push("");
}

const restoredHash = sha(fs.readFileSync(APP, "utf8"));
out.push("还原后 app.html sha256(前16) = " + restoredHash + "  → " + (restoredHash === baseHash ? "与基线一致（还原成功）" : "!! 与基线不一致"));
out.push("");
out.push("结论: 杀伤率 " + results.filter(r => r.killed).length + "/" + results.length);

fs.writeFileSync(path.join(DIR, "_mutation.txt"), out.join("\n") + "\n", "utf8");
if (restoredHash !== baseHash) process.exitCode = 2;
