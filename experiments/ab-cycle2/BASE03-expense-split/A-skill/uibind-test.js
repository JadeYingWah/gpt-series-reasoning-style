/* uibind-test.js —— 用最小 DOM 桩在 Node 中真实执行 app.html 的 <script id="ui">，
 * 验证「实时反馈 / 非法输入不崩 / 规整提示 / 结果渲染」。
 * 运行：node uibind-test.js   输出写入 uibind-output.txt
 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const OUT = [];
const log = s => OUT.push(s);
let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; log('PASS  ' + name); }
  else { fail++; log('FAIL  ' + name + (extra ? '  ' + extra : '')); }
}

/* ---------- 最小 DOM 桩 ---------- */
class ClassList {
  constructor() { this.s = new Set(); }
  add(...c) { c.forEach(x => this.s.add(x)); }
  remove(...c) { c.forEach(x => this.s.delete(x)); }
  contains(c) { return this.s.has(c); }
}
class El {
  constructor(tag) {
    this.tagName = tag; this.children = []; this._text = '';
    this.classList = new ClassList(); this.attrs = {}; this.value = ''; this._l = {};
  }
  set textContent(v) { this._text = String(v); this.children = []; }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(''); }
  appendChild(c) { this.children.push(c); return c; }
  get firstChild() { return this.children.length ? this.children[0] : null; }
  removeChild(c) { const i = this.children.indexOf(c); if (i >= 0) this.children.splice(i, 1); return c; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
  addEventListener(t, fn) { (this._l[t] = this._l[t] || []).push(fn); }
  dispatch(t) { (this._l[t] || []).forEach(fn => fn()); }
  querySelectorAll() { return []; }
}

const IDS = ['total', 'people', 'totalField', 'peopleField', 'totalHint', 'peopleHint',
             'result', 'bigAmount', 'lines', 'note'];
const byId = {};
IDS.forEach(id => { byId[id] = new El('div'); });

/* 从 app.html 里真实解析出 .quick button 的 data-fill，构造同样的按钮桩，
   以便真实执行按钮的 click 回调（否则这条路径完全未被覆盖）。 */
const htmlForButtons = fs.readFileSync(path.join(__dirname, 'app.html'), 'utf8');
const quickButtons = [];
const btnRe = /<button[^>]*data-fill="([^"]*)"[^>]*>/g;
let bm;
while ((bm = btnRe.exec(htmlForButtons)) !== null) {
  const el = new El('button');
  el.setAttribute('data-fill', bm[1].replace(/&quot;/g, '"'));
  quickButtons.push(el);
}

const documentStub = {
  getElementById: id => byId[id] || null,
  createElement: tag => new El(tag),
  createTextNode: t => { const e = new El('#text'); e._text = String(t); return e; },
  querySelectorAll: sel => (String(sel).indexOf('quick') >= 0 ? quickButtons : []),
  addEventListener: () => {}
};

const win = {};
win.window = win;
win.document = documentStub;
win.console = { error: () => {}, log: () => {}, warn: () => {} };
const winListeners = {};
win.addEventListener = (t, fn) => { (winListeners[t] = winListeners[t] || []).push(fn); };
win.setTimeout = (fn) => fn();

const ctx = vm.createContext(win);

/* ---------- 抽取并执行两段脚本 ---------- */
const html = fs.readFileSync(path.join(__dirname, 'app.html'), 'utf8');
const coreSrc = html.match(/<script id="core">([\s\S]*?)<\/script>/)[1];
const uiSrc = html.match(/<script id="ui">([\s\S]*?)<\/script>/)[1];

try {
  vm.runInContext(coreSrc, ctx, { filename: 'core' });
  log('PASS  core 脚本装载成功');
  pass++;
} catch (e) { log('FAIL  core 装载失败: ' + e.message); fail++; }

let uiLoaded = true;
try {
  vm.runInContext(uiSrc, ctx, { filename: 'ui' });
  log('PASS  ui 脚本装载成功（初始 render() 执行未抛异常）');
  pass++;
} catch (e) { uiLoaded = false; log('FAIL  ui 装载即抛异常: ' + e.message); fail++; }

if (!uiLoaded) { fs.writeFileSync(path.join(__dirname, 'uibind-output.txt'), OUT.join('\n') + '\n', 'utf8'); process.exit(1); }

/* ---------- 断言工具 ---------- */
const T = el => el.textContent;
function setAndRender(total, people) {
  byId.total.value = total;
  byId.people.value = people;
  byId.total.dispatch('input');
}
function linesText() { return T(byId.lines); }
function bigText() { return T(byId.bigAmount); }

/* ---------- 场景 1：初始空态 ---------- */
log('');
log('-- 场景 1：初始空态 --');
ok('结果区带 err 类（提示而非崩溃）', byId.result.classList.contains('err'));
ok('大字显示占位 —', bigText().indexOf('—') === 0, 'actual=' + bigText());
ok('提示包含「金额不能为空」', linesText().indexOf('金额不能为空') >= 0, 'actual=' + linesText());
ok('提示包含「人数不能为空」', linesText().indexOf('人数不能为空') >= 0, 'actual=' + linesText());
ok('状态行无「人数：人数」重复措辞', linesText().indexOf('人数：人数') < 0, 'actual=' + linesText());

