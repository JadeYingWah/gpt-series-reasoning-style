// DOM 接线验收：用最小 DOM 垫片真实执行 app.html 中的完整脚本（含事件处理）
// 目的：验证 render()/setCategory()/swap 在非法输入、空输入、负数、超长文本下不抛异常且给出提示
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'app.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const bodyHtml = html.slice(html.indexOf('<body>'), html.indexOf('</body>'));

/* ---------------- 最小 DOM 垫片 ---------------- */
class ClassList {
  constructor() { this.s = new Set(); }
  add(c) { this.s.add(c); }
  remove(c) { this.s.delete(c); }
  toggle(c, force) {
    if (force === undefined) force = !this.s.has(c);
    if (force) this.s.add(c); else this.s.delete(c);
    return force;
  }
  contains(c) { return this.s.has(c); }
  toString() { return [...this.s].join(' '); }
}
class El {
  constructor(tag) {
    this.tagName = tag;
    this.children = [];
    this.attrs = {};
    this.dataset = {};
    this.classList = new ClassList();
    this._text = '';
    this._value = '';
    this.listeners = {};
    this.tabIndex = 0;
  }
  appendChild(c) { this.children.push(c); c.parentNode = this; return c; }
  addEventListener(t, fn) { (this.listeners[t] = this.listeners[t] || []).push(fn); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  removeAttribute(k) { delete this.attrs[k]; }
  getAttribute(k) { return this.attrs[k]; }
  focus() { global.document.activeElement = this; }
  fire(type, ev) {
    (this.listeners[type] || []).forEach(fn => fn.call(this, Object.assign({ preventDefault() {}, target: this }, ev)));
  }
  get textContent() { return this._text; }
  set textContent(v) { this._text = String(v); this.children = []; }
  get value() { return this._value; }
  set value(v) { this._value = String(v); }
  get options() { return this.children; }
}
class Opt extends El {
  constructor(name, value) { super('option'); this.name = name; this.value = value; this.textContent = name; }
}

function parseIds(html2) {
  const map = {};
  const re = /<(\w+)([^>]*)id="([^"]+)"([^>]*)>/g;
  let m;
  while ((m = re.exec(html2))) {
    const el = new El(m[1]);
    el.id = m[3];
    const attrStr = m[2] + m[4];
    const dc = attrStr.match(/data-cat="([^"]+)"/);
    if (dc) el.dataset.cat = dc[1];
    map[m[3]] = el;
  }
  return map;
}

const byId = parseIds(bodyHtml);

// 三个 tab（按文档顺序）
const tabCats = [...bodyHtml.matchAll(/data-cat="([^"]+)"/g)].map(x => x[1]);
const tabs = tabCats.map(c => { const e = new El('button'); e.dataset.cat = c; return e; });
const tabsBar = new El('div');

global.Option = Opt;
global.document = {
  activeElement: null,
  querySelectorAll: sel => (sel === '.tab' ? tabs : []),
  querySelector: sel => (sel === '.tabs' ? tabsBar : null),
  getElementById: id => byId[id],
  createElement: tag => new El(tag)
};

/* ---------------- 执行交付脚本 ---------------- */
const errors = [];
try {
  new Function(script)();
} catch (e) {
  errors.push('初始化抛异常: ' + e.message);
}

const $ = id => byId[id];
let pass = 0, fail = 0;
function ok(cond, label, extra) {
  if (cond) pass++; else { fail++; console.log('FAIL ' + label + (extra ? ' | ' + extra : '')); }
}
// 每次调用都包住，异常即失败
function safe(label, fn) {
  try { fn(); pass++; return true; }
  catch (e) { fail++; console.log('FAIL ' + label + ' 抛异常: ' + e.message); return false; }
}
function type(v) { $('value').value = v; $('value').fire('input'); }

/* ---------- A. 初始化状态 ---------- */
ok(errors.length === 0, '脚本初始化无异常', errors.join(';'));
ok($('from').value === 'm' && $('to').value === 'ft', '初始长度单位 m->ft', $('from').value + '->' + $('to').value);
ok($('from').children.length === 8, '长度单位 8 个', String($('from').children.length));
ok($('primary').textContent === '—', '初始结果为空占位');
ok($('err').textContent === '', '初始无错误');

/* ---------- B. 输入即换算（无计算按钮） ---------- */
safe('输入 1 米', () => type('1'));
ok(/^1 米 = 3\.280839895 英尺$/.test($('primary').textContent), '1米=3.280839895英尺', $('primary').textContent);
safe('输入 0', () => type('0'));
ok($('primary').textContent === '0 米 = 0 英尺', '0 边界值', $('primary').textContent);
ok($('err').textContent === '', '0 无错误提示');

/* ---------- C. 非法输入 ---------- */
const badCases = ['', '   ', 'abc', '1a', '--1', '1..2', '1,000', 'Infinity', 'NaN', '0x10', '1/2', '＄', '　', '  12  '];
badCases.forEach(c => {
  safe('非法输入 ' + JSON.stringify(c), () => type(c));
  const isEmpty = c.trim() === '';
  if (isEmpty) {
    ok($('primary').textContent === '—' && $('err').textContent === '', '空输入: 占位且不报错 ' + JSON.stringify(c));
  } else if (c.trim() === '12') {
    ok($('err').textContent === '', '两侧空白应被接受');
  } else {
    ok($('err').textContent.length > 0, '非法输入给出提示 ' + JSON.stringify(c));
    ok($('primary').textContent === '—', '非法输入清空结果 ' + JSON.stringify(c));
    ok($('value').getAttribute('aria-invalid') === 'true', '非法输入标记 aria-invalid ' + JSON.stringify(c));
  }
});

