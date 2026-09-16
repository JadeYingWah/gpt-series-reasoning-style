/**
 * app.html 核心逻辑复算验证
 * 做法：从 app.html 正文中按标记原样提取 CORE-LOGIC 块，在 node vm 中执行，
 *       对「交付文件里真实运行的那段代码」跑断言——不是复制一份逻辑另测。
 * 运行：node verify/core-tests.mjs
 * 产出：verify/core-tests.log
 */
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const APP = path.join(__dirname, '..', 'app.html');
const html = fs.readFileSync(APP, 'utf8');

const lines = [];
let nPass = 0, nFail = 0;
const out = (s) => lines.push(s);

/* ---------- 1. 提取 core 逻辑 ---------- */
const LOG = path.join(__dirname, 'core-tests.log');
const START_TOK = 'CORE-LOGIC-START';
const END_TOK = 'CORE-LOGIC-END';
const iStart = html.indexOf(START_TOK), iEnd = html.indexOf(END_TOK);
if (iStart < 0 || iEnd < 0 || iEnd < iStart) {
  fs.writeFileSync(LOG, 'FATAL: app.html 未找到 CORE-LOGIC 标记\n', 'utf8');
  process.exit(2);
}
let coreSrc = html.slice(iStart + START_TOK.length, iEnd);
const iIife = coreSrc.indexOf('(function (root)');
if (iIife < 0) {
  fs.writeFileSync(LOG, 'FATAL: core 块内未找到 IIFE 起点\n', 'utf8');
  process.exit(2);
}
coreSrc = coreSrc.slice(iIife);
const iTailComment = coreSrc.lastIndexOf('/*');
if (iTailComment >= 0) coreSrc = coreSrc.slice(0, iTailComment);
coreSrc = coreSrc.replace(/\s+$/, '\n');

const coreLines = coreSrc.split('\n').length;
out(`source     : ${APP}`);
out(`core block : 提取成功，${coreLines} 行，${coreSrc.length} 字符（原文未改写）`);
out(`core head  : ${JSON.stringify(coreSrc.slice(0, 60))}`);
out(`core tail  : ${JSON.stringify(coreSrc.slice(-30))}`);
fs.writeFileSync(path.join(__dirname, 'core-extracted.js'), coreSrc, 'utf8');

function loadCore(src) {
  const sandbox = {};
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox, { filename: 'core-from-app.html' });
  if (!sandbox.UnitCore) throw new Error('UnitCore 未挂载');
  return sandbox.UnitCore;
}
let C;
try {
  C = loadCore(coreSrc);
} catch (e) {
  out('');
  out('FATAL: core 块加载失败 -> ' + e.message);
  out('core head: ' + JSON.stringify(coreSrc.slice(0, 120)));
  fs.writeFileSync(LOG, lines.join('\n') + '\n', 'utf8');
  process.exit(2);
}
/* ---------- 2. 断言框架 ---------- */
function check(name, ok, detail) {
  if (ok) { nPass++; out(`[PASS] ${name}`); }
  else { nFail++; out(`[FAIL] ${name}  ->  ${detail}`); }
}
const near = (a, b, eps = 1e-9) => typeof a === 'number' && Number.isFinite(a) && Math.abs(a - b) <= eps;
/* 小数的「有效位数」：小数点后去掉前导零剩下的位数
   "0.33333333" -> 8 ; "0.00000453595" -> 6 ; "123456000"（整数）-> 0 */
function fracSig(s) {
  if (typeof s !== 'string' || /e/i.test(s)) return null; // 科学计数法另算
  const fp = s.split('.')[1];
  if (!fp) return 0;
  return fp.replace(/^0+/, '').length;
}
function eqNum(name, got, want, eps) {
  check(name, near(got, want, eps === undefined ? Math.max(1e-9, Math.abs(want) * 1e-12) : eps),
        `期望 ${want}，实际 ${got}`);
}

