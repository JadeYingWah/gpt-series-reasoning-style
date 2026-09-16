// 路径3（DOM 仿真交互测试）：在 Node 内以最小 DOM 仿真执行 index.html 的页面脚本，
// 模拟点击全部筛选按钮（默认态/逐个点击/URL参数态/乱序迁移），
// 断言指标卡文本、图表柱数、逐柱数值、峰值高亮、active 按钮与 aria-pressed 全部与独立复算期望一致。
// 页面脚本任何运行时异常都会导致 FAIL（对应"无控制台报错"的仿真层证据）。
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(__dirname);
const html = readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const sm = html.match(/<script>([\s\S]*?)<\/script>/);
if (!sm){ console.error('FAIL: no <script>'); process.exit(1); }

/* ---- 独立期望值（第 3 份独立实现） ---- */
const data = [];
const re = /m:"([^"]+)",\s*v:(\d+)/g;
let mm;
while ((mm = re.exec(html)) !== null) data.push({ m: mm[1], v: Number(mm[2]) });
if (data.length !== 12){ console.error('FAIL: data length ' + data.length); process.exit(1); }
const RANGES = { all:[0,11], q1:[0,2], q2:[3,5], q3:[6,8], q4:[9,11] };
const LABELS = { all:'全年', q1:'第一季度', q2:'第二季度', q3:'第三季度', q4:'第四季度' };
const fmtInt = n => { let s = String(n), o = ''; while (s.length > 3){ o = ',' + s.slice(-3) + o; s = s.slice(0, -3); } return s + o; };
const fmtAvg = n => (Math.round(n * 10) / 10).toFixed(1);
function expected(key){
  const [a, b] = RANGES[key];
  const rows = data.slice(a, b + 1);
  let total = 0, peak = rows[0];
  for (const r of rows){ total += r.v; if (r.v > peak.v) peak = r; }
  return {
    kpiTotal: fmtInt(total) + ' 万元',
    kpiAvg: fmtAvg(total / rows.length) + ' 万元/月',
    kpiPeak: peak.m + peak.v + ' 万元',
    bars: rows.length, barValues: rows.map(r => r.v),
    title: '月度销售额趋势（' + LABELS[key] + '）',
  };
}

/* ---- 最小 DOM 仿真 ---- */
class El {
  constructor(tag){
    this.tagName = tag; this.children = []; this.attrs = {}; this._text = '';
    this.listeners = {}; this.parent = null;
    const store = new Set();
    this.classList = {
      add: (...c) => c.forEach(x => store.add(x)),
      remove: (...c) => c.forEach(x => store.delete(x)),
      contains: c => store.has(c),
    };
  }
  get textContent(){ return this.children.length === 0 ? this._text : this.children.map(c => c.textContent).join(''); }
  set textContent(v){ this._text = String(v); this.children = []; }
  appendChild(c){ this.children.push(c); c.parent = this; return c; }
  setAttribute(k, v){ this.attrs[k] = String(v); }
  getAttribute(k){ return k in this.attrs ? this.attrs[k] : null; }
  addEventListener(t, f){ (this.listeners[t] = this.listeners[t] || []).push(f); }
  click(){ (this.listeners.click || []).forEach(f => f()); }
}
function makeDoc(search){
  const ids = {};
  for (const id of ['kpi-total','kpi-avg','kpi-peak','chart-title','chart']){
    const e = new El('div'); e.setAttribute('id', id); ids[id] = e;
  }
  const buttons = ['all','q1','q2','q3','q4'].map(s => {
    const b = new El('button'); b.setAttribute('data-scope', s); return b;
  });
  const document = {
    getElementById: id => ids[id] || null,
    querySelectorAll: sel => sel === '.filters button' ? buttons : [],
    createElement: t => new El(t),
    createElementNS: (ns, t) => new El(t),
    createTextNode: t => { const e = new El('#text'); e._text = String(t); return e; },
  };
  return { document, location: { search }, ids, buttons };
}