/* ---------- 场景 2：1000 元 / 7 人 ---------- */
log('');
log('-- 场景 2：1000 元 / 7 人 --');
setAndRender('1000', '7');
// 1000.00 / 7 = 142.857.. -> 基准 142.85，余 5 分 -> 5 人付 142.86、2 人付 142.85
ok('大字 = 142.85 元/人', bigText().indexOf('142.85') === 0, 'actual=' + bigText());
ok('有余数时标注「基准」', bigText().indexOf('（基准）') >= 0, 'actual=' + bigText());
ok('结果区不再带 err', !byId.result.classList.contains('err'));
ok('明细含 5 人 × ¥142.86', linesText().indexOf('5 人 × ¥142.86') >= 0, 'actual=' + linesText());
ok('明细含 2 人 × ¥142.85', linesText().indexOf('2 人 × ¥142.85') >= 0);
ok('校验行合计 ¥1000.00', linesText().indexOf('¥1000.00') >= 0);
ok('校验标记「一致」', linesText().indexOf('一致') >= 0);
ok('金额字段标 good', byId.totalField.classList.contains('good'));
ok('金额 hint 显示识别值', T(byId.totalHint).indexOf('¥1000.00') >= 0, 'actual=' + T(byId.totalHint));

/* ---------- 场景 3：超 2 位小数规整提示 ---------- */
log('');
log('-- 场景 3：128.555 元 / 3 人（规整）--');
setAndRender('128.555', '3');
ok('hint 提示已规整', T(byId.totalHint).indexOf('规整') >= 0, 'actual=' + T(byId.totalHint));
ok('hint 标 warn 类', byId.totalHint.classList.contains('warn'));
ok('规整值 = ¥128.56', T(byId.totalHint).indexOf('128.56') >= 0);
// 128.56 / 3 = 42.8533.. -> 基准 42.85，余 1 分 -> 1 人付 42.86、2 人付 42.85
ok('大字 = 42.85', bigText().indexOf('42.85') === 0, 'actual=' + bigText());
ok('明细含 1 人 × ¥42.86', linesText().indexOf('1 人 × ¥42.86') >= 0, 'actual=' + linesText());
ok('明细含「余数 1 分」', linesText().indexOf('余数 1 分') >= 0, 'actual=' + linesText());
ok('校验合计 = 128.56', linesText().indexOf('¥128.56') >= 0, 'actual=' + linesText());

/* ---------- 场景 4：非法人数不崩 ---------- */
log('');
log('-- 场景 4：人数 0 / 负数 / 小数 / 文本 --');
[['300', '0'], ['300', '-3'], ['300', '3.5'], ['300', 'abc']].forEach(([t, p]) => {
  let threw = null;
  try { setAndRender(t, p); } catch (e) { threw = e; }
  ok('人数=' + JSON.stringify(p) + ' 不抛异常', threw === null, threw && threw.message);
  ok('人数=' + JSON.stringify(p) + ' 结果区为 err 态', byId.result.classList.contains('err'));
  ok('人数=' + JSON.stringify(p) + ' 大字回落 —', bigText().indexOf('—') === 0, 'actual=' + bigText());
});
setAndRender('300', '0');
ok('人数 0 提示「人数：必须大于 0」', linesText().indexOf('人数：必须大于 0') >= 0, 'actual=' + linesText());
setAndRender('300', '-3');
ok('人数 -3 提示「正整数」', linesText().indexOf('正整数') >= 0, 'actual=' + linesText());
setAndRender('300', '');
ok('人数空 提示「人数不能为空」', linesText().indexOf('人数不能为空') >= 0, 'actual=' + linesText());

/* ---------- 场景 5：金额非法不崩 ---------- */
log('');
log('-- 场景 5：金额非法 --');
[['', '8'], ['  ', '8'], ['abc', '8'], ['1.2.3', '8'], ['-100', '8'], ['1e3', '8']].forEach(([t, p]) => {
  let threw = null;
  try { setAndRender(t, p); } catch (e) { threw = e; }
  ok('金额=' + JSON.stringify(t) + ' 不抛异常', threw === null, threw && threw.message);
  ok('金额=' + JSON.stringify(t) + ' 结果区为 err 态', byId.result.classList.contains('err'));
});
setAndRender('', '8');
ok('空金额提示「金额不能为空」', linesText().indexOf('金额不能为空') >= 0, 'actual=' + linesText());
setAndRender('abc', '8');
ok('非法金额提示「金额：只能包含数字和一个小数点」',
   linesText().indexOf('金额：只能包含数字和一个小数点') >= 0, 'actual=' + linesText());

/* ---------- 场景 6：超长 / 特殊字符 ---------- */
log('');
log('-- 场景 6：超长与特殊字符 --');
const weird = ['9'.repeat(60), '9'.repeat(14), '\u0000\u0001', '<script>alert(1)</scr' + 'ipt>',
               '1'.repeat(20) + '.' + '9'.repeat(50), '٣٣٣', '½', 'Infinity', 'NaN', '0x10', '1,2,3.4.5'];
