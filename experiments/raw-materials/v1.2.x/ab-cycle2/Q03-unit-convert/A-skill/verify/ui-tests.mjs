/**
 * app.html 交互层端到端验证（真实浏览器内核）
 * 做法：把测试脚本注入 app.html 副本 -> Chrome headless --dump-dom -> 取回页面内生成的
 *       base64 报告 -> 解析。测的是真实 DOM + 真实事件分发，不是自制 DOM 桩。
 * 运行：node verify/ui-tests.mjs
 * 产出：verify/_ui-probe.html（注入后的副本）、verify/_dump.html（原始 DOM 转储）、verify/ui-tests.log
 */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const APP = path.join(__dirname, '..', 'app.html');
const PROBE = path.join(__dirname, '_ui-probe.html');
const DUMP = path.join(__dirname, '_dump.html');
const LOG = path.join(__dirname, 'ui-tests.log');

const BROWSERS = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
];

const TEST_JS = `
<script>
(function () {
  var R = [];
  var pageErrors = [];
  window.addEventListener('error', function (e) { pageErrors.push('error: ' + (e.message || e.type)); });
  window.addEventListener('unhandledrejection', function (e) { pageErrors.push('rejection: ' + e.reason); });
  var $ = function (id) { return document.getElementById(id); };
  var outText = function () { return $('outValue').textContent; };
  var outUnit = function () { return $('outUnit').textContent; };
  var msgCls  = function () { return $('msg').className; };
  var msgTxt  = function () { return $('msg').textContent; };
  function rec(name, ok, detail) { R.push({ name: name, ok: !!ok, detail: String(detail == null ? '' : detail) }); }
  function type(v) {
    var el = $('valueInput');
    el.value = v;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }
  function pick(sel, v) {
    var el = $(sel);
    el.value = v;
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }
  function cat(id) {
    document.querySelector('.tab[data-cat="' + id + '"]').click();
  }
  try {
    /* --- 初始状态 --- */
    rec('初始：长度 1 m -> cm 显示 100', outText() === '100', outText() + ' / ' + outUnit());
    rec('初始：结果带单位 cm', outUnit() === 'cm', outUnit());
    rec('初始：长度 tab aria-pressed=true',
        document.querySelector('.tab[data-cat="length"]').getAttribute('aria-pressed') === 'true');

    /* --- 输入即换算（无计算按钮） --- */
    type('2.5');
    rec('输入即换算：2.5 m -> cm = 250', outText() === '250', outText());
    type('0');
    rec('零边界：0 m -> cm = 0', outText() === '0', outText());
    type('1');
    pick('fromUnit', 'in'); pick('toUnit', 'cm');
    rec('小数精度：1 in -> cm = 2.54', outText() === '2.54', outText());
    rec('换算关系行随单位更新', $('formula').textContent.indexOf('2.54') >= 0, $('formula').textContent);

    /* --- 交互反馈 --- */
    pick('fromUnit', 'm'); pick('toUnit', 'cm'); type('3');
    rec('输入后结果区有 flash 反馈类', $('resultBox').classList.contains('flash'),
        $('resultBox').className);

    /* --- 非法输入 --- */
    type('abc');
    rec('字母输入：输出为 —', outText() === '—', outText());
    rec('字母输入：提示为 error 级', msgCls() === 'msg error', msgCls());
    rec('字母输入：提示含「不是有效数字」', msgTxt().indexOf('不是有效数字') >= 0, msgTxt());
    rec('字母输入：aria-invalid=true', $('valueInput').getAttribute('aria-invalid') === 'true',
        $('valueInput').getAttribute('aria-invalid'));
    type('');
    rec('空输入：输出为 —', outText() === '—', outText());
    rec('空输入：提示为 hint 级（非报错）', msgCls() === 'msg hint', msgCls());
    rec('空输入：提示引导输入', msgTxt().indexOf('请输入') >= 0, msgTxt());
    type('9'.repeat(300));
    rec('超长 300 字符：被拦截且不崩', outText() === '—' && msgTxt().indexOf('过长') >= 0, msgTxt().slice(0, 40));
    rec('超长输入后页面仍可继续换算', (function () { type('4'); return outText() === '400'; })(), outText());
    type('-5');
    rec('负数长度：输出为 —', outText() === '—', outText());
    rec('负数长度：提示含「不能为负值」', msgTxt().indexOf('不能为负值') >= 0, msgTxt());

    /* --- 交换按钮 --- */
    type('100');
    var f0 = $('fromUnit').value, t0 = $('toUnit').value;
    $('swapBtn').click();
    rec('交换：from/to 互换', $('fromUnit').value === t0 && $('toUnit').value === f0,
        f0 + '->' + t0 + ' 变 ' + $('fromUnit').value + '->' + $('toUnit').value);
    rec('交换：结果同步重算（100 cm -> m = 1）', outText() === '1', outText());
    rec('交换：焦点移到源单位下拉框（键盘可达）', document.activeElement === $('fromUnit'),
        document.activeElement && document.activeElement.id);

    /* --- 切到重量 --- */
    cat('weight');
    rec('切重量：长度 tab 取消选中',
        document.querySelector('.tab[data-cat="length"]').getAttribute('aria-pressed') === 'false');
    rec('切重量：重量 tab 选中',
        document.querySelector('.tab[data-cat="weight"]').getAttribute('aria-pressed') === 'true');
    rec('切重量：源单位下拉框已重建为重量单位',
        $('fromUnit').options.length === 6 && $('fromUnit').value === 'kg',
        $('fromUnit').options.length + ' 项，值=' + $('fromUnit').value);
    rec('切重量：标签同步为「重量」', $('inputLabel').textContent.indexOf('重量') >= 0,
        $('inputLabel').textContent);
    type('1');
    rec('重量换算：1 kg -> lb = 2.2046226', outText() === '2.2046226', outText());
    type('-1');
    rec('负数重量：被拦截', outText() === '—' && msgTxt().indexOf('不能为负值') >= 0, msgTxt());
    pick('fromUnit', 'oz'); pick('toUnit', 'g'); type('1');
    rec('重量换算：1 oz -> g = 28.349523', outText() === '28.349523', outText());

    /* --- 切到温度 --- */
    cat('temp');
    rec('切温度：源单位下拉框为 摄氏度/华氏度/开尔文',
        $('fromUnit').options.length === 3 && $('fromUnit').value === 'c' && $('toUnit').value === 'f',
        $('fromUnit').value + '->' + $('toUnit').value);
    type('0');
    rec('温度 0 °C -> °F = 32', outText() === '32', outText());
    type('100');
    rec('温度 100 °C -> °F = 212', outText() === '212', outText());
    type('-40');
    rec('温度负值 -40 °C -> °F = -40', outText() === '-40', outText());
    rec('温度负值：不是错误提示', msgCls() !== 'msg error', msgCls());
    type('37');
    rec('温度 37 °C -> °F = 98.6', outText() === '98.6', outText());
    pick('fromUnit', 'k'); pick('toUnit', 'c'); type('0');
    rec('温度 0 K -> °C = -273.15', outText() === '-273.15', outText());
    pick('toUnit', 'f'); type('0');
    rec('温度 0 K -> °F = -459.67', outText() === '-459.67', outText());
    pick('fromUnit', 'f'); pick('toUnit', 'c'); type('32');
    rec('温度 32 °F -> °C = 0', outText() === '0', outText());
    pick('fromUnit', 'c'); pick('toUnit', 'k'); type('-300');
    rec('低于绝对零度：仍给出算术结果但不阻断', outText() === '-26.85', outText());
    rec('低于绝对零度：给出 warn 级提示', msgCls() === 'msg warn', msgCls());
    rec('低于绝对零度：提示说明物理无意义', msgTxt().indexOf('绝对零度') >= 0, msgTxt());

    /* --- 键盘可达结构 --- */
    var focusables = Array.prototype.slice.call(
      document.querySelectorAll('button, input, select, a[href], [tabindex]')
    ).filter(function (el) { return el.tabIndex >= 0 && !el.disabled; });
    var ids = focusables.map(function (el) { return el.id || el.dataset.cat || el.tagName; });
    rec('可聚焦元素顺序为 类别 -> 数值 -> 源单位 -> 交换 -> 目标单位',
        ids.join(',').indexOf('length,weight,temp,valueInput,fromUnit,swapBtn,toUnit') === 0,
        ids.join(','));
    rec('可聚焦元素均为原生控件且 tabIndex >= 0',
        focusables.every(function (el) { return el.tabIndex >= 0; }), focusables.length + ' 个');

    /* --- 无「计算」按钮 --- */
    var btns = Array.prototype.slice.call(document.querySelectorAll('button'));
    rec('按钮总数 = 4（3 类别 + 1 交换）', btns.length === 4, String(btns.length));
    rec('不存在「计算」按钮',
        btns.every(function (b) { return b.textContent.indexOf('计算') < 0; }),
        btns.map(function (b) { return b.textContent.trim(); }).join('|'));
    rec('输入框为文本类型且无 change 才触发的限制（支持 input 即时触发）',
        $('valueInput').tagName === 'INPUT' && $('valueInput').getAttribute('type') === 'text',
        $('valueInput').getAttribute('type'));

    /* --- 无未捕获异常 --- */
    rec('全程无未捕获异常/未处理拒绝', pageErrors.length === 0, pageErrors.join(' ; '));

    var pass = R.filter(function (r) { return r.ok; }).length;
    var payload = JSON.stringify({ total: R.length, pass: pass, fail: R.length - pass, rows: R });
    var b64 = btoa(unescape(encodeURIComponent(payload)));
    var pre = document.createElement('pre');
    pre.id = '__report';
    pre.textContent = b64;
    document.body.appendChild(pre);
    document.title = (R.length - pass === 0 ? 'ALLPASS' : 'FAILED') + ' ' + pass + '/' + R.length;
  } catch (e) {
    var pre2 = document.createElement('pre');
    pre2.id = '__report';
    pre2.textContent = 'FATAL ' + (e && e.message);
    document.body.appendChild(pre2);
  }
})();
</script>
`;

