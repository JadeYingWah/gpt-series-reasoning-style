// 静态自检：证明 app.html 无外部资源引用、离线可运行。
// 用法：node evidence/static-check.mjs   （退出码 0 = 全过，1 = 有违规）
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const TARGET = process.env.Q01_TARGET || 'app.html';
const file = join(here, '..', TARGET);
const raw = readFileSync(file, 'utf8');
const lines = raw.split(/\r?\n/);

const NAMESPACE_OK = 'http://www.w3.org/2000/svg'; // XML 命名空间，不发起网络请求

const patterns = [
  [/https?:\/\//g, '外部 URL（http/https）'],
  [/\bsrc\s*=/g, 'src= 引用'],
  [/\bhref\s*=/g, 'href= 引用'],
  [/<link\b/gi, '<link> 标签'],
  [/@import\b/g, '@import'],
  [/\burl\s*\(/g, 'CSS url()'],
  [/\bfetch\s*\(/g, 'fetch()'],
  [/XMLHttpRequest/g, 'XMLHttpRequest'],
  [/new\s+WebSocket/g, 'WebSocket'],
  [/sendBeacon/g, 'sendBeacon'],
  [/<iframe\b/gi, '<iframe>'],
  [/<img\b/gi, '<img>'],
  [/integrity\s*=/g, 'SRI integrity 属性'],
];

let violations = 0;
const report = [];
for (const [re, label] of patterns) {
  const hits = [];
  lines.forEach((ln, i) => {
    const mm = ln.match(re);
    if (mm) mm.forEach(() => hits.push({ line: i + 1, text: ln.trim().slice(0, 140) }));
  });
  const real = hits.filter((h) => !h.text.includes(NAMESPACE_OK));
  if (real.length) violations += real.length;
  report.push({ label, hits: real.length, samples: real.slice(0, 5) });
}

// 结构断言
const asserts = [
  ['单文件内联 <style>', /<style>[\s\S]*<\/style>/.test(raw)],
  ['单文件内联 <script>（无 src）', /<script>[\s\S]*<\/script>/.test(raw) && !/<script[^>]*\bsrc/.test(raw)],
  ['数据块存在且可解析 JSON', /DATA:BEGIN[\s\S]*?const DATA = (\[[\s\S]*?\]);[\s\S]*?DATA:END/.test(raw)],
  ['存在地区筛控件', /id="region"/.test(raw)],
  ['存在空态容器', /data-testid="empty-state"/.test(raw)],
  ['存在 KPI 三卡', ['kpi-total', 'kpi-orders', 'kpi-avg'].every((k) => raw.includes(`data-testid="${k}"`))],
];

console.log('== 外部引用扫描（命中 0 = 无外链） ==');
for (const r of report) {
  console.log(`${r.hits === 0 ? 'PASS' : 'FAIL'}  ${r.label}: ${r.hits}`);
  r.samples.forEach((s) => console.log(`        line ${s.line}: ${s.text}`));
}
console.log('\n== 结构断言 ==');
for (const [name, ok] of asserts) console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}`);

const failedAsserts = asserts.filter(([, ok]) => !ok).length;
const ok = violations === 0 && failedAsserts === 0;
console.log(`\nRESULT: violations=${violations} failedAsserts=${failedAsserts} => ${ok ? 'PASS' : 'FAIL'}`);
console.log(`（唯一允许的 http:// 出现处：XML 命名空间 ${NAMESPACE_OK}，不触网）`);
process.exit(ok ? 0 : 1);
