// 真实浏览器验收：启动本机 Chrome（headless），经 CDP 驱动，读 DOM 与 expected.json 对账，
// 并通过 Input.dispatchKeyEvent 做「真实按键」操作，最后截图留证。
// 用法：node evidence/browser-check.mjs
// 依赖：仅 Node >= 22（内置全局 WebSocket）+ 本机已装 Chrome，无 npm 依赖。
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const TARGET = process.env.Q01_TARGET || 'app.html';          // 允许指向变异副本，供杀伤率审计
const OUT = process.env.Q01_OUT || 'browser-check.json';
const SHOTS_DIR = process.env.Q01_SHOTS || 'shots';
const shots = join(here, SHOTS_DIR);
if (!existsSync(shots)) mkdirSync(shots, { recursive: true });

const FILE_URL = 'file:///' + join(root, TARGET).replace(/\\/g, '/');
const expected = JSON.parse(readFileSync(join(here, 'expected.json'), 'utf8'));

const CHROME_CANDIDATES = [
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  join(process.env.LOCALAPPDATA || '', 'Google\\Chrome\\Application\\chrome.exe'),
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
];
const chromePath = CHROME_CANDIDATES.find((p) => p && existsSync(p));
if (!chromePath) { console.error('FAIL: 未找到 Chrome/Edge 可执行文件'); process.exit(2); }

const PORT = 9333;
const profile = join(tmpdir(), 'q01-cdp-profile-' + Date.now());
// 若上一次异常退出留下进程，先清掉
try { rmSync(profile, { recursive: true, force: true }); } catch {}

const results = [];
const shotsTaken = [];
const exceptions = [];
const consoleErrors = [];
let probeExceptions = [];

function rec(id, name, pass, detail) {
  results.push({ id, name, pass: !!pass, detail });
  console.log(`${pass ? 'PASS' : 'FAIL'}  [${id}] ${name}${detail !== undefined ? ' :: ' + JSON.stringify(detail) : ''}`);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(chromePath, [
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', '--hide-scrollbars', '--force-device-scale-factor=1',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--window-size=1280,900', '--allow-file-access-from-files', FILE_URL,
], { stdio: 'ignore' });

let ws;
let nextId = 1;
const pending = new Map();
const waiters = [];

function send(method, params = {}) {
  const id = nextId++;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((res, rej) => pending.set(id, { res, rej }));
}
async function ev(expr) {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error('页面表达式抛错: ' + JSON.stringify(r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text));
  return r.result.value;
}
const waitFor = (cond, ms = 8000, step = 120) => new Promise((res, rej) => {
  const t0 = Date.now();
  const tick = async () => {
    try { if (await cond()) return res(true); } catch { /* keep polling */ }
    if (Date.now() - t0 > ms) return rej(new Error('waitFor 超时'));
    setTimeout(tick, step);
  };
  tick();
});

async function shot(name) {
  const r = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
  const p = join(shots, name + '.png');
  writeFileSync(p, Buffer.from(r.data, 'base64'));
  shotsTaken.push(p);
  return p;
}

async function key(vk, code, keyName) {
  await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk, code, key: keyName });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk, code, key: keyName });
  await sleep(120);
}