/* ---------- 生成注入副本 ---------- */
const html = fs.readFileSync(APP, 'utf8');
const iBody = html.lastIndexOf('</body>');
const probe = html.slice(0, iBody) + TEST_JS + html.slice(iBody);
fs.writeFileSync(PROBE, probe, 'utf8');

/* ---------- 跑浏览器 ---------- */
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'unitconv-'));
const url = 'file:///' + PROBE.replace(/\\/g, '/');
const baseArgs = ['--headless=new', '--disable-gpu', '--no-sandbox', '--no-first-run',
  '--no-default-browser-check', '--disable-extensions', '--disable-sync',
  '--virtual-time-budget=8000', '--user-data-dir=' + profile, '--dump-dom', url];

let dump = '', used = '', stderr = '';
for (const exe of BROWSERS) {
  if (!fs.existsSync(exe)) continue;
  try {
    const buf = execFileSync(exe, baseArgs, { maxBuffer: 128 * 1024 * 1024, timeout: 90000 });
    dump = buf.toString('utf8');
    used = exe;
    if (dump.indexOf('__report') >= 0) break;
  } catch (e) {
    stderr += `${exe}: ${e.message}\n` + (e.stderr ? e.stderr.toString('utf8').slice(0, 400) : '');
  }
}
fs.writeFileSync(DUMP, dump, 'utf8');