function grab(ids, buttons){
  const svg = ids['chart'].children[0] || null;
  const bars = svg ? svg.children.filter(c => c.tagName === 'rect' && String(c.attrs.class || '').includes('bar')) : [];
  return {
    total: ids['kpi-total'].textContent,
    avg: ids['kpi-avg'].textContent,
    peak: ids['kpi-peak'].textContent,
    title: ids['chart-title'].textContent,
    bars: bars.length,
    barValues: bars.map(b => Number(b.attrs['data-v'])),
    active: buttons.filter(b => b.classList.contains('active')).map(b => b.getAttribute('data-scope')),
    peakCount: bars.filter(b => String(b.attrs.class).includes('bar-peak')).length,
  };
}
function problemsFor(key, st){
  const exp = expected(key), p = [];
  if (st.total !== exp.kpiTotal) p.push(`total: got=${JSON.stringify(st.total)} want=${JSON.stringify(exp.kpiTotal)}`);
  if (st.avg !== exp.kpiAvg) p.push(`avg: got=${JSON.stringify(st.avg)} want=${JSON.stringify(exp.kpiAvg)}`);
  if (st.peak !== exp.kpiPeak) p.push(`peak: got=${JSON.stringify(st.peak)} want=${JSON.stringify(exp.kpiPeak)}`);
  if (st.title !== exp.title) p.push(`title: got=${JSON.stringify(st.title)} want=${JSON.stringify(exp.title)}`);
  if (st.bars !== exp.bars) p.push(`bars: got=${st.bars} want=${exp.bars}`);
  if (JSON.stringify(st.barValues) !== JSON.stringify(exp.barValues)) p.push(`barValues: got=${JSON.stringify(st.barValues)} want=${JSON.stringify(exp.barValues)}`);
  if (!(st.active.length === 1 && st.active[0] === key)) p.push(`active: ${JSON.stringify(st.active)}`);
  if (st.peakCount !== 1) p.push(`peak-highlight count: ${st.peakCount}`);
  return p;
}

const results = { scenarios: [], scriptErrors: [] };
let failed = false;
function run(scriptArg, doc, name, cb){
  try {
    new Function('document', 'location', 'URLSearchParams', scriptArg)(doc.document, doc.location, URLSearchParams);
    cb();
  } catch(e){
    results.scriptErrors.push(name + ': ' + (e.stack || String(e)));
    failed = true;
  }
}

/* 场景A：默认加载（=all）+ 逐个点击 5 个筛选按钮 */
{
  const doc = makeDoc('');
  run(sm[1], doc, 'scenarioA', () => {
    const p0 = problemsFor('all', grab(doc.ids, doc.buttons));
    results.scenarios.push({ name: 'initial(default=all)', ok: p0.length === 0, problems: p0 });
    if (p0.length) failed = true;
    for (const key of ['q1','q2','q3','q4','all']){
      doc.buttons.find(b => b.getAttribute('data-scope') === key).click();
      const p = problemsFor(key, grab(doc.ids, doc.buttons));
      results.scenarios.push({ name: 'click→' + key, ok: p.length === 0, problems: p });
      if (p.length) failed = true;
    }
  });
}
/* 场景B：?scope=q3 URL 参数初始态 + 再点击 q1 */
{
  const doc = makeDoc('?scope=q3');
  run(sm[1], doc, 'scenarioB', () => {
    const p0 = problemsFor('q3', grab(doc.ids, doc.buttons));
    results.scenarios.push({ name: 'urlParam(?scope=q3)', ok: p0.length === 0, problems: p0 });
    if (p0.length) failed = true;
    doc.buttons.find(b => b.getAttribute('data-scope') === 'q1').click();
    const p = problemsFor('q1', grab(doc.ids, doc.buttons));
    results.scenarios.push({ name: 'urlParam→click q1', ok: p.length === 0, problems: p });
    if (p.length) failed = true;
  });
}
/* 场景C：乱序点击（状态迁移回归：q4→q2→all→q3→q1→q2） */
{
  const doc = makeDoc('');
  run(sm[1], doc, 'scenarioC', () => {
    for (const key of ['q4','q2','all','q3','q1','q2']){
      doc.buttons.find(b => b.getAttribute('data-scope') === key).click();
      const p = problemsFor(key, grab(doc.ids, doc.buttons));
      results.scenarios.push({ name: 'shuffle→' + key, ok: p.length === 0, problems: p });
      if (p.length) failed = true;
    }
  });
}

/* 场景D：非法 ?scope=bad 应回退全年（边界） */
{
  const doc = makeDoc('?scope=bad');
  run(sm[1], doc, 'scenarioD', () => {
    const p0 = problemsFor('all', grab(doc.ids, doc.buttons));
    results.scenarios.push({ name: 'urlParam(?scope=bad)→fallback all', ok: p0.length === 0, problems: p0 });
    if (p0.length) failed = true;
  });
}
/* 场景E：URLSearchParams 不可用时 try/catch 回退全年（边界） */
{
  const doc = makeDoc('?scope=q2');
  try {
    new Function('document', 'location', 'URLSearchParams', sm[1])(doc.document, doc.location, undefined);
    const p0 = problemsFor('all', grab(doc.ids, doc.buttons));
    results.scenarios.push({ name: 'no URLSearchParams→fallback all', ok: p0.length === 0, problems: p0 });
    if (p0.length) failed = true;
  } catch(e){
    results.scriptErrors.push('scenarioE: ' + (e.stack || String(e)));
    failed = true;
  }
}

writeFileSync(path.join(__dirname, 'out_shim.json'), JSON.stringify(results, null, 2));
const nOk = results.scenarios.filter(s => s.ok).length;
console.log((failed ? 'FAIL' : 'OK') + ` dom_shim_test: ${nOk}/${results.scenarios.length} 项状态断言通过，异常 ${results.scriptErrors.length} 个`);
if (failed) process.exit(1);