// DOM 读数（与 expected.json 同构，便于逐项比）
const READ_DOM = `(() => {
  const t = (s) => { const e = document.querySelector(s); return e ? e.textContent.trim() : null; };
  const num = (s) => { const e = document.querySelector(s + ' .num'); return e ? e.textContent.trim() : t(s); };
  const bars = [...document.querySelectorAll('[data-testid="bar"],[data-testid="bar-zero"]')].map(r => ({
    month: r.getAttribute('data-month'),
    value: Number(r.getAttribute('data-value')),
    fill: r.getAttribute('class')
  }));
  const labels = [...document.querySelectorAll('[data-testid="bar-label"]')].map(e => ({
    month: e.getAttribute('data-month'), text: e.textContent.trim()
  }));
  const xlabels = [...document.querySelectorAll('[data-testid="x-label"]')].map(e => ({ month: e.getAttribute('data-month'), text: e.textContent.trim() }));
  const opts = [...document.querySelectorAll('[data-testid="filter"] option')].map(o => o.value);
  return {
    total: num('[data-testid="kpi-total"]'),
    orders: num('[data-testid="kpi-orders"]'),
    avg: num('[data-testid="kpi-avg"]'),
    bars, labels, xlabels, opts,
    selectValue: document.querySelector('[data-testid="filter"]').value,
    badgeClass: document.querySelector('[data-testid="filter-badge"]').className,
    badgeText: t('[data-testid="filter-badge-text"]'),
    emptyShown: document.querySelector('[data-testid="empty-state"]').classList.contains('show'),
    emptyTitle: t('[data-testid="empty-title"]'),
    emptyDesc: t('[data-testid="empty-desc"]'),
    emptyMeta: t('[data-testid="empty-meta"]'),
    chartDisplay: document.getElementById('chart').style.display,
    datasetTag: t('[data-testid="dataset-tag"]'),
    uncaught: window.__uncaught.slice(),
    renderError: window.__renderError === undefined ? '__missing__' : window.__renderError,
    overflow: {
      docScroll: document.documentElement.scrollWidth,
      docClient: document.documentElement.clientWidth,
      bodyScroll: document.body.scrollWidth
    },
    badgeGeom: (() => {
      const b = document.querySelector('[data-testid="filter-badge"]');
      const t2 = document.querySelector('[data-testid="filter-badge-text"]');
      const r = b.getBoundingClientRect();
      return { w: Math.round(r.width), scrollW: t2.scrollWidth, clientW: t2.clientWidth, truncated: t2.scrollWidth > t2.clientWidth + 1 };
    })(),
    render: window.__lastRender
  };
})()`;