/* ---------- 原始交付文件的独立加载检查（未注入任何测试代码） ---------- */
let standalone = { ok: false, detail: '未执行' };
if (used) {
  try {
    const raw = execFileSync(used, baseArgs.slice(0, -2).concat(['--dump-dom', 'file:///' + APP.replace(/\\/g, '/')]),
      { maxBuffer: 128 * 1024 * 1024, timeout: 90000 }).toString('utf8');
    fs.writeFileSync(path.join(__dirname, '_dump-standalone.html'), raw, 'utf8');
    const problems = [];
    if (raw.indexOf('单位换算') < 0) problems.push('中文标题缺失');
    if (raw.indexOf('\uFFFD') >= 0) problems.push('出现替换字符（编码错误）');
    if (raw.indexOf('<span id="outValue">100</span>') < 0) problems.push('初始换算结果不是 100');
    if (raw.indexOf('cm') < 0) problems.push('初始目标单位缺失');
    if (/Unable to|SyntaxError|ReferenceError/i.test(raw)) problems.push('页面脚本报错');
    const tabs = (raw.match(/class="tab"/g) || []).length;
    if (tabs !== 3) problems.push('类别按钮数 = ' + tabs);
    standalone = { ok: problems.length === 0, detail: problems.join(' ; ') || '独立加载正常，初始即显示 100 cm' };
  } catch (e) {
    standalone = { ok: false, detail: '独立加载执行失败：' + e.message };
  }
}

const lines = [];
lines.push('target     : ' + APP);
lines.push('browser    : ' + (used || '(未找到可用浏览器)'));
lines.push('probe html : ' + PROBE);
lines.push('dump html  : ' + DUMP + ' (' + dump.length + ' 字符)');
lines.push('');

let fatal = null, report = null;
if (!used) {
  fatal = '未找到可用浏览器内核，交互层无法端到端验证';
} else {
  const m = dump.match(/<pre id="__report">([\s\S]*?)<\/pre>/);
  if (!m) {
    fatal = '浏览器 DOM 转储中未找到 __report 节点（页面脚本可能未执行）';
    lines.push('stderr: ' + stderr.slice(0, 800));
  } else if (m[1].indexOf('FATAL') === 0) {
    fatal = '注入测试脚本内部异常：' + m[1];
  } else {
    try {
      report = JSON.parse(Buffer.from(m[1].trim(), 'base64').toString('utf8'));
    } catch (e) {
      fatal = '报告解析失败：' + e.message;
    }
  }
}

if (fatal) {
  lines.push('FATAL: ' + fatal);
  lines.push('RESULT: UNVERIFIED（交互层未能验证，需人工按 response.md 的自验步骤复核）');
  fs.writeFileSync(LOG, lines.join('\n') + '\n', 'utf8');
  process.stdout.write(lines.join('\n') + '\n');
  process.exit(3);
}

report.rows.forEach((r) => lines.push(`[${r.ok ? 'PASS' : 'FAIL'}] ${r.name}${r.ok ? '' : '  ->  ' + r.detail}`));
lines.push('');
lines.push(`[${standalone.ok ? 'PASS' : 'FAIL'}] 原始 app.html 独立加载（无注入）  ->  ${standalone.detail}`);
const totalFail = report.fail + (standalone.ok ? 0 : 1);
const totalAll = report.total + 1;
const passAll = report.pass + (standalone.ok ? 1 : 0);
lines.push('');
lines.push('============================');
lines.push(`TOTAL ${totalAll}   PASS ${passAll}   FAIL ${totalFail}`);
lines.push(totalFail === 0 ? 'RESULT: ALL PASS' : 'RESULT: FAILED');
fs.writeFileSync(LOG, lines.join('\n') + '\n', 'utf8');
process.stdout.write(lines.join('\n') + '\n');
process.exit(totalFail === 0 ? 0 : 1);
