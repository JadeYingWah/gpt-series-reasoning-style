// 路径1（Node 独立复算）：从 index.html 提取内联数据与页面脚本，
// 独立计算 5 个筛选态的期望指标，输出 out_node.json，并落盘提取的页面脚本供语法检查。
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(__dirname);
const html = readFileSync(path.join(ROOT, 'index.html'), 'utf8');

const sm = html.match(/<script>([\s\S]*?)<\/script>/);
if (!sm){ console.error('FAIL: no <script> block found'); process.exit(1); }
writeFileSync(path.join(__dirname, 'page_script_extracted.js'), sm[1]);

const data = [];
const re = /m:"([^"]+)",\s*v:(\d+)/g;
let m;
while ((m = re.exec(html)) !== null) data.push({ m: m[1], v: Number(m[2]) });
if (data.length !== 12){ console.error('FAIL: expected 12 months, got ' + data.length); process.exit(1); }

const RANGES = { all:[0,11], q1:[0,2], q2:[3,5], q3:[6,8], q4:[9,11] };
const fmtInt = n => { let s = String(n), o = ''; while (s.length > 3){ o = ',' + s.slice(-3) + o; s = s.slice(0, -3); } return s + o; };
const fmtAvg = n => (Math.round(n * 10) / 10).toFixed(1);

const out = {};
for (const key of Object.keys(RANGES)){
  const [a, b] = RANGES[key];
  const rows = data.slice(a, b + 1);
  let total = 0, peak = rows[0];
  for (const r of rows){ total += r.v; if (r.v > peak.v) peak = r; }
  out[key] = {
    count: rows.length, total, avg: total / rows.length,
    peakMonth: peak.m, peakValue: peak.v,
    months: rows.map(r => r.m), values: rows.map(r => r.v),
    expect: {
      kpiTotal: fmtInt(total) + ' 万元',
      kpiAvg: fmtAvg(total / rows.length) + ' 万元/月',
      kpiPeak: peak.m + peak.v + ' 万元',
      bars: rows.length,
      barValues: rows.map(r => r.v),
    },
  };
}
writeFileSync(path.join(__dirname, 'out_node.json'), JSON.stringify(out, null, 2));
console.log('OK compute_node: all=' + out.all.expect.kpiTotal + ' avg=' + out.all.expect.kpiAvg + ' peak=' + out.all.expect.kpiPeak);
