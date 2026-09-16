// 路径4（真实浏览器 headless 渲染校验，最保守路径）：
// 用 Edge（回退 Chrome）--headless --dump-dom 逐个加载 5 个筛选态（通过 ?scope= 让页面在真实浏览器中直接进入对应状态），
// 保存渲染后的 DOM 快照到 out_render/，并断言去标签文本中包含期望的指标卡三值与图表标题、
// data-v 序列与期望柱值一致。渲染缺失（如脚本致命错误导致卡片停留在"–"）会直接 FAIL。
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(__dirname);
const htmlPath = path.join(ROOT, 'index.html');
const html = readFileSync(htmlPath, 'utf8');

/* ---- 独立期望值（第 4 份独立实现） ---- */
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

const candidates = [
  process.env.HEADLESS_BROWSER,
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
].filter(Boolean);
const browser = candidates.find(p => existsSync(p));
if (!browser){ console.error('FAIL: no Edge/Chrome found'); process.exit(1); }

const outDir = path.join(__dirname, 'out_render');
mkdirSync(outDir, { recursive: true });
const fileUrl = 'file:///' + htmlPath.replace(/\\/g, '/');

const results = { browser, dumps: {} };
let failed = false;
for (const key of ['all','q1','q2','q3','q4']){
  const url = key === 'all' ? fileUrl : fileUrl + '?scope=' + key;
  let dump = '';
  const baseArgs = ['--disable-gpu', '--no-first-run', '--no-default-browser-check',
                    '--virtual-time-budget=4000', '--dump-dom', url];
  try {
    dump = execFileSync(browser, ['--headless=new', ...baseArgs],
      { encoding: 'utf8', timeout: 60000, stdio: ['ignore', 'pipe', 'pipe'] });
  } catch (e1) {
    dump = execFileSync(browser, ['--headless', ...baseArgs],
      { encoding: 'utf8', timeout: 60000, stdio: ['ignore', 'pipe', 'pipe'] });
  }
  writeFileSync(path.join(outDir, 'scope-' + key + '.html'), dump);
  const text = dump.replace(/<[^>]+>/g, '');
  const exp = expected(key);
  const problems = [];
  if (!text.includes(exp.kpiTotal)) problems.push('kpiTotal missing: ' + JSON.stringify(exp.kpiTotal));
  if (!text.includes(exp.kpiAvg)) problems.push('kpiAvg missing: ' + JSON.stringify(exp.kpiAvg));
  if (!text.includes(exp.kpiPeak)) problems.push('kpiPeak missing: ' + JSON.stringify(exp.kpiPeak));
  if (!text.includes(exp.title)) problems.push('title missing: ' + JSON.stringify(exp.title));
  const dv = [...dump.matchAll(/data-v="(\d+)"/g)].map(x => Number(x[1]));
  if (dv.length !== exp.bars) problems.push(`bar count: got=${dv.length} want=${exp.bars}`);
  if (JSON.stringify(dv) !== JSON.stringify(exp.barValues)) problems.push(`barValues: got=${JSON.stringify(dv)} want=${JSON.stringify(exp.barValues)}`);
  if (problems.length) failed = true;
  results.dumps[key] = { url, ok: problems.length === 0, problems, snapshot: 'out_render/scope-' + key + '.html' };
}

writeFileSync(path.join(__dirname, 'out_browser.json'), JSON.stringify(results, null, 2));
console.log((failed ? 'FAIL' : 'OK') + ` browser_check: 5 个筛选态真实渲染校验（${browser}）`);
if (failed) process.exit(1);
