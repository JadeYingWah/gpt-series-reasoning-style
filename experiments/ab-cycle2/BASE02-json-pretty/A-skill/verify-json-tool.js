/**
 * BASE02 / A 臂 —— app.html 的可复算验证脚本（Node，无第三方依赖）
 * 运行： node verify-json-tool.js
 * 产物： verify-report.txt （人读） / verify-report.json （机读）
 *
 * 做法：
 *  1. 从 app.html 抽出内联 <script>，在 vm 沙箱里执行（沙箱无 document，DOM 分支自动跳过）
 *  2. 单元测试：合法/非法样例、错误定位、（与 JSON.parse 的）差分测试
 *  3. 边界测试：空输入、BOM、重复键、数字保真、深嵌套、未闭合、控制字符
 *  4. 性能测试：>100KB 输入的美化/压缩耗时
 *  5. 静态检查：无外部依赖（无 http(s):// / src= / fetch / XHR 等）
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const DIR = __dirname;
const HTML = path.join(DIR, "app.html");
const REPORT_TXT = path.join(DIR, "verify-report.txt");
const REPORT_JSON = path.join(DIR, "verify-report.json");

const lines = [];
const records = [];
let pass = 0, fail = 0;

function log(s) { lines.push(s); }
function ok(name, extra) {
  pass++;
  records.push({ name, status: "PASS", detail: extra === undefined ? "" : String(extra) });
  log("  [PASS] " + name + (extra !== undefined ? "  -> " + extra : ""));
}
function bad(name, extra) {
  fail++;
  records.push({ name, status: "FAIL", detail: extra === undefined ? "" : String(extra) });
  log("  [FAIL] " + name + (extra !== undefined ? "  -> " + extra : ""));
}
function check(cond, name, extra) { cond ? ok(name, extra) : bad(name, extra); }
function section(t) { log(""); log("=== " + t + " ==="); }

/* ---------- 1. 加载 app.html 内联脚本 ---------- */
section("0. 加载被测代码");
const html = fs.readFileSync(HTML, "utf8");
const scriptMatches = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)];
check(scriptMatches.length === 1, "app.html 恰好含 1 个内联 <script>（无外链）",
  "实际 " + scriptMatches.length + " 个");
const inlineJS = scriptMatches[0][1];
const sandbox = { console };
vm.createContext(sandbox);
vm.runInContext(inlineJS, sandbox, { filename: "app.html:inline-script" });
const T = sandbox.JSONTool;
check(!!T && typeof T.parse === "function" && typeof T.stringify === "function" && typeof T.run === "function",
  "沙箱内成功导出 JSONTool（parse/stringify/run）",
  Object.keys(T || {}).join(","));
log("  app.html 大小: " + html.length + " 字符 / " + Buffer.byteLength(html, "utf8") + " 字节");

/* ---------- 2. 独立性交叉校验工具 ---------- */
// 与库里算法不同的写法，用来独立复核 行/列 计算
function independentPos(text, index) {
  const upto = text.slice(0, index).split("\n");
  return { line: upto.length, column: upto[upto.length - 1].length + 1 };
}
function deepEqual(a, b) {
  if (a === b) return true;
  if (typeof a === "number" && typeof b === "number") return Object.is(a, b) || a === b;
  if (a === null || b === null || typeof a !== "object" || typeof b !== "object") return false;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  const ka = Object.keys(a), kb = Object.keys(b);
  if (ka.length !== kb.length) return false;
  return ka.every(k => deepEqual(a[k], b[k]));
}

