#!/usr/bin/env node
/**
 * M3 个人主页 v2（浅色主题+联系表单）· 交叉验证（独立方法 2：Node.js/V8 独立运行时 + 独立实现）
 *
 * 变更 v2：浅色主题检查（亮度>0.85）、14 组浅色对比度用例、表单静态接线检查、
 *          动态执行从 HTML 提取的 validateContact 纯函数（输入域分段用例）。
 * 与 Python 主验证（verify_m3.py）互不共享代码，独立复算。
 * 输出: stdout + evidence/result_crosscheck.txt；全部通过 RESULT: ALL GREEN，否则 FAIL（exit 1）
 *
 * 注：原计划 PowerShell 复算，因宿主安全策略拦截 .ps1 文件执行与 Invoke-Expression，
 *     改用 Node.js 独立运行时——方法独立性（第二运行时+第二实现）不受影响。
 */
"use strict";
const fs = require("fs");
const path = require("path");

const evidenceDir = __dirname;
const htmlPath = path.resolve(evidenceDir, "..", "index.html");
const outPath = path.join(evidenceDir, "result_crosscheck.txt");

let pass = 0, fail = 0;
const lines = [];
function check(name, ok, detail = "") {
  const entry = `${ok ? "PASS" : "FAIL"} | ${name}` + (detail ? ` | ${detail}` : "");
  if (ok) pass++; else fail++;
  lines.push(entry);
}

// ---- 读取（Node 独立 UTF-8 解码路径）----
let text;
try {
  const raw = fs.readFileSync(htmlPath);
  text = new TextDecoder("utf-8", { fatal: true }).decode(raw); // 非 UTF-8 抛错
  check("单文件存在且可按 UTF-8 严格解码", true, `${raw.length} bytes, BOM=${raw[0] === 0xef ? "有" : "无"}`);
} catch (e) {
  console.error(`FATAL: 读取/解码 index.html 失败: ${e.message}`);
  process.exit(2);
}

// ---- 1. 结构计数（变更后：结构保留 + 表单）----
const cards  = (text.match(/class="project-card"/g) || []).length;
const groups = (text.match(/class="skill-group"/g) || []).length;
const tags   = (text.match(/class="tag"/g) || []).length;
const hasAvatar = /class="avatar"/.test(text) && text.includes("<svg");

check("头像占位存在（.avatar + 内联 SVG）", hasAvatar);
check("技能区块存在（分组≥1 且 标签≥5，结构保留）", groups >= 1 && tags >= 5, `分组 ${groups}，标签 ${tags}`);
check("项目卡片恰好 3 张（结构保留）", cards === 3, `实际 ${cards} 张`);
check("联系表单存在（#contact-form + novalidate）", /<form[^>]+id="contact-form"/.test(text) && /<form[^>]+novalidate/.test(text));
// 属性顺序无关的字段检查：提取完整标签后逐属性断言
function fieldOk(id, expectedType, isTextarea) {
  const pat = isTextarea
    ? new RegExp(`<textarea[^>]*id="${id}"[^>]*>`)
    : new RegExp(`<input[^>]*id="${id}"[^>]*>`);
  const m = text.match(pat);
  if (!m) return "标签未找到";
  if (!isTextarea && !new RegExp(`type="${expectedType}"`).test(m[0])) return "type 不匹配";
  if (!/\brequired\b/.test(m[0])) return "缺 required";
  if (!new RegExp(`<label[^>]+for="${id}"`).test(text)) return "缺 label[for]";
  return null;
}
const fName = fieldOk("cf-name", "text", false);
const fEmail = fieldOk("cf-email", "email", false);
const fMessage = fieldOk("cf-message", "textarea", true);
check("三字段齐备且 required（name/email/message + label[for]，属性顺序无关）",
      !fName && !fEmail && !fMessage,
      [fName, fEmail, fMessage].filter(Boolean).join("; ") || "姓名/邮箱/留言均通过");
check("成功提示存在且初始 hidden",
      /id="form-success"/.test(text) && (/<p[^>]+id="form-success"[^>]*hidden/.test(text) || /<p[^>]+hidden[^>]*id="form-success"/.test(text)));

