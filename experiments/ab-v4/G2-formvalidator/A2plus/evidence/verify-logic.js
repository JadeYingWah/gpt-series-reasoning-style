'use strict';
/*
 * G2/A2+ 路径2：逻辑级测试电池（Node 提取式）
 * 原理：从交付的 index.html 中提取真实校验函数源码（markers 之间），在 Node 中求值后跑边界电池。
 * 另含变异测试（5 个内存变异体），验证电池本身有鉴别力（kill rate 必须为 5/5）。
 * 用法：node verify-logic.js [path/to/index.html]（默认 ../index.html）
 */
const fs = require('fs');
const path = require('path');

const htmlPath = process.argv[2] || path.join(__dirname, '..', 'index.html');
const html = fs.readFileSync(htmlPath, 'utf8');
let exitCode = 0;

function report(ok, tag, detail) {
  if (!ok) exitCode = 1;
  console.log((ok ? '[PASS] ' : '[FAIL] ') + tag + (detail ? ' — ' + detail : ''));
}

/* ---------- Part A: 静态结构检查 ---------- */
console.log('== Part A 静态结构 ==');
report(!/https?:\/\//i.test(html), 'A1 无外部 http(s) 引用');
report(/novalidate/.test(html), 'A2 表单含 novalidate（校验由 JS 接管）');
report(/id="email"/.test(html) && /id="phone"/.test(html) && /id="password"/.test(html), 'A3 三字段齐全');
report(/aria-live/.test(html) && /aria-describedby/.test(html), 'A4 aria 状态同步存在');
report(/addEventListener\('blur'/.test(html), 'A5 失焦校验绑定');
report(/addEventListener\('submit'/.test(html) && /preventDefault/.test(html), 'A6 提交拦截 + preventDefault');
report(/VALIDATORS-BEGIN/.test(html) && /VALIDATORS-END/.test(html), 'A7 校验器提取标记存在');

/* ---------- 提取真实校验函数 ---------- */
const m = html.match(/\/\*==VALIDATORS-BEGIN==\*\/([\s\S]*?)\/\*==VALIDATORS-END==\*\//);
if (!m) { console.log('[FAIL] 提取校验器失败'); process.exit(1); }
const src = m[1];

function loadValidators(code) {
  const factory = new Function(code + '\nreturn { validateEmail: validateEmail, validatePhone: validatePhone, validatePassword: validatePassword };');
  return factory();
}

/* ---------- Part B: 边界测试电池 ---------- */
console.log('== Part B 边界测试电池 ==');
const V = loadValidators(src);
const battery = [
  // 邮箱：空值 / 格式错 / 超长 / 特殊字符 / 合法
  { f: 'validateEmail', v: '', ok: false, d: '邮箱-空值' },
  { f: 'validateEmail', v: '   ', ok: false, d: '邮箱-纯空白' },
  { f: 'validateEmail', v: 'plainaddress', ok: false, d: '邮箱-无@格式错' },
  { f: 'validateEmail', v: 'a b@example.com', ok: false, d: '邮箱-含空格特殊字符' },
  { f: 'validateEmail', v: 'a@@b.com', ok: false, d: '邮箱-双@特殊字符' },
  { f: 'validateEmail', v: 'user@domain', ok: false, d: '邮箱-无顶级域' },
  { f: 'validateEmail', v: 'a'.repeat(250) + '@x.com', ok: false, d: '邮箱-超长255字符' },
  { f: 'validateEmail', v: 'user+tag@example.com', ok: true, d: '邮箱-含+号合法' },
  { f: 'validateEmail', v: 'user.name@example.cn', ok: true, d: '邮箱-含点合法' },
  { f: 'validateEmail', v: 'a'.repeat(240) + '@x.com', ok: true, d: '邮箱-247字符合法' },
  // 手机号：空值 / 格式错 / 超长 / 特殊字符 / 合法
  { f: 'validatePhone', v: '', ok: false, d: '手机号-空值' },
  { f: 'validatePhone', v: '   ', ok: false, d: '手机号-纯空白' },
  { f: 'validatePhone', v: '1380013800', ok: false, d: '手机号-10位不足' },
  { f: 'validatePhone', v: '138001380001', ok: false, d: '手机号-12位超长' },
  { f: 'validatePhone', v: '1380013800a', ok: false, d: '手机号-含字母特殊字符' },
  { f: 'validatePhone', v: '138 0013 8000', ok: false, d: '手机号-含空格特殊字符' },
  { f: 'validatePhone', v: '+8613800138000', ok: false, d: '手机号-含+号特殊字符' },
  { f: 'validatePhone', v: '10800138000', ok: false, d: '手机号-第2位为0格式错' },
  { f: 'validatePhone', v: '23800138000', ok: false, d: '手机号-不以1开头' },
  { f: 'validatePhone', v: '13800138000', ok: true, d: '手机号-合法13x' },
  { f: 'validatePhone', v: '19800138000', ok: true, d: '手机号-合法19x' },
  // 密码：空值 / 太短 / 缺字母 / 缺数字 / 超长 / 特殊字符合法 / 合法
  { f: 'validatePassword', v: '', ok: false, d: '密码-空值' },
  { f: 'validatePassword', v: '        ', ok: false, d: '密码-8空格(无字母数字)' },
  { f: 'validatePassword', v: 'ab1', ok: false, d: '密码-3位太短' },
  { f: 'validatePassword', v: 'a7xxxxx', ok: false, d: '密码-7位边界' },
  { f: 'validatePassword', v: 'abcdefgh', ok: false, d: '密码-缺数字' },
  { f: 'validatePassword', v: '12345678', ok: false, d: '密码-缺字母' },
  { f: 'validatePassword', v: 'a1' + 'x'.repeat(63), ok: false, d: '密码-65字符超长' },
  { f: 'validatePassword', v: 'a7xxxxxx', ok: true, d: '密码-8位边界合法' },
  { f: 'validatePassword', v: 'abc12345!@#', ok: true, d: '密码-含特殊字符合法' },
  { f: 'validatePassword', v: 'a1' + 'x'.repeat(62), ok: true, d: '密码-64字符边界合法' }
];
let passB = 0;
battery.forEach(function (c) {
  const r = V[c.f](c.v);
  const ok = r.ok === c.ok;
  if (ok) passB++;
  report(ok, c.d, '期望' + (c.ok ? '通过' : '拒绝') + '，实际' + (r.ok ? '通过' : '拒绝：' + r.msg));
});
report(passB === battery.length, 'B 汇总 ' + passB + '/' + battery.length);

/* ---------- Part C: 变异测试（电池鉴别力） ---------- */
console.log('== Part C 变异测试 ==');
const mutations = [
  { tag: 'M1 手机号正则放宽为 /^\\d{11}$/', from: '/^1[3-9]\\d{9}$/', to: '/^\\d{11}$/' },
  { tag: 'M2 密码最短 8 降为 6', from: 'v.length < 8', to: 'v.length < 6' },
  { tag: 'M3 邮箱超长检查 254 放宽为 9999', from: 'v.length > 254', to: 'v.length > 9999' },
  { tag: 'M4 邮箱正则去掉顶级域要求', from: '/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/', to: '/^[^\\s@]+@[^\\s@]+$/' },
  { tag: 'M5 密码缺字母检查被移除', from: 'if (!/[A-Za-z]/.test(v))', to: 'if (false)' }
];
let killed = 0;
mutations.forEach(function (mu) {
  if (!src.includes(mu.from)) { report(false, mu.tag, '变异源串未找到，无法注入'); return; }
  const mutant = loadValidators(src.replace(mu.from, mu.to));
  let caught = false;
  battery.forEach(function (c) {
    if (caught) return;
    let r;
    try { r = mutant[c.f](c.v); } catch (e) { caught = true; return; }
    if (r.ok !== c.ok) caught = true;
  });
  if (caught) killed++;
  report(caught, mu.tag, caught ? '被电池捕获（RED）' : '未被捕获（电池失效）');
});
report(killed === mutations.length, 'C 汇总 kill rate ' + killed + '/' + mutations.length);

console.log('== 结论 ==');
console.log(exitCode === 0 ? 'ALL GREEN：结构检查、边界电池、变异鉴别力全部通过' : '存在 FAIL 项，见上方标记');
process.exit(exitCode);