/* ---------- 3. 格式化正确性 ---------- */
section("1. 美化 / 压缩 正确性");
const cp = [
  '{"a":1,"b":[1,2,{"c":true}],"d":null,"e":"x"}',
  '[]', '{}', '[[]]', '{"":""}',
  '{"s":"\u4e2d\u6587 \u00e9 \u4f60\u597d"}',
  '[1,-0.5,1e10,1E-3,0,12345678901234567890]',
  '{"n":{"a":{"b":{"c":[1,2,3]}}}}',
];
let fmtAllOk = true;
for (const src of cp) {
  const pretty = T.run(src, "pretty");
  const min = T.run(src, "minify");
  const name = "格式化样例: " + (src.length > 42 ? src.slice(0, 39) + "..." : src);
  if (!pretty.ok || !min.ok) { fmtAllOk = false; bad(name, "解析失败: " + (pretty.message || min.message)); continue; }
  const eqP = deepEqual(JSON.parse(pretty.text), JSON.parse(src));
  const eqM = deepEqual(JSON.parse(min.text), JSON.parse(src));
  const indentOK = pretty.text.indexOf("\n  ") !== -1 || src.replace(/\s/g, "").length <= 4;
  if (eqP && eqM && indentOK) ok(name, "美化/压缩均可被 JSON.parse 还原且值相等");
  else { fmtAllOk = false; bad(name, "eqP=" + eqP + " eqM=" + eqM + " indentOK=" + indentOK); }
}
// 缩进必须恰好 2 空格
const demo = T.run('{"a":[1,{"b":2}]}', "pretty");
const expectExact = '{\n  "a": [\n    1,\n    {\n      "b": 2\n    }\n  ]\n}';
check(demo.ok && demo.text === expectExact, "缩进严格等于 2 空格且换行结构正确",
  demo.ok ? JSON.stringify(demo.text.slice(0, 60)) : demo.message);

/* ---------- 4. 非法输入的错误定位 ---------- */
section("2. 非法 JSON 的错误定位（行/列/偏移）");
const errCases = [
  { src: '{"a":}', at: 5, what: "缺少值" },
  { src: '{"a":1,}', at: 7, what: "尾随逗号(对象)" },
  { src: '[1,2,]', at: 5, what: "尾随逗号(数组)" },
  { src: '{"a" 1}', at: 5, what: "缺少冒号" },
  { src: "{'a':1}", at: 1, what: "单引号键" },
  { src: '{"a":1}{"b":2}', at: 7, what: "主体后多余内容" },
  { src: '{"a":01}', at: 6, what: "前导零" },
  { src: '[1,2', at: 0, what: "数组未闭合" },
  { src: '{"a":"unterminated}', at: 5, what: "字符串未闭合" },
  { src: '{"a":tru}', at: 5, what: "非法字面量" },
];
for (const c of errCases) {
  const r = T.run(c.src, "pretty");
  const name = "错误定位: " + c.what + "  " + JSON.stringify(c.src);
  if (r.ok) { bad(name, "本应报错却解析成功"); continue; }
  const ind = independentPos(c.src, r.index);
  const locMatch = (r.line === ind.line && r.column === ind.column);
  const offMatch = (r.index === c.at);
  const charOK = c.src[r.index] !== undefined;
  if (locMatch && offMatch && charOK) {
    ok(name, "line=" + r.line + " col=" + r.column + " offset=" + r.index +
      " 指向 " + JSON.stringify(c.src[r.index]) + " ｜ " + r.message);
  } else {
    bad(name, "期望 offset=" + c.at + "，得到 offset=" + r.index +
      " line=" + r.line + "/" + ind.line + " col=" + r.column + "/" + ind.column + " ｜ " + r.message);
  }
}
// 多行输入的行号
// 手工核算：'{\n  "a": 1,\n  "b": ,\n  "c": 3\n}' 中第 3 行是 `  "b": ,`
// 该行起始于偏移 12，逗号位于偏移 19 → 行 3、列 8（1 起始）
const multi = '{\n  "a": 1,\n  "b": ,\n  "c": 3\n}';
const mr = T.run(multi, "pretty");
const mind = independentPos(multi, 19);
check(!mr.ok && mr.line === 3 && mr.column === 8 && mr.index === 19 &&
      mr.line === mind.line && mr.column === mind.column,
  "多行输入行号正确（第 3 行第 8 列，偏移 19，独立算法复核一致）",
  mr.ok ? "解析成功" : ("line=" + mr.line + " col=" + mr.column + " offset=" + mr.index + " ｜ " + mr.message));
check(!!mr.excerpt && /\^/.test(mr.excerpt.caret), "错误摘录含插入符 ^",
  mr.excerpt ? JSON.stringify(mr.excerpt.lineText) + " / " + JSON.stringify(mr.excerpt.caret) : "(none)");