/* ---------- 3. 长度 ---------- */
out('');
out('== 长度（基准：米）==');
eqNum('1 m -> cm', C.convertRaw('length', 'm', 'cm', 1), 100);
eqNum('1 m -> mm', C.convertRaw('length', 'm', 'mm', 1), 1000);
eqNum('1 km -> m', C.convertRaw('length', 'km', 'm', 1), 1000);
eqNum('1 in -> cm', C.convertRaw('length', 'in', 'cm', 1), 2.54);
eqNum('1 ft -> m', C.convertRaw('length', 'ft', 'm', 1), 0.3048);
eqNum('1 ft -> in', C.convertRaw('length', 'ft', 'in', 1), 12);
eqNum('1 mi -> km', C.convertRaw('length', 'mi', 'km', 1), 1.609344);
eqNum('1 mi -> m', C.convertRaw('length', 'mi', 'm', 1), 1609.344);
eqNum('0 m -> km（零边界）', C.convertRaw('length', 'm', 'km', 0), 0);
eqNum('100 cm -> m', C.convertRaw('length', 'cm', 'm', 100), 1);
eqNum('0.001 m -> mm', C.convertRaw('length', 'm', 'mm', 0.001), 1);
eqNum('2.5 km -> mi', C.convertRaw('length', 'km', 'mi', 2.5), 1.5534279805933, 1e-6);

/* ---------- 4. 重量 ---------- */
out('');
out('== 重量（基准：千克）==');
eqNum('1 kg -> g', C.convertRaw('weight', 'kg', 'g', 1), 1000);
eqNum('1 g -> mg', C.convertRaw('weight', 'g', 'mg', 1), 1000);
eqNum('1 t -> kg', C.convertRaw('weight', 't', 'kg', 1), 1000);
eqNum('1 lb -> g', C.convertRaw('weight', 'lb', 'g', 1), 453.59237);
eqNum('1 oz -> g', C.convertRaw('weight', 'oz', 'g', 1), 28.349523125);
eqNum('16 oz -> lb', C.convertRaw('weight', 'oz', 'lb', 16), 1);
eqNum('0 kg -> lb（零边界）', C.convertRaw('weight', 'kg', 'lb', 0), 0);
eqNum('1 lb -> oz', C.convertRaw('weight', 'lb', 'oz', 1), 16);

/* ---------- 5. 温度 ---------- */
out('');
out('== 温度（摄氏 / 华氏 / 开尔文）==');
eqNum('0 °C -> °F', C.convertRaw('temp', 'c', 'f', 0), 32);
eqNum('100 °C -> °F', C.convertRaw('temp', 'c', 'f', 100), 212);
eqNum('37 °C -> °F', C.convertRaw('temp', 'c', 'f', 37), 98.6);
eqNum('-40 °C -> °F（负值）', C.convertRaw('temp', 'c', 'f', -40), -40);
eqNum('0 °C -> K', C.convertRaw('temp', 'c', 'k', 0), 273.15);
eqNum('-273.15 °C -> K（绝对零度）', C.convertRaw('temp', 'c', 'k', -273.15), 0);
eqNum('0 K -> °C', C.convertRaw('temp', 'k', 'c', 0), -273.15);
eqNum('0 K -> °F', C.convertRaw('temp', 'k', 'f', 0), -459.67);
eqNum('273.15 K -> °C', C.convertRaw('temp', 'k', 'c', 273.15), 0);
eqNum('32 °F -> °C', C.convertRaw('temp', 'f', 'c', 32), 0);
eqNum('212 °F -> °C', C.convertRaw('temp', 'f', 'c', 212), 100);
eqNum('98.6 °F -> °C', C.convertRaw('temp', 'f', 'c', 98.6), 37, 1e-9);
eqNum('0 °F -> °C（负值区）', C.convertRaw('temp', 'f', 'c', 0), -17.77777777777778, 1e-9);
eqNum('绝对零度 °F', C.toCelsius('f', -459.67), -273.15, 1e-9);

/* ---------- 6. 同单位恒等 ---------- */
out('');
out('== 同单位恒等（全类别全单位）==');
let identBad = [];
for (const cat of Object.keys(C.CATEGORIES)) {
  for (const u of C.CATEGORIES[cat].units) {
    const v = C.convertRaw(cat, u.id, u.id, 7.25);
    if (!near(v, 7.25, 1e-9)) identBad.push(`${cat}/${u.id}=${v}`);
  }
}
check('所有 unit x -> x 恒等', identBad.length === 0, identBad.join(', '));

