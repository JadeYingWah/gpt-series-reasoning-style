/* selftest.js —— 从 app.html 抽出 #core 纯计算脚本，在 Node 中复算并断言。
 * 运行：node selftest.js   （输出同时打印并写入 selftest-output.txt）
 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const OUT = [];
function log(s) { OUT.push(s); }

function done() {
  const text = OUT.join('\n') + '\n';
  fs.writeFileSync(path.join(__dirname, 'selftest-output.txt'), text, 'utf8');
  process.stdout.write(text);
}

let pass = 0, fail = 0;
function eq(name, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (ok) { pass++; log('PASS  ' + name); }
  else { fail++; log('FAIL  ' + name + '  actual=' + JSON.stringify(actual) + ' expected=' + JSON.stringify(expected)); }
}
function truthy(name, actual) {
  if (actual) { pass++; log('PASS  ' + name); }
  else { fail++; log('FAIL  ' + name + '  (falsy)'); }
}

/* ---------- 1. 抽取并加载 #core ---------- */
const htmlPath = path.join(__dirname, 'app.html');
const html = fs.readFileSync(htmlPath, 'utf8');
const m = html.match(/<script id="core">([\s\S]*?)<\/script>/);
if (!m) { log('FATAL 未能在 app.html 中找到 <script id="core">'); done(); process.exit(1); }
log('== 抽取 core 脚本：' + m[1].length + ' 字符 ==');

const sandbox = {};
vm.createContext(sandbox);
try {
  vm.runInContext(m[1], sandbox, { filename: 'app.html#core' });
  log('PASS  core 脚本在 vm 中无语法错误并成功执行');
  pass++;
} catch (e) {
  log('FAIL  core 脚本执行报错: ' + e.message);
  done(); process.exit(1);
}
const C = sandbox.AACore;
truthy('AACore 已挂载到全局', !!(C && C.normalizeAmount && C.normalizePeople && C.computeSplit));
log('');

/* ---------- 2. 金额规整 normalizeAmount ---------- */
log('-- normalizeAmount（金额规整）--');
eq('300 -> 30000 分', C.normalizeAmount('300').cents, 30000);
eq("'128.5' -> 12850 分", C.normalizeAmount('128.5').cents, 12850);
eq("'128.555' 规整 -> 12856 分", C.normalizeAmount('128.555').cents, 12856);
eq("'128.555'.rounded === true", C.normalizeAmount('128.555').rounded, true);
eq("'128.55'.rounded === false", C.normalizeAmount('128.55').rounded, false);
eq("'1.234' 舍 -> 123 分", C.normalizeAmount('1.234').cents, 123);
eq("'1.235' 入 -> 124 分", C.normalizeAmount('1.235').cents, 124);
eq("'0.005' 入 -> 1 分", C.normalizeAmount('0.005').cents, 1);
eq("千分位 '1,000' -> 100000 分", C.normalizeAmount('1,000').cents, 100000);
eq("全角逗号 '1，000.50' -> 100050 分", C.normalizeAmount('1，000.50').cents, 100050);
eq("带币符 '￥128.50' -> 12850 分", C.normalizeAmount('￥128.50').cents, 12850);
eq("带空格 ' 88 ' -> 8800 分", C.normalizeAmount(' 88 ').cents, 8800);
eq("'.5' -> 50 分", C.normalizeAmount('.5').cents, 50);
eq("normalized 两位小数 '128.555'", C.normalizeAmount('128.555').normalized, '128.56');
eq("'0' -> 0 分", C.normalizeAmount('0').cents, 0);
eq("空串 code=EMPTY", C.normalizeAmount('').code, 'EMPTY');
eq("纯空格 code=EMPTY", C.normalizeAmount('   ').code, 'EMPTY');
eq("null code=EMPTY", C.normalizeAmount(null).code, 'EMPTY');
eq("'abc' code=INVALID", C.normalizeAmount('abc').code, 'INVALID');
eq("'1.2.3' code=INVALID", C.normalizeAmount('1.2.3').code, 'INVALID');
eq("'.' code=INVALID", C.normalizeAmount('.').code, 'INVALID');
eq("'12.' -> 1200 分", C.normalizeAmount('12.').cents, 1200);
eq("'-100' code=INVALID", C.normalizeAmount('-100').code, 'INVALID');
eq("'1e3' code=INVALID", C.normalizeAmount('1e3').code, 'INVALID');
eq("超长 40 位数字 code=TOO_LARGE", C.normalizeAmount('9'.repeat(40)).code, 'TOO_LARGE');
eq("16 位整数 code=TOO_LARGE", C.normalizeAmount('9999999999999999').code, 'TOO_LARGE');
eq("13 位整数可用", C.normalizeAmount('9999999999999').ok, true);
log('');