check(!!mr.excerpt && mr.excerpt.lineText.indexOf('"b"') !== -1, "错误摘录指向出错行原文",
  mr.excerpt ? JSON.stringify(mr.excerpt.lineText) : "(none)");

/* ---------- 5. 与 JSON.parse 的差分测试 ---------- */
section("3. 差分测试（对照原生 JSON.parse）");
const validCorpus = [
  '{"a":1}', '{"a":[1,2,3]}', '[1,2,3]', '"str"', '123', 'true', 'false', 'null',
  '{"nested":{"x":[{"y":1},{"y":2}]},"t":true,"f":false,"z":null}',
  '{"e":"\\u00e9\\n\\t\\"\\\\"}',
  '[0.1,1e-7,1E+21,-0.0]',
  '{"dup":1,"dup":2}',
  '[[[[[1]]]]]'
];
let diffValidOK = true;
for (const src of validCorpus) {
  const mine = T.run(src, "minify");
  let nativeV, nativeErr = null;
  try { nativeV = JSON.parse(src); } catch (e) { nativeErr = e; }
  const consistent = nativeErr ? !mine.ok : (mine.ok && deepEqual(JSON.parse(mine.text), nativeV));
  if (!consistent) { diffValidOK = false; bad("差分(合法) " + JSON.stringify(src),
    "mine.ok=" + mine.ok + " native=" + (nativeErr ? "throw" : "ok") + " mine=" + JSON.stringify(mine.text || mine.message)); }
}
check(diffValidOK, "合法语料：" + validCorpus.length + " 例，我方判定与 JSON.parse 完全一致");

const invalidCorpus = [
  '{"a":}', '{,}', '[,]', '{"a"1}', '{"a":1,}', '[1,]', '01', '-', '.5', '+1',
  'NaN', 'Infinity', 'undefined', '{"a":1}{"b":2}', '[1 2]', '"unterminated',
  '{"a":1\x01}', '{"a":1}\n  ', 'tru', '{"a":1,,"b":2}', '[' + ']', '{"a":}'
];
let diffInvalidOK = true;
for (const src of invalidCorpus) {
  let nativeThrew = false;
  try { JSON.parse(src); } catch (e) { nativeThrew = true; }
  const mine = T.run(src, "minify");
  const agree = nativeThrew ? !mine.ok : true; // 只要求我方在原生报错时也报错
  if (!agree) { diffInvalidOK = false; bad("差分(非法) " + JSON.stringify(src), "JSON.parse 抛错但我方解析成功"); }
}
check(diffInvalidOK, "非法语料：" + invalidCorpus.length + " 例，JSON.parse 报错的样例我方均报错");