/* ---------- 7. 输入校验（非法输入不崩） ---------- */
out('');
out('== 输入校验：status / level ==');
const E = (cat, from, raw) => C.evaluate(cat, from, raw);
function checkStatus(name, r, status, level) {
  check(name, r.status === status && (level === undefined || r.level === level),
        `期望 ${status}/${level}，实际 ${r.status}/${r.level}，msg="${r.message}"`);
}
checkStatus('空串 -> empty', E('length', 'm', ''), 'empty', 'hint');
checkStatus('纯空格 -> empty', E('length', 'm', '   '), 'empty', 'hint');
checkStatus('null -> empty', E('length', 'm', null), 'empty');
checkStatus('undefined -> empty', E('length', 'm', undefined), 'empty');
checkStatus('字母 abc -> invalid', E('length', 'm', 'abc'), 'invalid', 'error');
checkStatus('半数字 1a -> invalid', E('length', 'm', '1a'), 'invalid', 'error');
checkStatus('千分位 1,000 -> invalid', E('length', 'm', '1,000'), 'invalid', 'error');
checkStatus('单独小数点 . -> invalid', E('length', 'm', '.'), 'invalid', 'error');
checkStatus('多个小数点 1.2.3 -> invalid', E('length', 'm', '1.2.3'), 'invalid', 'error');
checkStatus('Infinity -> invalid', E('length', 'm', 'Infinity'), 'invalid', 'error');
checkStatus('NaN 文本 -> invalid', E('length', 'm', 'NaN'), 'invalid', 'error');
checkStatus('溢出 1e999 -> invalid', E('length', 'm', '1e999'), 'invalid', 'error');
checkStatus('中文数字 三 -> invalid', E('length', 'm', '三'), 'invalid', 'error');
checkStatus('负数长度 -> invalid', E('length', 'm', '-5'), 'invalid', 'error');
checkStatus('负数重量 -> invalid', E('weight', 'kg', '-5'), 'invalid', 'error');
checkStatus('负零长度 -0 -> ok', E('length', 'm', '-0'), 'ok');
checkStatus('零长度 0 -> ok', E('length', 'm', '0'), 'ok');
checkStatus('负数温度 -> ok（允许）', E('temp', 'c', '-40'), 'ok');
checkStatus('负华氏 -> ok', E('temp', 'f', '-100'), 'ok');
checkStatus('负数绝对零度以下 -> warn 不阻断', E('temp', 'c', '-300'), 'ok', 'warn');
checkStatus('负开尔文 -> warn 不阻断', E('temp', 'k', '-5'), 'ok', 'warn');
checkStatus('边界 0 K -> ok', E('temp', 'k', '0'), 'ok');
checkStatus('科学计数 1e3 -> ok', E('length', 'm', '1e3'), 'ok');
checkStatus('带符号 +5 -> ok', E('length', 'm', '+5'), 'ok');
checkStatus('首尾空格 " 5 " -> ok', E('length', 'm', ' 5 '), 'ok');
checkStatus('尾点 "5." -> ok', E('length', 'm', '5.'), 'ok');
checkStatus('前导点 ".5" -> ok', E('length', 'm', '.5'), 'ok');
checkStatus('前导零 "007" -> ok', E('length', 'm', '007'), 'ok');
checkStatus('未知类别 -> invalid', E('nope', 'm', '1'), 'invalid', 'error');
check('1e3 取值正确', E('length', 'm', '1e3').value === 1000, 'value=' + E('length', 'm', '1e3').value);
check('+5 取值正确', E('length', 'm', '+5').value === 5, 'value=' + E('length', 'm', '+5').value);
check('".5" 取值正确', E('length', 'm', '.5').value === 0.5, 'value=' + E('length', 'm', '.5').value);
check('"007" 取值正确', E('length', 'm', '007').value === 7, 'value=' + E('length', 'm', '007').value);

out('');
out('== 超长文本 / 非字符串输入 ==');
const long60 = '1'.repeat(60);
const long61 = '1'.repeat(61);
const long300 = '9'.repeat(300);
checkStatus('60 字符 -> ok（上限内）', E('length', 'm', long60), 'ok');
checkStatus('61 字符 -> invalid', E('length', 'm', long61), 'invalid', 'error');
checkStatus('300 字符纯数字 -> invalid 不崩', E('length', 'm', long300), 'invalid', 'error');
check('300 字符 alpha -> invalid', E('length', 'm', 'x'.repeat(300)).status === 'invalid',
      'status=' + E('length', 'm', 'x'.repeat(300)).status);
check('300 字符提示做了截断', E('length', 'm', long300).message.length < 200,
      'msg len=' + E('length', 'm', long300).message.length);