// ---- 2. 外部依赖（独立实现：全量属性值抽取 + 关键词全文扫描；内联脚本允许）----
const depHits = [];
const attrRe = /(?:href|src)\s*=\s*"([^"]*)"/g;
let am;
while ((am = attrRe.exec(text)) !== null) {
  const v = am[1];
  if (!(v === "#" || v.startsWith("mailto:"))) depHits.push(`属性值违规: ${v}`);
}
if (/<script[^>]*\bsrc\s*=/i.test(text)) depHits.push("script 外链 src");
if (/<link\b/i.test(text)) depHits.push("link 标签");
if (/@import/i.test(text)) depHits.push("CSS @import");
if (/https?:\/\/|\/\//.test(text)) depHits.push("外部 URL / 协议相对地址字面量");
check("外部依赖 0 命中（属性白名单 + 关键词扫描）", depHits.length === 0,
  depHits.length ? depHits.join("; ") : `扫描干净（href/src 共 ${(text.match(/(?:href|src)\s*=/g) || []).length} 处，均白名单内）`);

// ---- 3. 表单校验逻辑动态执行（独立路径：V8 实跑交付物内的纯函数）----
let dynamicOk = false, dynamicDetail = "";
const fnM = text.match(/\/\*VALIDATE-START\*\/([\s\S]*?)\/\*VALIDATE-END\*\//);
if (!fnM) {
  dynamicDetail = "未找到 VALIDATE 标记的 validateContact 纯函数";
} else {
  try {
    const validateContact = new Function(fnM[1] + "; return validateContact;")();

    // 输入域分段用例：正常值 / 边界值（空白串、格式变体）/ 异常值（全空、部分缺失）
    const cases = [
      // [描述, 输入, 期望错误字段集合]
      ["正常值：全填合法", { name: "张三", email: "zhang@example.com", message: "你好" }, []],
      ["正常值：复杂合法邮箱", { name: "Li Si", email: "user.name+tag@sub.domain.cn", message: "hi" }, []],
      ["异常值：全空", { name: "", email: "", message: "" }, ["name", "email", "message"]],
      ["边界值：全空白串", { name: "   ", email: "  ", message: "\n\t " }, ["name", "email", "message"]],
      ["边界值：最小合法邮箱 a@b.c", { name: "x", email: "a@b.c", message: "m" }, []],
      ["异常值：无@（plainaddress）", { name: "x", email: "plainaddress", message: "m" }, ["email"]],
      ["边界值：缺域名主体 a@b.", { name: "x", email: "a@b.", message: "m" }, ["email"]],
      ["边界值：缺 TLD a@b", { name: "x", email: "a@b", message: "m" }, ["email"]],
      ["边界值：缺 local @b.c", { name: "x", email: "@b.c", message: "m" }, ["email"]],
      ["异常值：local 含空格 a b@c.d", { name: "x", email: "a b@c.d", message: "m" }, ["email"]],
      ["部分缺失：仅缺姓名", { name: "", email: "a@b.c", message: "hi" }, ["name"]],
      ["部分缺失：仅邮箱格式错", { name: "x", email: "bad", message: "hi" }, ["email"]],
    ];
    const bad = [];
    for (const [desc, input, expected] of cases) {
      const errs = validateContact(input);
      const got = Object.keys(errs).sort();
      const want = expected.slice().sort();
      if (JSON.stringify(got) !== JSON.stringify(want)) {
        bad.push(`${desc}: 期望[${want}] 实得[${got}]`);
      }
    }
    dynamicOk = bad.length === 0;
    dynamicDetail = dynamicOk ? `${cases.length} 个分段用例全部符合期望` : bad.join(" | ");
  } catch (e) {
    dynamicDetail = `执行失败: ${e.message}`;
  }
}
check("表单校验逻辑动态执行（V8 实跑，输入域分段）", dynamicOk, dynamicDetail);

// ---- 4. 事件接线静态检查（与动态路径互补的第二角度）----
check("提交接线（submit 监听 + preventDefault + 成功/失败分支）",
      /addEventListener\(["']submit["']/.test(text) &&
      /preventDefault\(\)/.test(text) &&
      /form\.reset\(\)/.test(text) &&
      /success\.hidden\s*=\s*false/.test(text) &&
      /success\.hidden\s*=\s*true/.test(text));
check("错误提示元素齐备（err-name/err-email/err-message）",
      ["name", "email", "message"].every(f => new RegExp(`id="err-${f}"`).test(text)));

// ---- 5. WCAG 对比度（独立实现：Math.pow 路径；浅色调色板 14 组）----
function lum(hex) {
  const h = hex.replace("#", "");
  const ch = [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16) / 255);
  const lin = c => (c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  return 0.2126 * lin(ch[0]) + 0.7152 * lin(ch[1]) + 0.0722 * lin(ch[2]);
}
function contrast(fg, bg) {
  const l1 = lum(fg), l2 = lum(bg);
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
}
function blend(fg, bg, alpha) {
  const fh = fg.replace("#", ""), bh = bg.replace("#", "");
  const mx = [0, 2, 4].map(i => {
    const f = parseInt(fh.slice(i, i + 2), 16), b = parseInt(bh.slice(i, i + 2), 16);
    return Math.round(f * alpha + b * (1 - alpha));
  });
  return "#" + mx.map(v => v.toString(16).padStart(2, "0")).join("");
}

const pairs = [
  ["#1f2937", "#f5f7fa", "正文 on 页面背景", 16, false],
  ["#1f2937", "#ffffff", "卡片正文 on surface", 16, false],
  ["#1f2937", "#eef1f5", "标签文字 on elevated", 14, false],
  ["#4b5563", "#f5f7fa", "副标题/表单标签/页脚链接 on 背景", 16, false],
  ["#4b5563", "#ffffff", "项目描述 on surface", 14, false],
  ["#626b78", "#f5f7fa", "状态/页脚弱化文字 on 背景", 14, false],
  ["#1d4ed8", "#f5f7fa", "链接 on 背景", 16, false],
  ["#1d4ed8", "#ffffff", "卡片内链接 on surface", 14, false],
  ["#1d4ed8", blend("#1d4ed8", "#ffffff", 0.08), "技术标签 on 混合底色(rgba 8%)", 12, false],
  ["#0f172a", "#3b82f6", "头像文字 on 渐变暗端", 30, true],
  ["#0f172a", "#93c5fd", "头像文字 on 渐变亮端", 30, true],
  ["#b42318", "#f5f7fa", "表单错误提示 on 背景", 14, false],
  ["#166534", blend("#166534", "#f5f7fa", 0.08), "成功提示 on 浅绿底(rgba 8%)", 14, false],
  ["#ffffff", "#1d4ed8", "按钮文字 on 按钮底", 14, false],
];
for (const [fg, bg, label, px, bold] of pairs) {
  const ratio = contrast(fg, bg);
  const large = px >= 24 || (px >= 18.66 && bold);
  const need = large ? 3.0 : 4.5;
  check(`对比度 ${label} = ${ratio.toFixed(2)}:1（要求 ≥${need}）`, ratio >= need, `fg=${fg} bg=${bg}`);
}

// ---- 6. 浅色背景亮度 ----
const bgM = text.match(/--bg:\s*(#[0-9a-fA-F]{6})/);
let bgOk = false, bgDetail = "";
if (bgM) {
  const L = lum(bgM[1]);
  bgOk = L > 0.85;
  bgDetail = `L=${L.toFixed(4)} (${bgM[1]})`;
}
check("页面背景足够浅（>0.85）", bgOk, bgDetail);
check("color-scheme: light 声明", /color-scheme["']?\s*[:=]\s*["']?light/i.test(text));

// ---- 汇总 ----
lines.unshift(
  "交叉验证（Node.js v" + process.version + " / V8 独立运行时独立实现，含校验逻辑动态执行）",
  `目标文件: ${htmlPath}`,
  `检查项: ${pass + fail} | PASS: ${pass} | FAIL: ${fail}`
);
lines.push(fail > 0 ? "RESULT: FAIL" : "RESULT: ALL GREEN");
fs.writeFileSync(outPath, lines.join("\n"), "utf8");
console.log(lines.join("\n"));
process.exit(fail > 0 ? 1 : 0);