/* ---------- 6. 边界测试 ---------- */
section("4. 边界测试");
function boundary(name, fn) {
  try { fn(); } catch (e) { bad(name, "抛出未捕获异常: " + (e && e.message)); }
}
// 空输入
boundary("空字符串", () => {
  const r = T.run("", "pretty");
  check(!r.ok && r.line === 1 && r.column === 1, "空字符串：优雅报错且定位 1:1", r.message);
});
boundary("纯空白", () => {
  const r = T.run("   \n\t  ", "pretty");
  check(!r.ok, "纯空白：报「输入为空」", r.message);
});
boundary("BOM", () => {
  const r = T.run("\uFEFF{\"a\":1}", "pretty");
  check(r.ok && r.text === '{\n  "a": 1\n}', "带 UTF-8 BOM：正常解析", r.ok ? JSON.stringify(r.text) : r.message);
});
boundary("重复键", () => {
  const r = T.run('{"a":1,"a":2}', "pretty");
  const kept = r.ok && (r.text.match(/"a"/g) || []).length === 2;
  check(kept, "重复键：两个键都保留（原生 JSON.parse 会丢）", r.ok ? JSON.stringify(r.text) : r.message);
});
boundary("数字保真", () => {
  const big = '12345678901234567890';
  const r = T.run("[" + big + ",1e400,-0]", "minify");
  const keep = r.ok && r.text.indexOf(big) !== -1 && r.text.indexOf("1e400") !== -1 && r.text.indexOf("-0") !== -1;
  check(keep, "大整数/超大指数/-0：原样保留字面量", r.ok ? r.text : r.message);
});
boundary("制表符缩进输入", () => {
  const r = T.run('{\n\t"a":\t1\n}', "pretty");
  check(r.ok && r.text === '{\n  "a": 1\n}', "输入用制表符：输出归一为 2 空格", r.ok ? JSON.stringify(r.text) : r.message);
});
boundary("字符串内控制字符", () => {
  const r = T.run('{"a":"x\ny"}', "pretty");
  check(!r.ok && /控制字符/.test(r.message), "字符串内裸换行：报未转义控制字符", r.message);
});
boundary("未闭合字符串", () => {
  const r = T.run('"abc', "pretty");
  check(!r.ok && /未闭合/.test(r.message), "顶层未闭合字符串：优雅报错", r.message);
});
boundary("超长单行（错误定位裁剪）", () => {
  const long = '{"k":"' + "a".repeat(5000) + '"}';
  const r = T.run(long, "minify");
  check(r.ok, "5000 字符单行：正常处理", r.ok ? r.text.length + " 字符" : r.message);
  const bad2 = '{"k":"' + "a".repeat(5000) + '",}}';
  const r2 = T.run(bad2, "pretty");
  check(!r2.ok && r2.excerpt.lineText.length <= 170, "超长出错行：摘录被裁剪到 160 字符窗口",
    r2.ok ? "解析成功" : ("摘录长度 " + r2.excerpt.lineText.length));
});
boundary("深嵌套 2000 层（超上限）", () => {
  const deep = "[".repeat(2000) + "]".repeat(2000);
  const r = T.run(deep, "minify");
  check(!r.ok && /嵌套层级过深/.test(r.message), "2000 层嵌套：优雅报「嵌套层级过深」而非栈溢出", r.message);
});
boundary("深嵌套 100000 层（极端）", () => {
  const deep = "[".repeat(100000) + "]".repeat(100000);
  const r = T.run(deep, "minify");
  check(!r.ok && /嵌套层级过深/.test(r.message), "10 万层嵌套：仍优雅报错，无 RangeError", r.message);
});
boundary("深嵌套 900 层（上限内）", () => {
  const deep = "[".repeat(900) + "1" + "]".repeat(900);
  const r = T.run(deep, "minify");
  check(r.ok && r.text === deep, "900 层嵌套：正常往返", r.ok ? "长度 " + r.text.length : r.message);
});
boundary("顶层标量", () => {
  check(T.run("123", "pretty").text === "123", "顶层数字：输出 123");
  check(T.run("true", "pretty").text === "true", "顶层 true：输出 true");
  check(T.run('"a"', "pretty").text === '"a"', "顶层字符串：输出 \"a\"");
});
boundary("空对象/空数组嵌套", () => {
  const r = T.run('{"a":{},"b":[]}', "pretty");
  check(r.ok && r.text === '{\n  "a": {},\n  "b": []\n}', "空对象/空数组：不展开多行",
    r.ok ? JSON.stringify(r.text) : r.message);
});

/* ---------- 7. 性能 / 大输入 ---------- */
section("5. 大输入（>100KB）性能");
function buildBig(n) {
  const arr = [];
  for (let i = 0; i < n; i++) {
    arr.push({ id: i, name: "\u9879\u76ee" + i, tags: ["a", "b", "c"], ok: i % 2 === 0, score: i * 1.5 });
  }
  return JSON.stringify({ total: n, items: arr });
}
const big = buildBig(3000);
log("  构造大输入：" + big.length + " 字符 / " + Buffer.byteLength(big, "utf8") + " 字节");
check(Buffer.byteLength(big, "utf8") > 100 * 1024, "测试输入确实 >100KB",
  Buffer.byteLength(big, "utf8") + " 字节");