check('非法输入 message 非空', E('length', 'm', 'abc').message.length > 0, 'message 为空');
check('对象输入不崩', (() => { try { C.evaluate('length', 'm', { a: 1 }); return true; } catch (e) { return false; } })(), 'threw');
check('数组输入不崩', (() => { try { C.evaluate('length', 'm', [1, 2]); return true; } catch (e) { return false; } })(), 'threw');

out('');
out('== 提示信息的「原因」是否指向正确（不只是「有报错」）==');
check('字母输入提示「不是有效数字」', E('length', 'm', 'abc').message.indexOf('不是有效数字') >= 0,
      E('length', 'm', 'abc').message);
check('混杂 12abc 提示「不是有效数字」', E('length', 'm', '12abc').message.indexOf('不是有效数字') >= 0,
      E('length', 'm', '12abc').message);
check('溢出 1e999 提示「超出可计算范围」', E('length', 'm', '1e999').message.indexOf('超出可计算范围') >= 0,
      E('length', 'm', '1e999').message);
check('超长输入提示「过长」', E('length', 'm', long300).message.indexOf('过长') >= 0,
      E('length', 'm', long300).message);
check('负长度提示「不能为负值」', E('length', 'm', '-5').message.indexOf('不能为负值') >= 0,
      E('length', 'm', '-5').message);
check('负重量提示「不能为负值」', E('weight', 'kg', '-5').message.indexOf('不能为负值') >= 0,
      E('weight', 'kg', '-5').message);
check('低于绝对零度提示提及「绝对零度」', E('temp', 'c', '-300').message.indexOf('绝对零度') >= 0,
      E('temp', 'c', '-300').message);
check('空输入提示引导输入而非报错', E('length', 'm', '').message.indexOf('请输入') >= 0,
      E('length', 'm', '').message);
check('非法输入提示里回显了被拒内容', E('length', 'm', 'abc').message.indexOf('abc') >= 0,
      E('length', 'm', 'abc').message);

/* ---------- 8. 模糊测试：随机输入不得抛异常 ---------- */
out('');
out('== 模糊测试 ==');
let fuzzThrow = 0, fuzzOk = 0, fuzzNonOk = 0;
let seed = 20260912;
const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
const alphabet = '0123456789.eE+-  abc汉字%$#';
const randInt = (n) => Math.floor(rnd() * n);
/* 一半样本刻意构造成「可能合法的数字」：纯随机串几乎全被拦截，ok 分支等于没测到 */
function genSample() {
  if (rnd() < 0.5) {
    let s = rnd() < 0.25 ? (rnd() < 0.5 ? '-' : '+') : '';
    s += '0123456789'.slice(0, 1 + randInt(9));
    if (rnd() < 0.5) s += '.' + '0123456789'.slice(0, randInt(9));
    if (rnd() < 0.3) s += 'e' + (rnd() < 0.5 ? '-' : '') + '0123456789'.slice(0, 1 + randInt(3));
    return s;
  }
  let s = '';
  const len = randInt(40);
  for (let j = 0; j < len; j++) s += alphabet[randInt(alphabet.length)];
  return s;
}
const cats = Object.keys(C.CATEGORIES);
const unitsOf = (cat) => C.CATEGORIES[cat].units.map((u) => u.id);
for (let i = 0; i < 5000; i++) {
  const s = genSample();
  const cat = cats[randInt(cats.length)];
  const us = unitsOf(cat);
  const from = us[randInt(us.length)];
  const to = us[randInt(us.length)];
  try {
    const r = C.evaluate(cat, from, s);
    if (r.status === 'ok') {
      const v = C.convertRaw(cat, from, to, r.value);
      const f = C.formatValue(v);
      if (typeof f !== 'string' || ['undefined', 'null', 'NaN'].indexOf(f) >= 0) throw new Error('bad format: ' + f);
      const nSig = fracSig(f);
      if (nSig !== null && nSig > 8) throw new Error('小数有效位 ' + nSig + ' 位: ' + f);
      fuzzOk++;
    } else {
      if (typeof r.message !== 'string' || r.message.length === 0) throw new Error('empty message');
      fuzzNonOk++;
    }
  } catch (e) {
    fuzzThrow++;
    if (fuzzThrow <= 3) out(`  fuzz-throw 输入="${JSON.stringify(s)}" cat=${cat} ${from}->${to} : ${e.message}`);
  }
}
out(`  5000 组随机输入：可算 ${fuzzOk} / 已拦截 ${fuzzNonOk} / 抛异常 ${fuzzThrow}`);
check('模糊测试零未捕获异常', fuzzThrow === 0, `${fuzzThrow} 次抛异常`);
check('模糊测试 ok 分支被充分覆盖（非空转）', fuzzOk > 500, `fuzzOk=${fuzzOk}`);
check('模糊测试拦截分支被充分覆盖（非空转）', fuzzNonOk > 500, `fuzzNonOk=${fuzzNonOk}`);