/* ---------- D. 超长文本 ---------- */
safe('超长文本 10000 字符', () => type('9'.repeat(10000)));
ok($('err').textContent.length > 0, '超长文本有提示且不崩');
ok($('err').textContent.length < 80, '超长文本提示被截断', String($('err').textContent.length));
safe('超长小数 1.' + '0'.repeat(500) + '1', () => type('1.' + '0'.repeat(500) + '1'));
ok(true, '超长小数未抛异常');

/* ---------- E. 负数：长度/重量拒绝，温度允许 ---------- */
safe('长度 -5', () => type('-5'));
ok(/负数/.test($('err').textContent), '长度负数被拒', $('err').textContent);
ok($('primary').textContent === '—', '长度负数结果清空');

safe('切到重量', () => tabs[1].fire('click'));
safe('重量 -1', () => type('-1'));
ok(/负数/.test($('err').textContent), '重量负数被拒', $('err').textContent);

/* ---------- F. 温度公式与边界（走完整渲染链路） ---------- */
safe('切到温度', () => tabs[2].fire('click'));
ok($('from').value === 'c' && $('to').value === 'f', '温度默认 c->f');
ok($('from').children.length === 3, '温度单位 3 个');
safe('温度 0', () => type('0'));
ok($('primary').textContent === '0 摄氏度 (°C) = 32 华氏度 (°F)', '0°C=32°F', $('primary').textContent);
safe('温度 100', () => type('100'));
ok(/= 212 华氏度/.test($('primary').textContent), '100°C=212°F', $('primary').textContent);
safe('温度 -40', () => type('-40'));
ok($('err').textContent === '', '温度负数被允许');
ok($('primary').textContent === '-40 摄氏度 (°C) = -40 华氏度 (°F)', '-40°C=-40°F', $('primary').textContent);

// 华氏 -> 开尔文：-459.67F = 0K
safe('F->K 绝对零度', () => {
  $('from').value = 'f'; $('to').value = 'k'; $('from').fire('change');
  type('-459.67');
});
ok(/= 0 开尔文/.test($('primary').textContent), '-459.67°F = 0K', $('primary').textContent);

// 低于绝对零度 -> 提示但不阻断
safe('低于绝对零度', () => type('-500'));
ok(/绝对零度/.test($('note').textContent), '低于绝对零度给出提示', $('note').textContent);
ok(/华氏度/.test($('primary').textContent), '低于绝对零度仍做数学换算');

/* ---------- G. 交换单位 ---------- */
safe('切回长度', () => tabs[0].fire('click'));
safe('交换前输入', () => type('2'));
const before = $('primary').textContent;
safe('点击交换', () => $('swap').fire('click'));
ok($('from').value === 'ft' && $('to').value === 'm', '交换后单位反转', $('from').value + '->' + $('to').value);
ok($('primary').textContent !== before, '交换后结果重算', $('primary').textContent);
ok(/^2 英尺 = 0\.6096 米$/.test($('primary').textContent), '2ft=0.6096m', $('primary').textContent);

/* ---------- H. 溢出 ---------- */
safe('溢出 1e308 km->mm', () => {
  $('from').value = 'km'; $('to').value = 'mm'; $('from').fire('change');
  type('1e308');
});
ok($('err').textContent.length > 0, '溢出给出提示', $('err').textContent);

/* ---------- I. 键盘：方向键切换类别 ---------- */
safe('方向键右', () => {
  global.document.activeElement = tabs[0];
  tabsBar.fire('keydown', { key: 'ArrowRight' });
});
ok(tabs[1].getAttribute('aria-selected') === 'true', 'ArrowRight 切到重量', String(tabs[1].getAttribute('aria-selected')));
safe('方向键左回绕', () => {
  global.document.activeElement = tabs[0];
  tabsBar.fire('keydown', { key: 'ArrowLeft' });
});
ok(tabs[2].getAttribute('aria-selected') === 'true', 'ArrowLeft 回绕到温度');
safe('Home 键', () => {
  global.document.activeElement = tabs[2];
  tabsBar.fire('keydown', { key: 'Home' });
});
ok(tabs[0].getAttribute('aria-selected') === 'true', 'Home 回到长度');
safe('Tab 键不拦截', () => {
  global.document.activeElement = tabs[0];
  tabsBar.fire('keydown', { key: 'Tab' });
});
ok(tabs[0].getAttribute('aria-selected') === 'true', 'Tab 键不被吞掉');

/* ---------- J. 类别切换后结果重算不抛异常 ---------- */
['length', 'weight', 'temperature'].forEach((c, i) => {
  safe('切换类别 ' + c, () => { tabs[i].fire('click'); type('1'); });
});

console.log('\nPASS=' + pass + '  FAIL=' + fail);
process.exit(fail ? 1 : 0);
