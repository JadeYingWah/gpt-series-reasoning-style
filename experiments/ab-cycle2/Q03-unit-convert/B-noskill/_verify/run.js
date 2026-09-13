// 验收脚本：直接从 app.html 抽取已交付的脚本片段并在 node 中执行（非重写实现）
// 抽取范围：从 "var DATA" 到 "/* ---------------- DOM" 之前的纯逻辑段
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'app.html'), 'utf8');
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) throw new Error('未找到内联 script');
const script = m[1];

const start = script.indexOf('var DATA');
const end = script.indexOf('/* ---------------- DOM');
if (start < 0 || end < 0 || end <= start) throw new Error('未定位到纯逻辑段');
const pure = script.slice(start, end);

// 在受控作用域中执行交付代码
const factory = new Function(pure + '\nreturn {DATA, NUM_RE, toCelsius, fromCelsius, convert, findUnit, fmt};');
const L = factory();

let pass = 0, fail = 0;
function eq(actual, expected, label) {
  const ok = String(actual) === String(expected);
  if (ok) { pass++; } else { fail++; console.log('FAIL ' + label + ' => got ' + actual + ', want ' + expected); }
}
function near(actual, expected, tol, label) {
  const ok = Math.abs(actual - expected) <= tol;
  if (ok) { pass++; } else { fail++; console.log('FAIL ' + label + ' => got ' + actual + ', want ~' + expected); }
}

// ---------- 1. 温度公式 ----------
near(L.convert('temperature', 0,   'c', 'f'), 32,        1e-9, 'C->F 0');
near(L.convert('temperature', 100, 'c', 'f'), 212,       1e-9, 'C->F 100');
near(L.convert('temperature', -40, 'c', 'f'), -40,       1e-9, 'C->F -40 交点');
near(L.convert('temperature', 0,   'c', 'k'), 273.15,    1e-9, 'C->K 0 (边界)');
near(L.convert('temperature', -273.15, 'c', 'k'), 0,     1e-9, 'C->K 绝对零度');
near(L.convert('temperature', 32,  'f', 'c'), 0,         1e-9, 'F->C 32');
near(L.convert('temperature', 212, 'f', 'c'), 100,       1e-9, 'F->C 212');
near(L.convert('temperature', -459.67, 'f', 'k'), 0,     1e-9, 'F->K 绝对零度');
near(L.convert('temperature', 0,   'k', 'c'), -273.15,   1e-9, 'K->C 0');
near(L.convert('temperature', 273.15, 'k', 'f'), 32,     1e-9, 'K->F');
near(L.convert('temperature', 0,   'k', 'f'), -459.67,   1e-9, 'K->F 0K');
near(L.convert('temperature', -273.15, 'c', 'f'), -459.67, 1e-9, 'C->F 绝对零度');
// 往返自洽
[-273.15, -40, 0, 37.5, 100].forEach(function (v) {
  near(L.convert('temperature', L.convert('temperature', v, 'c', 'k'), 'k', 'c'), v, 1e-9, 'C->K->C ' + v);
  near(L.convert('temperature', L.convert('temperature', v, 'c', 'f'), 'f', 'c'), v, 1e-9, 'C->F->C ' + v);
});

// ---------- 2. 长度 / 重量 ----------
near(L.convert('length', 1, 'm',  'cm'), 100,        1e-9, '1m=100cm');
near(L.convert('length', 1, 'mi', 'm'),  1609.344,   1e-9, '1mi=1609.344m');
near(L.convert('length', 1, 'in', 'cm'), 2.54,       1e-9, '1in=2.54cm');
near(L.convert('length', 0, 'km', 'mm'), 0,          1e-12, '0 长度');
near(L.convert('weight', 1, 'kg', 'g'),  1000,       1e-9, '1kg=1000g');
near(L.convert('weight', 1, 'lb', 'kg'), 0.45359237, 1e-9, '1lb=0.45359237kg');
near(L.convert('weight', 1, 'oz', 'g'),  28.349523125, 1e-9, '1oz=28.349523125g');
near(L.convert('weight', 0, 't', 'mg'),  0,          1e-12, '0 重量');

// ---------- 3. 非法输入：正则拦截 ----------
[ '', ' ', 'abc', '1a', '--1', '1..2', '1,000', 'Infinity', 'NaN', '0x10',
  '1e', '1/2', '１００', '@#$%', '1.2.3', '+', '-', '.'
].forEach(function (s) {
  const t = s.trim();
  const blocked = t === '' || !L.NUM_RE.test(t);
  if (blocked) pass++; else { fail++; console.log('FAIL 非法输入未被拦截: ' + JSON.stringify(s)); }
});
// 合法输入应通过
['0', '-40', '3.5', '.5', '1e3', '+2', '-0.001'].forEach(function (s) {
  if (L.NUM_RE.test(s)) pass++; else { fail++; console.log('FAIL 合法输入被误拦: ' + JSON.stringify(s)); }
});

// ---------- 4. 格式化：不产生无意义长小数 ----------
eq(L.fmt(0.1 + 0.2), '0.3', '浮点 0.1+0.2');
eq(L.fmt(1 / 3), '0.3333333333', '1/3 限 10 位有效数字');
eq(L.fmt(1), '1', '整数');
eq(L.fmt(-40), '-40', '负数');
eq(L.fmt(2.54), '2.54', '2.54');
eq(L.fmt(1609.344), '1609.344', '1609.344');
eq(L.fmt(0.000001), '0.000001', '1e-6');
eq(L.fmt(1e-9), '1e-9', '1e-9 用科学计数');
eq(L.fmt(1e20), '1e+20', '1e20 用科学计数');
eq(L.fmt(NaN), '—', 'NaN');
eq(L.fmt(Infinity), '—', 'Infinity');
// 长度检查：任何输出都不应超过 12 个字符量级（科学计数法除外）
[1, 2.54, 1 / 3, 0.1 + 0.2, 1e-9].forEach(function (n) {
  const s = L.fmt(n);
  if (s.length <= 14) pass++; else { fail++; console.log('FAIL 格式化过长: ' + s); }
});

// ---------- 5. 溢出 ----------
if (!isFinite(L.convert('length', 1e308, 'km', 'mm'))) pass++;
else { fail++; console.log('FAIL 溢出未被识别'); }

console.log('\nPASS=' + pass + '  FAIL=' + fail);
process.exit(fail ? 1 : 0);