let weirdThrow = 0;
weird.forEach(w => {
  let threw = null;
  try { setAndRender(w, '5'); } catch (e) { threw = e; weirdThrow++; log('  抛出: ' + JSON.stringify(w) + ' -> ' + e.message); }
  try { setAndRender('100', w); } catch (e) { threw = e; weirdThrow++; log('  抛出(人数): ' + JSON.stringify(w) + ' -> ' + e.message); }
});
ok('超长/特殊字符输入零异常（共 ' + weird.length * 2 + ' 组）', weirdThrow === 0);

/* ---------- 场景 7：随机模糊 ---------- */
log('');
log('-- 场景 7：随机模糊 5000 组 --');
const alphabet = '0123456789.-+,，￥  abcXYZ\u0000\n\t．½%';
let fuzzThrow = 0;
for (let i = 0; i < 5000; i++) {
  const len = Math.floor(Math.random() * 30);
  let s = '';
  for (let j = 0; j < len; j++) s += alphabet[Math.floor(Math.random() * alphabet.length)];
  try { setAndRender(s, s); } catch (e) { fuzzThrow++; if (fuzzThrow <= 3) log('  抛出: ' + JSON.stringify(s) + ' -> ' + e.message); }
}
ok('随机模糊 5000 组零未捕获异常', fuzzThrow === 0, '抛出 ' + fuzzThrow + ' 次');

/* ---------- 场景 8：极端守恒 ---------- */
log('');
log('-- 场景 8：极端值守恒 --');
setAndRender('0', '1');
ok('0 元 / 1 人 = 0.00', bigText().indexOf('0.00') === 0, 'actual=' + bigText());
setAndRender('0.01', '3');
ok('0.01 元 / 3 人 = 0.00 基准', bigText().indexOf('0.00') === 0, 'actual=' + bigText());
ok('0.01 元 / 3 人 有 1 人多付 0.01', linesText().indexOf('1 人 × ¥0.01') >= 0, 'actual=' + linesText());
setAndRender('9999999999999.99', '2');
ok('13 位整数可用且不崩', !byId.result.classList.contains('err'), 'actual=' + linesText());
setAndRender('99999999999999.99', '2');
ok('14 位整数被拒（TOO_LARGE）', byId.result.classList.contains('err'));

/* ---------- 场景 9：快捷按钮点击（真实执行 click 回调） ---------- */
log('');
log('-- 场景 9：快捷按钮 click 回调 --');
ok('从 app.html 解析到 4 个 .quick button', quickButtons.length === 4, 'actual=' + quickButtons.length);
if (quickButtons.length === 4) {
  let threw = null;
  try { quickButtons[0].dispatch('click'); } catch (e) { threw = e; }
  ok('按钮1「1000 元 / 7 人」不抛异常', threw === null, threw && threw.message);
  ok('按钮1 填入 total=1000', byId.total.value === '1000', 'actual=' + byId.total.value);
  ok('按钮1 填入 people=7', byId.people.value === '7', 'actual=' + byId.people.value);
  ok('按钮1 渲染出 142.85', bigText().indexOf('142.85') === 0, 'actual=' + bigText());

  threw = null;
  try { quickButtons[1].dispatch('click'); } catch (e) { threw = e; }
  ok('按钮2「128.555 元 / 3 人」不抛异常', threw === null, threw && threw.message);
  ok('按钮2 触发规整提示', T(byId.totalHint).indexOf('规整') >= 0, 'actual=' + T(byId.totalHint));
  ok('按钮2 渲染出 42.85', bigText().indexOf('42.85') === 0, 'actual=' + bigText());

  threw = null;
  try { quickButtons[2].dispatch('click'); } catch (e) { threw = e; }
  ok('按钮3「边界：人数 0」不抛异常', threw === null, threw && threw.message);
  ok('按钮3 people=0 且结果区 err', byId.people.value === '0' && byId.result.classList.contains('err'));
  ok('按钮3 提示「人数：必须大于 0」', linesText().indexOf('人数：必须大于 0') >= 0, 'actual=' + linesText());

  threw = null;
  try { quickButtons[3].dispatch('click'); } catch (e) { threw = e; }
  ok('按钮4「清空」不抛异常', threw === null, threw && threw.message);
  ok('按钮4 清空两个输入', byId.total.value === '' && byId.people.value === '');
  ok('按钮4 回到空态提示', linesText().indexOf('金额不能为空') >= 0, 'actual=' + linesText());
}

/* ---------- 汇总 ---------- */
log('');
log('================================');
log('通过 ' + pass + ' 项，失败 ' + fail + ' 项，共 ' + (pass + fail) + ' 项');
log(fail === 0 ? '结论：全部通过' : '结论：存在失败项');
fs.writeFileSync(path.join(__dirname, 'uibind-output.txt'), OUT.join('\n') + '\n', 'utf8');
process.exit(fail === 0 ? 0 : 1);