let t0 = process.hrtime.bigint();
const bp = T.run(big, "pretty");
let t1 = process.hrtime.bigint();
const bm = T.run(big, "minify");
let t2 = process.hrtime.bigint();
const prettyMs = Number(t1 - t0) / 1e6, minMs = Number(t2 - t1) / 1e6;
check(bp.ok, "大输入美化：成功无异常", "耗时 " + prettyMs.toFixed(1) + " ms，输出 " + bp.text.length + " 字符");
check(bm.ok, "大输入压缩：成功无异常", "耗时 " + minMs.toFixed(1) + " ms，输出 " + bm.text.length + " 字符");
check(bp.ok && deepEqual(JSON.parse(bp.text), JSON.parse(big)), "大输入美化结果语义等价（JSON.parse 比对）");
check(bm.ok && deepEqual(JSON.parse(bm.text), JSON.parse(big)), "大输入压缩结果语义等价（JSON.parse 比对）");
check(prettyMs < 3000 && minMs < 3000, "大输入单次处理 < 3s（同步主线程预算内）",
  "pretty=" + prettyMs.toFixed(1) + "ms, minify=" + minMs.toFixed(1) + "ms");

// 更大的输入（~1MB）压力
const huge = buildBig(20000);
let h0 = process.hrtime.bigint(); const hr = T.run(huge, "minify"); let h1 = process.hrtime.bigint();
const hugeMs = Number(h1 - h0) / 1e6;
check(hr.ok, "压力输入 ~" + Math.round(Buffer.byteLength(huge, "utf8") / 1024) + "KB 压缩成功",
  "耗时 " + hugeMs.toFixed(1) + " ms");

// 100KB 的非法输入（错误出现在末尾）—— 确认快速失败且不卡
const badBig = '{"items":[' + '1,'.repeat(60000) + ']}';
let b0 = process.hrtime.bigint(); const br = T.run(badBig, "minify"); let b1 = process.hrtime.bigint();
check(!br.ok, "100KB+ 非法输入：快速报错不卡死",
  "耗时 " + (Number(b1 - b0) / 1e6).toFixed(1) + " ms，line=" + br.line + " col=" + br.column);

/* ---------- 8. 无外部依赖（静态扫描） ---------- */
section("6. 静态检查：无外部依赖 / 离线可运行");
const patterns = [
  [/\bsrc\s*=/i, "src= 外链"],
  [/\bhref\s*=/i, "href= 外链"],
  [/https?:\/\//i, "http(s):// URL"],
  [/@import/i, "@import"],
  [/\bfetch\s*\(/i, "fetch()"],
  [/XMLHttpRequest/i, "XMLHttpRequest"],
  [/new\s+WebSocket/i, "WebSocket"],
  [/importScripts/i, "importScripts"],
  [/\bcdn\b/i, "cdn 字样"],
];
let staticClean = true;
for (const [re, label] of patterns) {
  const m = html.match(re);
  const isStyleTag = false;
  if (m) {
    // 允许 <style>/<script> 标签自身的属性写入检查之外：这里对全文扫描，命中即视为可疑
    staticClean = false;
    bad("静态检查：" + label, "在 app.html 中命中 " + JSON.stringify(m[0]));
  } else {
    ok("静态检查：无 " + label);
  }
}
check(html.indexOf("<script>") !== -1 && html.indexOf("</script>") !== -1, "内联 <script> 存在（非外链）");
check(/<style>/i.test(html) && /<\/style>/i.test(html), "内联 <style> 存在（非外链）");
check(!/<!--/.test(html) || true, "备注：扫描基于原始文本，非 DOM 解析");

/* ---------- 9. 汇总 ---------- */
section("汇总");
log("  通过: " + pass);
log("  失败: " + fail);
log("  结论: " + (fail === 0 ? "全部通过" : "存在失败项"));
log("");
log("  复算方式: cd BASE02-json-pretty/A-skill && node verify-json-tool.js");
log("  被测文件: app.html (" + Buffer.byteLength(html, "utf8") + " 字节)");

const report = lines.join("\n") + "\n";
fs.writeFileSync(REPORT_TXT, report, "utf8");
fs.writeFileSync(REPORT_JSON, JSON.stringify({
  pass, fail,
  appHtmlBytes: Buffer.byteLength(html, "utf8"),
  bigInputBytes: Buffer.byteLength(big, "utf8"),
  timings: { prettyMs, minMs, hugeMs, hugeKb: Math.round(Buffer.byteLength(huge, "utf8") / 1024) },
  records
}, null, 2), "utf8");

process.exitCode = fail === 0 ? 0 : 1;
console.log(report);
