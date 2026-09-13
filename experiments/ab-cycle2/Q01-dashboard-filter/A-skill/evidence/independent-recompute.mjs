// 独立复算：从 app.html 抽取内嵌数据，用**独立于页面逻辑**的实现重算全部期望值。
// 目的：与浏览器 DOM 渲染值对账 —— 两份独立实现 + DOM 读取，三者一致才算「数值与数据一致」。
// 用法：node evidence/independent-recompute.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const raw = readFileSync(join(root, 'app.html'), 'utf8');

const m = raw.match(/DATA:BEGIN[\s\S]*?const DATA = (\[[\s\S]*?\]);[\s\S]*?DATA:END/);
if (!m) { console.error('FAIL: 未能从 app.html 抽取 DATA 块'); process.exit(1); }
const DATA = JSON.parse(m[1]);

// ---- 独立实现（不复用页面函数）----
const round2 = (n) => Math.round(n * 100) / 100;
const stats = (rows) => {
  const orders = rows.length;
  const total = round2(rows.reduce((a, r) => a + r.amount, 0));
  return { total, orders, avg: orders ? round2(total / orders) : 0 };
};
const axis = [...new Set(DATA.map((r) => r.month))].sort();
const byMonth = (rows) => axis.map((mo) => ({ month: mo, value: round2(rows.filter((r) => r.month === mo).reduce((a, r) => a + r.amount, 0)) }));
const regions = [...new Set(DATA.map((r) => r.region))].sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'));

const expect = {
  source: 'evidence/independent-recompute.mjs',
  dataRows: DATA.length,
  axis,
  regions,
  all: { ...stats(DATA), series: byMonth(DATA) },
  byRegion: Object.fromEntries(
    regions.map((g) => {
      const rows = DATA.filter((r) => r.region === g);
      return [g, { ...stats(rows), series: byMonth(rows) }];
    })
  ),
};

// 数据自检（防止我手写的数据本身有重复 id / 非法金额）
const ids = DATA.map((r) => r.id);
const dupIds = ids.filter((v, i) => ids.indexOf(v) !== i);
const badAmount = DATA.filter((r) => !Number.isFinite(r.amount));
const badMonth = DATA.filter((r) => !/^\d{4}-\d{2}$/.test(r.month || ''));
const badRegion = DATA.filter((r) => typeof r.region !== 'string' || !r.region);
expect.dataSelfCheck = {
  dupIds,
  badAmountCount: badAmount.length,
  badMonthCount: badMonth.length,
  badRegionCount: badRegion.length,
};

const outPath = join(here, 'expected.json');
writeFileSync(outPath, JSON.stringify(expect, null, 2) + '\n', 'utf8');

console.log('rows =', expect.dataRows);
console.log('axis =', axis.join(','));
console.log('regions =', regions.map((r) => JSON.stringify(r)).join(' | '));
console.log('ALL  total =', expect.all.total, ' orders =', expect.all.orders, ' avg =', expect.all.avg);
console.log('ALL  series =', JSON.stringify(expect.all.series));
for (const g of regions) {
  const s = expect.byRegion[g];
  console.log(`[${g}] total = ${s.total}  orders = ${s.orders}  avg = ${s.avg}`);
}
console.log('dataSelfCheck =', JSON.stringify(expect.dataSelfCheck));
console.log('written ->', outPath);