/* ---------- 9. formatValue 精度 ---------- */
out('');
out('== 精度 / 格式化（无意义长小数）==');
check('formatValue(0) === "0"', C.formatValue(0) === '0', C.formatValue(0));
check('formatValue(-0) === "0"', C.formatValue(-0) === '0', C.formatValue(-0));
check('formatValue(0.1+0.2) === "0.3"', C.formatValue(0.1 + 0.2) === '0.3', C.formatValue(0.1 + 0.2));
check('formatValue(2.5400000000000005) === "2.54"',
      C.formatValue(2.5400000000000005) === '2.54', C.formatValue(2.5400000000000005));
check('formatValue(NaN) === "—"', C.formatValue(NaN) === '—', C.formatValue(NaN));
check('formatValue(Infinity) === "—"', C.formatValue(Infinity) === '—', C.formatValue(Infinity));
check('formatValue(1/3) 小数有效位 <= 8', (() => { const n = fracSig(C.formatValue(1 / 3)); return n !== null && n <= 8; })(),
      `${C.formatValue(1 / 3)} -> ${fracSig(C.formatValue(1 / 3))} 位`);
check('formatValue(1e-7) 用科学计数', /e-7$/.test(C.formatValue(1e-7)), C.formatValue(1e-7));
check('formatValue(1e20) 无长串零', C.formatValue(1e20).length <= 8, C.formatValue(1e20));
out(`  样例：1/3 -> ${C.formatValue(1 / 3)} ; 0.1+0.2 -> ${C.formatValue(0.1 + 0.2)} ; ` +
    `0.001m->mm -> ${C.formatValue(C.convertRaw('length', 'm', 'mm', 0.001))} ; ` +
    `1in->cm -> ${C.formatValue(C.convertRaw('length', 'in', 'cm', 1))} ; ` +
    `1mi->km -> ${C.formatValue(C.convertRaw('length', 'mi', 'km', 1))} ; ` +
    `1kg->lb -> ${C.formatValue(C.convertRaw('weight', 'kg', 'lb', 1))} ; ` +
    `37C->F -> ${C.formatValue(C.convertRaw('temp', 'c', 'f', 37))}`);
check('格式化的 1/3 无浮点长尾', !/\d{10,}/.test(C.formatValue(1 / 3)), C.formatValue(1 / 3));
check('格式化结果小数有效位 <= 8（抽查 300 例）', (() => {
  let bad = 0, worst = '';
  for (let i = 1; i <= 300; i++) {
    const s = C.formatValue(C.convertRaw('length', 'mm', 'mi', i * 7 + 0.3));
    const n = fracSig(s);
    if (n !== null && n > 8) { bad++; worst = s; }
  }
  if (bad) out(`  超长样例：${worst}`);
  return bad === 0;
})(), '存在超过 8 位的小数尾数');

