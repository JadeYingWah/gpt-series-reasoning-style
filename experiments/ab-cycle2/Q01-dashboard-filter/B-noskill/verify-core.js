// 裁判 1/2：核心逻辑与边界（Node 环境，从 app.html 提取 /*<<CORE>>*/ 逻辑块直接执行）
// 用法：node verify-core.js [待测文件，默认 app.html]；退出码 0=全过，1=有失败
const fs = require('fs');
const TARGET = process.argv[2] || 'app.html';
const html = fs.readFileSync(TARGET, 'utf8');
const m = html.match(/\/\*<<CORE>>\*\/([\s\S]*?)\/\*<<\/CORE>>\*\//);
if (!m) { console.error('FATAL: 无法提取 CORE 逻辑块'); process.exit(1); }
const C = new Function(m[1] + '; return {RAW_ORDERS,sanitizeOrders,listRegions,filterOrders,computeSummary,groupByMonth,niceMax,formatMoney,formatCompact,safePct};')();

let pass = 0, fail = 0; const fails = [];
const eq = (n, g, w) => { if (JSON.stringify(g) === JSON.stringify(w)) pass++; else { fail++; fails.push(n + ' got=' + JSON.stringify(g) + ' want=' + JSON.stringify(w)); } };
const ok = (n, c, x) => { if (c) pass++; else { fail++; fails.push(n + (x ? ' | ' + x : '')); } };

// ---------- 1. 总览数字与实际数据一致（独立复算） ----------
const raw = C.RAW_ORDERS;
const clean = C.sanitizeOrders(raw);
eq('内嵌记录全部合法', clean.dropped, 0);
eq('清洗后条数', clean.orders.length, raw.length);
const s = C.computeSummary(clean.orders);
const handTotal = raw.reduce((a, b) => a + b.amount, 0);
eq('总销售额=独立求和', s.total, handTotal);
eq('订单数=记录条数', s.orders, raw.length);
eq('客单价=总额/订单数', s.avg, handTotal / raw.length);
ok('客单价有限', Number.isFinite(s.avg));
console.log('【实算·全部地区】总销售额=' + C.formatMoney(s.total) + ' 订单数=' + s.orders + ' 客单价=' + C.formatMoney(s.avg));

// ---------- 2. 地区筛选：数字卡与图表同步 ----------
const regions = C.listRegions(clean.orders);
eq('地区数=5', regions.length, 5);
eq('地区去重', regions.slice().sort().join(','), ['东北', '华东', '华北', '华南', '西南'].sort().join(','));
ok('地区排序稳定(拼音升序)', JSON.stringify(regions) === JSON.stringify([...regions].sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'))));
let sumOfParts = 0;
for (const r of regions) {
  const sub = C.filterOrders(clean.orders, [r]);
  const hand = raw.filter(o => o.region === r);
  eq('地区' + r + ' 订单数', sub.length, hand.length);
  const ss = C.computeSummary(sub);
  const handSum = hand.reduce((a, b) => a + b.amount, 0);
  eq('地区' + r + ' 总额', ss.total, handSum);
  eq('地区' + r + ' 客单价', ss.avg, handSum / hand.length);
  const rows = C.groupByMonth(sub);
  eq('地区' + r + ' 月聚合合计=数字卡总额', rows.reduce((a, b) => a + b.amount, 0), ss.total);
  sumOfParts += ss.total;
  console.log('  筛选 ' + r + ' → 订单' + ss.orders + '，总额' + C.formatMoney(ss.total) + '，客单价' + C.formatMoney(ss.avg) + '，' + rows.length + ' 个月');
}
eq('各地区总额之和=总额', sumOfParts, handTotal);
const sub2 = C.filterOrders(clean.orders, ['华东', '华南']);
eq('多选(华东+华南)总额=两块之和',
   C.computeSummary(sub2).total,
   C.computeSummary(C.filterOrders(clean.orders, ['华东'])).total + C.computeSummary(C.filterOrders(clean.orders, ['华南'])).total);
ok('筛选后总额<全量总额', C.computeSummary(sub2).total < s.total);

// ---------- 3. 柱状图数值与数据一致 ----------
const rowsAll = C.groupByMonth(clean.orders);
const handMonths = {};
raw.forEach(o => { handMonths[o.month] = (handMonths[o.month] || 0) + o.amount; });
eq('月份数', rowsAll.length, Object.keys(handMonths).length);
rowsAll.forEach(r => eq('月 ' + r.month + ' 聚合值', r.amount, handMonths[r.month]));
eq('月度合计=总额', rowsAll.reduce((a, b) => a + b.amount, 0), handTotal);
eq('月份升序', rowsAll.map(r => r.month).join(','), rowsAll.map(r => r.month).slice().sort().join(','));
const shuffled = [...clean.orders].reverse();
const rowsShuffled = C.groupByMonth(shuffled);
eq('乱序输入仍按月升序', rowsShuffled.map(r => r.month).join(','), rowsShuffled.map(r => r.month).slice().sort().join(','));
eq('乱序输入聚合值不变', rowsShuffled.map(r => r.amount).join(','), rowsAll.map(r => r.amount).join(','));
const dirtyMonths = C.groupByMonth([{ month: '2026-13', amount: 1 }, { month: null, amount: 2 }, { month: '2026-01', amount: 3 }, { amount: 4 }]);
eq('非法月份不进入图表', dirtyMonths.length, 1);
eq('非法月份金额不计入', dirtyMonths[0].amount, 3);
eq('含非法记录时只统计合法金额', C.computeSummary([{ amount: NaN }, { amount: 10 }, { amount: '20' }]).total, 30);
eq('含非法记录时订单数只算合法', C.computeSummary([{ amount: NaN }, { amount: 10 }, { amount: '20' }]).orders, 2);
const top = C.niceMax(Math.max(...rowsAll.map(r => r.amount)));
ok('轴上限>=最大月值', top >= Math.max(...rowsAll.map(r => r.amount)), 'top=' + top);
const asc = [...rowsAll].sort((a, b) => a.amount - b.amount);
const hs = asc.map(r => C.safePct(r.amount, top));
ok('柱高随数值单调不减', hs.every((h, i) => i === 0 || h >= hs[i - 1]), JSON.stringify(hs));
ok('柱高均在[0,100]', hs.every(h => h >= 0 && h <= 100));
ok('最高柱接近满格(>80%)', Math.max(...hs) > 80 && Math.max(...hs) <= 100, 'max=' + Math.max(...hs));
console.log('【实算·月度】' + rowsAll.map(r => r.label + '=' + C.formatMoney(r.amount)).join(' | ') + '  轴上限=' + C.formatCompact(top));

// ---------- 4. 空筛选结果 ----------
const emptyOrders = C.filterOrders(clean.orders, []);
eq('空选择→0 条', emptyOrders.length, 0);
const se = C.computeSummary(emptyOrders);
eq('空态 isEmpty', se.isEmpty, true);
eq('空态 total=0', se.total, 0);
ok('空态 avg 不是 NaN', Number.isFinite(se.avg));
eq('空态 avg=0', se.avg, 0);
eq('空态月聚合=[]', C.groupByMonth(emptyOrders), []);
eq('空态金额显示', C.formatMoney(se.total), '¥0.00');
eq('空态客单价显示', C.formatMoney(se.avg), '¥0.00');

// ---------- 5. 边界：非法输入（不抛未捕获异常） ----------
const junk = [null, undefined, 'abc', 123, {}, [], [null], [[]], [{}], [{region: '华东'}], [{amount: 1}], [{region: '华东', month: '2026-01'}], NaN, true, [{region: '华东', month: '2026-01', amount: NaN}], [null, {region: '华东', month: '2026-01', amount: 5}]];
let threw = null;
for (const j of junk) { try { C.sanitizeOrders(j); C.listRegions(j); C.groupByMonth(j); C.computeSummary(j); C.filterOrders(j, ['华东']); C.filterOrders(clean.orders, j); } catch (e) { threw = String(j) + ' -> ' + e.message; } }
ok('各类非法入参不抛错', threw === null, threw || '');
eq('sanitizeOrders("abc") 丢弃0', C.sanitizeOrders('abc').dropped, 0);
eq('sanitizeOrders([null,null]) 丢弃2', C.sanitizeOrders([null, null]).dropped, 2);
const bad = [
  { region: '华东', month: '2026-01', amount: NaN },
  { region: '华东', month: '2026-01', amount: Infinity },
  { region: '华东', month: '2026-01', amount: -500 },
  { region: '华东', month: '2026-01', amount: 'abc' },
  { region: '华东', month: '2026-01', amount: null },
  { region: '华东', month: '2026-01', amount: undefined },
  { region: '华东', month: '2026-13', amount: 100 },
  { region: '华东', month: '2026-1', amount: 100 },
  { region: '华东', month: '2026-00', amount: 100 },
  { region: '华东', month: '', amount: 100 },
  { region: '华东', month: null, amount: 100 },
  { region: '', month: '2026-01', amount: 100 },
  { region: '   ', month: '2026-01', amount: 100 },
  { region: null, month: '2026-01', amount: 100 },
  { region: 123, month: '2026-01', amount: 100 }
];
const bs = C.sanitizeOrders(bad);
eq('非法记录全部丢弃', bs.orders.length, 0);
eq('丢弃计数正确', bs.dropped, 15);
const okRows = C.sanitizeOrders([{ region: '华东', month: '2026-01', amount: '1000' }, { region: '华东', month: '2026-01', amount: 0 }]);
eq('数字字符串金额可容忍', okRows.orders.length, 2);
eq('字符串金额转数', okRows.orders[0].amount, 1000);
eq('0 金额合法', okRows.orders[1].amount, 0);
eq('负数被丢弃', C.sanitizeOrders([{ region: '华东', month: '2026-01', amount: -1 }]).orders.length, 0);
eq('NaN 被丢弃', C.sanitizeOrders([{ region: '华东', month: '2026-01', amount: NaN }]).orders.length, 0);
eq('未知地区筛选→空', C.filterOrders(clean.orders, ['火星']), []);
eq('filterOrders(o,null)→全部', C.filterOrders(clean.orders, null).length, raw.length);
eq('filterOrders(o,undefined)→全部', C.filterOrders(clean.orders, undefined).length, raw.length);
eq('filterOrders(o,"华东"非数组)→全部', C.filterOrders(clean.orders, '华东').length, raw.length);
eq('总计为0时客单价不产生NaN', Number.isFinite(C.computeSummary([]).avg), true);

// ---------- 6. 边界：超长文本 ----------
const longRegion = '超'.repeat(5000);
const longCustomer = '名'.repeat(20000);
const lc = C.sanitizeOrders([{ id: 'L1', region: longRegion, month: '2026-01', amount: 1, customer: longCustomer }]);
eq('超长文本记录保留', lc.orders.length, 1);
eq('数据层不截断(region)', lc.orders[0].region.length, 5000);
eq('数据层不截断(customer)', lc.orders[0].customer.length, 20000);
ok('超长文本参与聚合并通过', (() => { try { C.groupByMonth(lc.orders); C.computeSummary(lc.orders); return true; } catch (e) { return false; } })());
ok('CSS 对超长文本做省略处理', /text-overflow:\s*ellipsis/.test(html) && /min-width:\s*0/.test(html) && /word-break:\s*break-all/.test(html));
ok('地区标签设 max-width 限制', /\.chip\{[\s\S]*?max-width:\s*220px/.test(html) || /max-width:\s*220px/.test(html));

// ---------- 7. 格式化容错 ----------
[undefined, NaN, Infinity, null, 'abc', {}, []].forEach(v => eq('formatMoney(' + String(v) + ')=—', C.formatMoney(v), '—'));
[NaN, Infinity, 'abc'].forEach(v => eq('formatCompact(' + String(v) + ')=—', C.formatCompact(v), '—'));
eq('formatMoney(0)', C.formatMoney(0), '¥0.00');
eq('formatMoney(1234567.891)', C.formatMoney(1234567.891), '¥1,234,567.89');
eq('formatMoney(-5)', C.formatMoney(-5), '-¥5.00');
eq('formatCompact(0)', C.formatCompact(0), '¥0');
eq('formatCompact(128600)', C.formatCompact(128600), '¥12.9万');
eq('safePct(0,0)=0', C.safePct(0, 0), 0);
eq('safePct(5,0)=0', C.safePct(5, 0), 0);
eq('safePct(NaN,100)=0', C.safePct(NaN, 100), 0);
eq('safePct(-5,100)=0', C.safePct(-5, 100), 0);
eq('safePct(Infinity,100)=0', C.safePct(Infinity, 100), 0);
eq('safePct 上限钳制', C.safePct(200, 100), 100);
eq('niceMax(0)=0', C.niceMax(0), 0);
eq('niceMax(-1)=0', C.niceMax(-1), 0);
eq('niceMax(NaN)=0', C.niceMax(NaN), 0);

// ---------- 8. 静态/结构核对 ----------
ok('无外链 src/href/@import', !/\ssrc\s*=|\shref\s*=|@import/i.test(html));
ok('无 http(s) 字面量', html.indexOf('http://') < 0 && html.indexOf('https://') < 0);
ok('数字卡含三项指标', html.indexOf('总销售额') >= 0 && html.indexOf('订单数') >= 0 && html.indexOf('客单价') >= 0);
ok('空态文案存在', html.indexOf('没有符合条件的数据') >= 0);
ok('未用 innerHTML 注入数据', !/innerHTML\s*=/.test(html));
ok('有 try/catch 兜底与错误框', /catch\s*\(\s*err\s*\)/.test(html) && /id="errBox"/.test(html));
ok('柱高来自 safePct', /bar\.style\.height\s*=\s*safePct\(/.test(html));
ok('卡片值来自 computeSummary', /renderCards\(summary\)/.test(html));
ok('图表用筛选后数据', /renderChart\(groupByMonth\(picked\)\)/.test(html));
ok('筛选控件为可切换按钮组', /role="group"/.test(html) && /aria-pressed/.test(html));
ok('单文件：2 段 script、0 个 link', (html.match(/<script/g) || []).length === 2 && (html.match(/<link/g) || []).length === 0);
ok('设置了标题层级', /<h1/.test(html) && /<h2/.test(html) && /panel-title/.test(html));

console.log('#'.repeat(64));
console.log('PASS=' + pass + '  FAIL=' + fail);
if (fails.length) { console.log('--- FAILURES ---'); fails.forEach(f => console.log('  ' + f)); }
process.exit(fail ? 1 : 0);