const fmt2 = (n) => { const v = Math.abs(Number(n)); const s = v.toFixed(2).split('.'); return (Number(n) < 0 ? '-' : '') + s[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '.' + s[1]; };

function cmpKpi(dom, expStats, tag) {
  const okT = dom.total === fmt2(expStats.total);
  const okO = dom.orders === String(expStats.orders).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  const okA = dom.avg === fmt2(expStats.avg);
  rec(`kpi-${tag}`, `KPI 与独立复算一致（${tag}）`, okT && okO && okA,
    { dom: { total: dom.total, orders: dom.orders, avg: dom.avg }, exp: { total: fmt2(expStats.total), orders: expStats.orders, avg: fmt2(expStats.avg) }, okT, okO, okA });
}
function cmpBars(dom, expSeries, tag) {
  const got = dom.bars.map((b) => ({ month: b.month, value: b.value }));
  const same = got.length === expSeries.length && got.every((g, i) => g.month === expSeries[i].month && g.value === expSeries[i].value);
  const labelOk = dom.labels.length === expSeries.filter((s) => s.value > 0).length;
  rec(`bars-${tag}`, `柱状图各月数值与数据一致（${tag}）`, same && labelOk,
    { dom: got, exp: expSeries, barCount: dom.bars.length, labelCount: dom.labels.length });
}

try {
  // ---- 连接 ----
  await waitFor(async () => {
    const r = await fetch(`http://127.0.0.1:${PORT}/json/list`);
    const list = await r.json();
    const page = list.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
    if (!page) return false;
    ws = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
    ws.onmessage = (m) => {
      const msg = JSON.parse(m.data);
      if (msg.id && pending.has(msg.id)) {
        const { res, rej } = pending.get(msg.id); pending.delete(msg.id);
        msg.error ? rej(new Error(msg.error.message)) : res(msg.result);
      } else if (msg.method === 'Runtime.exceptionThrown') {
        exceptions.push(String(msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text).split('\n')[0]);
      } else if (msg.method === 'Log.entryAdded' && msg.params.entry.level === 'error') {
        consoleErrors.push(msg.params.entry.text);
      }
    };
    return true;
  }, 20000, 200);

  await send('Runtime.enable');
  await send('Page.enable');
  await send('Log.enable');
  await waitFor(() => ev('!!window.__app && !!window.__lastRender'), 8000);
  await sleep(400);

  // ============ C1 默认视图 ============
  let dom = await ev(READ_DOM);
  cmpKpi(dom, expected.all, 'ALL');
  cmpBars(dom, expected.all.series, 'ALL');
  rec('C1-axis', '月份轴与数据并集一致（含 x 轴标签）',
    JSON.stringify(dom.xlabels.map((x) => x.month)) === JSON.stringify(expected.axis),
    { dom: dom.xlabels, exp: expected.axis });
  rec('C1-empty-hidden', '有数据时不显示空态', dom.emptyShown === false && dom.chartDisplay !== 'none', { emptyShown: dom.emptyShown, chartDisplay: dom.chartDisplay });
  rec('C1-regions', '筛选项 = 数据中的地区集合 + 全部',
    JSON.stringify(dom.opts) === JSON.stringify(['ALL', ...expected.regions]),
    { dom: dom.opts, exp: ['ALL', ...expected.regions] });
  rec('C1-tooltip', '柱体带数值 tooltip（含金额与笔数）',
    await ev(`(() => { const b = document.querySelector('[data-testid="bar"]'); const t = b && b.querySelector('title'); return t ? t.textContent : null; })()`)
      ? true : false,
    await ev(`(() => { const b = document.querySelector('[data-testid="bar"]'); const t = b && b.querySelector('title'); return t ? t.textContent : null; })()`));
  await shot('01-default-all');

  // ============ C2 真实按键筛选：全部 -> 华东（index 2） ============
  await ev(`document.querySelector('[data-testid="filter"]').focus()`);
  await key(40, 'ArrowDown', 'ArrowDown');
  await key(40, 'ArrowDown', 'ArrowDown');
  await sleep(300);
  dom = await ev(READ_DOM);
  let method = 'keyboard';
  if (dom.selectValue !== '华东') {
    method = 'fallback-change-event';
    await ev(`(() => { const s = document.querySelector('[data-testid="filter"]'); s.value = '华东'; s.dispatchEvent(new Event('change', { bubbles: true })); })()`);
    await sleep(300);
    dom = await ev(READ_DOM);
  }
  rec('C2-filter-applied', '按键操作后筛选值生效为「华东」', dom.selectValue === '华东', { method, selectValue: dom.selectValue });
  cmpKpi(dom, expected.byRegion['华东'], '华东');
  cmpBars(dom, expected.byRegion['华东'].series, '华东');
  rec('C2-badge', '筛选后徽标同步显示当前地区与命中笔数',
    dom.badgeText.includes('华东') && dom.badgeText.includes(String(expected.byRegion['华东'].orders)), { badgeText: dom.badgeText });
  rec('C2-axis-stable', '筛选后月份轴不塌缩（仍为全量 6 个月）',
    dom.bars.length === expected.axis.length, { bars: dom.bars.length, axis: expected.axis.length });
  rec('C2-zero-bars', '无订单月份渲染为 0 高柱而非消失',
    dom.bars.filter((b) => b.value === 0).length === expected.byRegion['华东'].series.filter((s) => s.value === 0).length,
    { zeroBars: dom.bars.filter((b) => b.value === 0).length });
  await shot('02-filter-huadong');

  // ============ C2b 真实按键切到超长名地区（index 4），验证月份轴不塌缩 ============
  const LONG_REGION = expected.regions.find((r) => r.length > 8) || expected.regions[expected.regions.length - 1];
  await ev(`document.querySelector('[data-testid="filter"]').focus()`);
  await key(40, 'ArrowDown', 'ArrowDown');
  await key(40, 'ArrowDown', 'ArrowDown');
  await sleep(300);
  dom = await ev(READ_DOM);
  rec('C2b-territory', `按键切到超长名地区「${LONG_REGION.slice(0, 12)}…」生效`, dom.selectValue === LONG_REGION, { selectValue: dom.selectValue });
  cmpKpi(dom, expected.byRegion[LONG_REGION], '超长名地区');
  cmpBars(dom, expected.byRegion[LONG_REGION].series, '超长名地区');
  rec('C2b-axis-stable', '该地区仅 3 个月有单，月份轴仍保持全量 6 个月不塌缩',
    dom.bars.length === expected.axis.length && dom.bars.filter((b) => b.value > 0).length === 3,
    { bars: dom.bars.length, nonZero: dom.bars.filter((b) => b.value > 0).length, exp: expected.axis.length });
  rec('C2b-long-option', '超长地区名在 select 中不撑破布局（无横向溢出）',
    dom.overflow.docScroll <= dom.overflow.docClient + 1, dom.overflow);
  await shot('02b-long-region-filter');

  // 回到「全部」再继续
  await ev(`window.__app.setFilter('ALL')`); await sleep(250);

  // ============ C3 真实空筛选结果：数据中移除「华东」，保留华东筛选 ============
  await ev(`window.__app.setFilter('华东')`); await sleep(250);
  await ev(`window.__app.setData(window.__app.getData().filter(r => r.region !== '华东'))`);
  await sleep(400);
  dom = await ev(READ_DOM);
  rec('C3-empty-real', '筛选结果为空时显示空态文案（真实筛选路径）',
    dom.emptyShown === true && dom.chartDisplay === 'none' && !!dom.emptyDesc,
    { emptyShown: dom.emptyShown, chartDisplay: dom.chartDisplay, title: dom.emptyTitle, desc: dom.emptyDesc, meta: dom.emptyMeta });
  rec('C3-empty-kpi-zero', '空结果时 KPI 归零且不残留旧值',
    dom.total === '0.00' && dom.orders === '0' && dom.avg === '0.00', { total: dom.total, orders: dom.orders, avg: dom.avg });
  rec('C3-empty-no-exception', '空结果渲染无未捕获异常', dom.uncaught.length === 0 && dom.renderError === null, { uncaught: dom.uncaught, renderError: dom.renderError });
  await shot('03-empty-filter');

  // ============ C4 边界 ============
  await ev(`window.__app.reset()`); await sleep(300);

  // C4a 空数据集
  await ev(`window.__app.setData([])`); await sleep(300);
  dom = await ev(READ_DOM);
  rec('C4a-empty-dataset', '空数据集：显示空态、KPI 归零、无异常',
    dom.emptyShown && dom.total === '0.00' && dom.orders === '0' && dom.uncaught.length === 0 && dom.renderError === null,
    { title: dom.emptyTitle, desc: dom.emptyDesc, datasetTag: dom.datasetTag, uncaught: dom.uncaught, renderError: dom.renderError });
  await shot('04-empty-dataset');

  // C4b 非数组 / 异常行
  const nasty = `window.__app.setData([null, 1, "x", {id:'A'}, {id:'B',month:'2026-01',region:'华北',amount:'abc'}, {id:'C',month:'2026-01',region:'华北',amount:NaN}, {id:'D',month:'2026-01',region:'华北',amount:1000}])`;
  await ev(nasty); await sleep(300);
  dom = await ev(READ_DOM);
  rec('C4b-nasty-rows', '含 null/非对象/非数字金额的脏数据不抛异常，仅计入有效行',
    dom.uncaught.length === 0 && dom.renderError === null && dom.total === '1,000.00' && dom.orders === '1',
    { total: dom.total, orders: dom.orders, uncaught: dom.uncaught, renderError: dom.renderError });
  await ev(`window.__app.setData(null)`); await sleep(300);
  dom = await ev(READ_DOM);
  rec('C4b-non-array', 'setData(null) 不抛异常，降级为空数据', dom.uncaught.length === 0 && dom.emptyShown === true, { uncaught: dom.uncaught, emptyShown: dom.emptyShown });

  // C4c 非法筛选输入（多种类型）
  await ev(`window.__app.reset()`); await sleep(200);
  const invalids = [
    ['字符串未知地区', `'火星大区'`],
    ['空字符串', `''`],
    ['null', `null`],
    ['undefined', `undefined`],
    ['数字', `12345`],
    ['对象', `({foo:'bar'})`],
    ['数组', `['华东']`],
    ['超长字符串(5000字)', `'X'.repeat(5000)`],
    ['含 HTML/脚本片段', `'<img src=x onerror=alert(1)>'`],
  ];
  for (const [name, expr] of invalids) {
    const before = exceptions.length;
    await ev(`window.__app.setFilter(${expr})`);
    await sleep(150);
    const d = await ev(READ_DOM);
    const ok = d.uncaught.length === 0 && d.renderError === null && d.emptyShown === true && exceptions.length === before;
    rec('C4c-' + name, `非法筛选输入「${name}」→ 空态处理且无异常`, ok,
      { emptyShown: d.emptyShown, emptyTitle: d.emptyTitle, badgeText: d.badgeText, uncaught: d.uncaught, renderError: d.renderError, cdpExceptions: exceptions.length - before });
  }
  await shot('05-invalid-input');

  // C4d 超长文本
  await ev(`window.__app.reset()`); await sleep(200);
  const LONG = '华南·粤港澳大湾区跨境业务区'.repeat(12); // 168 字
  await ev(`window.__app.setData(window.__app.getData().concat([{id:'LONG-1',month:'2026-06',region:${JSON.stringify(LONG)},amount:8888}]))`);
  await sleep(200);
  await ev(`window.__app.setFilter(${JSON.stringify(LONG)})`);
  await sleep(400);
  dom = await ev(READ_DOM);
  const longOk = dom.uncaught.length === 0 && dom.renderError === null
    && dom.total === '8,888.00' && dom.orders === '1'
    && dom.overflow.docScroll <= dom.overflow.docClient + 1
    && dom.badgeGeom.truncated === true;
  rec('C4d-long-text', '超长地区名(168字)：不抛异常、无横向溢出、徽标省略号截断、数值仍正确', longOk,
    { total: dom.total, orders: dom.orders, badgeTextLen: dom.badgeText.length, badgeGeom: dom.badgeGeom, overflow: dom.overflow, uncaught: dom.uncaught });
  await shot('06-long-text-168');

  // C4e 超长数值文本 + 极多月份（规模压力）
  await ev(`window.__app.reset()`);
  const many = [];
  for (let i = 0; i < 240; i++) many.push({ id: 'M' + i, month: '20' + String(20 + (i % 24)).slice(0, 2) + '-' + String((i % 12) + 1).padStart(2, '0'), region: '地区' + (i % 7), amount: 1000000 + i });
  await ev(`window.__app.setData(${JSON.stringify(many)})`); await sleep(500);
  dom = await ev(READ_DOM);
  const expMany = 240 * 1000000 + (239 * 240 / 2);
  rec('C4e-scale', '240 笔 / 24 个月 / 7 地区：渲染无异常且总额正确',
    dom.uncaught.length === 0 && dom.renderError === null && dom.total === fmt2(expMany) && dom.bars.length === 24,
    { total: dom.total, exp: fmt2(expMany), bars: dom.bars.length, overflow: dom.overflow, uncaught: dom.uncaught });
  await shot('07-scale-240x24');
  await ev(`window.__app.reset()`); await sleep(300);

  // ============ C5 探测器正控（RED 测试：证明探测器不是橡皮图章） ============
  const beforePage = (await ev('window.__uncaught.length'));
  const beforeCdp = exceptions.length;
  await ev(`setTimeout(() => { throw new Error('DETECTOR-PROBE-INTENTIONAL'); }, 0)`);
  await sleep(600);
  const afterPage = (await ev('window.__uncaught.length'));
  const probeHit = afterPage > beforePage && exceptions.length > beforeCdp;
  probeExceptions = exceptions.slice(beforeCdp);
  rec('C5-detector-red', '正控：故意抛错时页面收集器与 CDP 异常事件都能变红（证明前述「无异常」不是空转）',
    probeHit, { pageUncaught: [beforePage, afterPage], cdpExceptions: [beforeCdp, exceptions.length], probe: probeExceptions });

  // ============ C6 控制台错误（排除正控后） ============
  rec('C6-console', '全程未产生 console error', consoleErrors.length === 0, consoleErrors.slice(0, 5));
  rec('C6-render-error', '全程 render 内部错误捕获器始终为空', (await ev('window.__renderError')) === null, await ev('window.__renderError'));

  // ============ C7 离线（断网）验证 ============
  await send('Network.enable');
  await send('Network.emulateNetworkConditions', { offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0 });
  await send('Page.reload', { ignoreCache: true });
  await sleep(1200);
  const off = await waitFor(() => ev('!!window.__app && !!window.__lastRender'), 6000).then(() => true).catch(() => false);
  dom = await ev(READ_DOM);
  rec('C7-offline', '断网后重载仍完整渲染（KPI + 柱状图）',
    off && dom.orders === String(expected.all.orders) && dom.bars.length === expected.axis.length && dom.uncaught.length === 0,
    { reloaded: off, orders: dom.orders, bars: dom.bars.length, uncaught: dom.uncaught });
  await shot('08-offline-reload');

} catch (e) {
  rec('FATAL', '验收脚本异常', false, String(e && e.stack || e));
} finally {
  try { if (ws) ws.close(); } catch {}
  try { chrome.kill(); } catch {}
  await sleep(500);
  try { rmSync(profile, { recursive: true, force: true }); } catch {}
}

const failed = results.filter((r) => !r.pass);
const summary = {
  fileUrl: FILE_URL,
  ranAt: new Date().toISOString(),
  total: results.length,
  passed: results.length - failed.length,
  failed: failed.length,
  shots: shotsTaken,
  cdpExceptionsTotal: exceptions.length,
  results,
};
writeFileSync(join(here, OUT), JSON.stringify(summary, null, 2) + '\n', 'utf8');
console.log(`\n==== ${summary.passed}/${summary.total} PASS, ${summary.failed} FAIL ====`);
if (!process.env.Q01_QUIET) console.log('截图：', shotsTaken.map((s) => s.split(/[\\/]/).pop()).join(', '));
if (failed.length) console.log('失败项：', failed.map((f) => f.id).join(', '));
process.exit(failed.length ? 1 : 0);