/* ---------- 10. 静态检查：单文件 / 离线 ---------- */
out('');
out('== 静态检查：单文件·离线·键盘可达 ==');
const forbidden = [
  [/https?:\/\//i, '外部 URL（http/https）'],
  [/\bsrc\s*=\s*["']/i, 'src= 外链'],
  [/<link\b/i, '<link> 外部样式'],
  [/@import/i, 'CSS @import'],
  [/\bfetch\s*\(/, 'fetch('],
  [/XMLHttpRequest/, 'XMLHttpRequest'],
  [/<script[^>]+\bsrc/i, '<script src>'],
  [/<iframe\b/i, '<iframe>'],
  [/<img\b/i, '<img> 外部图片'],
  [/localStorage|sessionStorage/, '存储依赖'],
];
for (const [re, label] of forbidden) {
  check(`不含 ${label}`, !re.test(html), `命中 ${re}`);
}
check('HTTP 头内无 charset 之外的外部引用', !/rel\s*=\s*["']stylesheet/i.test(html), 'stylesheet 引用');
check('样式内联（存在 <style> 块）', /<style>[\s\S]{200,}<\/style>/.test(html), '无内联样式块');
check('脚本内联（存在 <script> 无 src）', /<script>[\s\S]{200,}<\/script>/.test(html), '无内联脚本');

const iTabs = html.indexOf('id="tabs"');
const iInput = html.indexOf('id="valueInput"');
const iFrom = html.indexOf('id="fromUnit"');
const iSwap = html.indexOf('id="swapBtn"');
const iTo = html.indexOf('id="toUnit"');
out(`  源码顺序索引：tabs=${iTabs} input=${iInput} from=${iFrom} swap=${iSwap} to=${iTo}`);
check('Tab 顺序：类别 -> 数值 -> 源单位 -> 交换 -> 目标单位',
      iTabs < iInput && iInput < iFrom && iFrom < iSwap && iSwap < iTo,
      'DOM 顺序不满足');
check('类别切换控件为原生 button（可键盘触发）', /<button type="button" class="tab"/.test(html), '非原生 button');
check('交换按钮为原生 button 且带 aria-label', /<button[^>]*id="swapBtn"[^>]*aria-label=/.test(html), '缺 aria-label');
check('单位选择为原生 select（可键盘操作）',
      /<select id="fromUnit">/.test(html) && /<select id="toUnit">/.test(html), '非原生 select');
check('结果区有 aria-live 播报', /aria-live="polite"/.test(html), '缺 aria-live');
check('输入框 aria-invalid 状态在代码中切换', /setAttribute\('aria-invalid'/.test(html), '未切换 aria-invalid');
check('无「计算」按钮', !/计算\s*<\/button>/.test(html), '存在计算按钮文案');

/* ---------- 11. 变异检验（证明上面的测试有鉴别力）---------- */
out('');
out('== 变异检验：把测试想防的错误做一次，它会不会红 ==');
function runKill(mutatedSrc, label, expectKill) {
  let killed = 0;
  try {
    const M = loadCore(mutatedSrc);
    const cases = [
      ['1 in -> cm 应为 2.54', () => near(M.convertRaw('length', 'in', 'cm', 1), 2.54)],
      ['1 ft -> m 应为 0.3048', () => near(M.convertRaw('length', 'ft', 'm', 1), 0.3048)],
      ['1 mi -> km 应为 1.609344', () => near(M.convertRaw('length', 'mi', 'km', 1), 1.609344)],
      ['0°C -> 32°F', () => near(M.convertRaw('temp', 'c', 'f', 0), 32)],
      ['100°C -> 212°F', () => near(M.convertRaw('temp', 'c', 'f', 100), 212)],
      ['32°F -> 0°C', () => near(M.convertRaw('temp', 'f', 'c', 32), 0)],
      ['212°F -> 100°C', () => near(M.convertRaw('temp', 'f', 'c', 212), 100)],
      ['98.6°F -> 37°C', () => near(M.convertRaw('temp', 'f', 'c', 98.6), 37, 1e-9)],
      ['0°F -> -17.7778°C', () => near(M.convertRaw('temp', 'f', 'c', 0), -17.77777777777778, 1e-9)],
      ['-273.15°C -> 0K', () => near(M.convertRaw('temp', 'c', 'k', -273.15), 0)],
      ['0K -> -459.67°F', () => near(M.convertRaw('temp', 'k', 'f', 0), -459.67)],
      ['1 kg -> 1000 g', () => near(M.convertRaw('weight', 'kg', 'g', 1), 1000)],
      ['1 t -> 1000 kg', () => near(M.convertRaw('weight', 't', 'kg', 1), 1000)],
      ['abc 应被拦截', () => M.evaluate('length', 'm', 'abc').status === 'invalid'],
      ['abc 提示应为「不是有效数字」', () => M.evaluate('length', 'm', 'abc').message.indexOf('不是有效数字') >= 0],
      ['12abc 提示应为「不是有效数字」', () => M.evaluate('length', 'm', '12abc').message.indexOf('不是有效数字') >= 0],
      ['空串应被识别为空', () => M.evaluate('length', 'm', '').status === 'empty'],
      ['-5 长度应被拒绝', () => M.evaluate('length', 'm', '-5').status === 'invalid'],
      ['-5 重量应被拒绝', () => M.evaluate('weight', 'kg', '-5').status === 'invalid'],
      ['-40°C 应允许', () => M.evaluate('temp', 'c', '-40').status === 'ok'],
      ['-300°C 应给出 warn 提示', () => M.evaluate('temp', 'c', '-300').level === 'warn'],
      ['-300°C 提示应提及绝对零度', () => M.evaluate('temp', 'c', '-300').message.indexOf('绝对零度') >= 0],
      ['300 字符应被拦截', () => M.evaluate('length', 'm', '9'.repeat(300)).status === 'invalid'],
      ['300 字符提示应含「过长」', () => M.evaluate('length', 'm', '9'.repeat(300)).message.indexOf('过长') >= 0],
      ['0.1+0.2 格式化为 0.3', () => M.formatValue(0.1 + 0.2) === '0.3'],
      ['formatValue(0) 应为 "0"', () => M.formatValue(0) === '0'],
      ['格式化结果小数位数 <= 8', () => { const n = fracSig(M.formatValue(1 / 3)); return n !== null && n <= 8; }],
      ['同单位恒等', () => near(M.convertRaw('length', 'm', 'm', 7.25), 7.25)],
    ];
    for (const [, fn] of cases) { try { if (!fn()) killed++; } catch { killed++; } }
  } catch (e) {
    out(`  [${label}] 变异体加载失败：${e.message}`);
    killed = -1;
  }
  const ok = killed >= expectKill;
  if (ok) nPass++; else nFail++;
  out(`  ${ok ? '[PASS]' : '[FAIL]'} ${label} -> 杀死 ${killed} 项${ok ? '' : `（要求 >= ${expectKill}）`}`);
}
runKill(coreSrc.replace(/factor:\s*0\.0254/, 'factor: 0.0255'), '变异1 英寸系数 0.0254 -> 0.0255', 1);
runKill(coreSrc.replace(/factor:\s*0\.3048/, 'factor: 0.3049'), '变异2 英尺系数 0.3048 -> 0.3049', 1);
runKill(coreSrc.replaceAll('factor: 1000', 'factor: 1001'), '变异3 千米/吨系数 1000 -> 1001（两处）', 2);
runKill(coreSrc.replace('(v - 32) * 5 / 9', '(v - 32) * 9 / 5'), '变异4 华氏转摄氏公式倒置', 2);
runKill(coreSrc.replace('c * 9 / 5 + 32', 'c * 9 / 5 + 30'), '变异5 摄氏转华氏偏移 32 -> 30', 1);
runKill(coreSrc.replace(/var NUM_RE = [^;]+;/, 'var NUM_RE = /^[\\s\\S]*$/;'), '变异6 数字校验正则被放宽为全匹配', 1);
runKill(coreSrc.replaceAll('allowNegative: false', 'allowNegative: true'), '变异7 取消长度/重量负数拦截', 2);
runKill(coreSrc.replace('MAX_INPUT_CHARS = 60', 'MAX_INPUT_CHARS = 100000'), '变异8 取消超长输入上限', 2);
runKill(coreSrc.replace("x === 0) return '0'", "x === 0) return '0.0000000000'"), '变异9 零值格式化引入噪声', 1);
runKill(coreSrc.replace('if (x === 0)', 'if (false)'), '变异10 去掉零值特判', 1);
runKill(coreSrc.replace('* 5 / 9', '* 5 / 9.0000001'), '变异11 华氏转摄氏分母微扰', 1);
runKill(coreSrc.replace('factor: 1609.344', 'factor: 1609.3'), '变异12 英里系数 1609.344 -> 1609.3', 1);
runKill(coreSrc.replace(/return '0';/, "return '';"), '变异13 零值返回空串', 1);
runKill(coreSrc.replace('text.length > MAX_INPUT_CHARS', 'text.length > 100000'), '变异14 超长上限失效（另一种写法）', 1);
runKill(coreSrc.replace('ABS_ZERO_C = -273.15', 'ABS_ZERO_C = -999'), '变异15 绝对零度阈值放宽', 1);

/* ---------- 12. 汇总 ---------- */
out('');
out('============================');
out(`TOTAL ${nPass + nFail}   PASS ${nPass}   FAIL ${nFail}`);
out(nFail === 0 ? 'RESULT: ALL PASS' : 'RESULT: FAILED');
const log = lines.join('\n') + '\n';
fs.writeFileSync(path.join(__dirname, 'core-tests.log'), log, 'utf8');
process.stdout.write(log);
process.exit(nFail === 0 ? 0 : 1);