/* ---------- 3. 人数规整 normalizePeople ---------- */
log('-- normalizePeople（人数规整）--');
eq("'8' -> 8", C.normalizePeople('8').n, 8);
eq("' 12 ' -> 12", C.normalizePeople(' 12 ').n, 12);
eq("'0' code=ZERO", C.normalizePeople('0').code, 'ZERO');
eq("'00' code=ZERO", C.normalizePeople('00').code, 'ZERO');
eq("'-3' code=INVALID", C.normalizePeople('-3').code, 'INVALID');
eq("'3.5' code=INVALID", C.normalizePeople('3.5').code, 'INVALID');
eq("'abc' code=INVALID", C.normalizePeople('abc').code, 'INVALID');
eq("'' code=EMPTY", C.normalizePeople('').code, 'EMPTY');
eq("'1000001' code=TOO_LARGE", C.normalizePeople('1000001').code, 'TOO_LARGE');
eq("'1000000' 可用", C.normalizePeople('1000000').ok, true);
log('');

/* ---------- 4. 分摊算法 computeSplit ---------- */
log('-- computeSplit（余数分摊）--');
let r = C.computeSplit(100000, 3);
eq('1000元/3人 base', r.baseCents, 33333);
eq('1000元/3人 remainder', r.remainder, 1);
eq('1000元/3人 highCount', r.highCount, 1);
eq('1000元/3人 lowCount', r.lowCount, 2);
eq('1000元/3人 每人基准', r.perPerson, '333.33');
eq('1000元/3人 多付档', r.perPersonHigh, '333.34');
eq('1000元/3人 合计守恒', r.sumCheck, 100000);

r = C.computeSplit(1000, 7);
eq('1000分/7人 base', r.baseCents, 142);
eq('1000分/7人 remainder', r.remainder, 6);
eq('1000分/7人 每人基准', r.perPerson, '1.42');
eq('1000分/7人 多付档', r.perPersonHigh, '1.43');
eq('1000分/7人 合计守恒', r.sumCheck, 1000);

r = C.computeSplit(30000, 8);
eq('300元/8人 余数', r.remainder, 0);
eq('300元/8人 每人', r.perPerson, '37.50');
eq('300元/8人 无多付档', r.highCount, 0);

r = C.computeSplit(0, 5);
eq('0元/5人 每人', r.perPerson, '0.00');
eq('0元/5人 守恒', r.sumCheck, 0);

r = C.computeSplit(1, 3);
eq('1分/3人 base=0', r.baseCents, 0);
eq('1分/3人 1人付 0.01', r.perPersonHigh, '0.01');
eq('1分/3人 守恒', r.sumCheck, 1);

// 随机穷举：守恒 + 每人差额 <= 1 分
let fuzzFail = 0, fuzzRun = 0;
for (let t = 0; t < 20000; t++) {
  const cents = Math.floor(Math.random() * 100000000);
  const people = 1 + Math.floor(Math.random() * 1000);
  const x = C.computeSplit(cents, people);
  fuzzRun++;
  if (x.sumCheck !== cents) fuzzFail++;
  if (x.perPersonHigh !== ((x.baseCents + 1) / 100).toFixed(2)) fuzzFail++;
}
eq('随机 20000 组：合计恒等且档位正确（失败数）', fuzzFail, 0);
log('  随机用例数 = ' + fuzzRun);

// 大数压力：1 万亿元 / 999999 人
r = C.computeSplit(100000000000000, 999999);
eq('1万亿元/999999人 守恒', r.sumCheck, 100000000000000);
truthy('1万亿元/999999人 无 NaN', !isNaN(Number(r.perPerson)));
log('');

/* ---------- 5. 交付物静态检查 ---------- */
log('-- app.html 静态检查 --');
eq('无 http(s):// 外链', /https?:\/\//i.test(html.replace(/https?:\/\/(www\.)?w3\.org/g, '')), false);
eq('无 <script src=', /<script[^>]+src=/i.test(html), false);
eq('无 <link href=', /<link[^>]+href=/i.test(html), false);
eq('无 fetch(', /\bfetch\s*\(/.test(html), false);
eq('无 XMLHttpRequest', /XMLHttpRequest/.test(html), false);
eq('无 import(', /\bimport\s*\(/.test(html), false);
eq('存在 <script id="core">', /<script id="core">/.test(html), true);
eq('存在 <script id="ui">', /<script id="ui">/.test(html), true);
truthy('含 window error 全局兜底', /window\.addEventListener\('error'/.test(html));
truthy('含 try/catch 兜底', /catch\s*\(err\)/.test(html));
log('');

/* ---------- 汇总 ---------- */
log('================================');
log('通过 ' + pass + ' 项，失败 ' + fail + ' 项，共 ' + (pass + fail) + ' 项');
log(fail === 0 ? '结论：全部通过' : '结论：存在失败项');
done();
process.exit(fail === 0 ? 0 : 1);
