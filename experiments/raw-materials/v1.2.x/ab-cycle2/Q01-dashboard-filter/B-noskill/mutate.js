// 变异测试脚本：对 app.html 注入缺陷，验证两个裁判（verify-core.js / verify-e2e.js）确实有杀伤力
// 用法：node mutate.js [裁判1] [裁判2] ...   （默认 verify-core.js）
// 说明：仅 exit=1 计为"杀死"；exit=2 视为裁判自身故障（Chrome 未起来等），该次判定作废
const fs = require('fs');
const { execFileSync } = require('child_process');
const original = fs.readFileSync('app.html', 'utf8');

const MUTANTS = [
  ['M1 客单价分子分母错配(total+=a 但 n=orders.length)', 'total += a; n++;', 'total += a; n = orders.length;'],
  ['M2 月份不再排序', '  keys.sort();\n  return keys.map', '  return keys.map'],
  ['M3 柱高上限钳制失效', 'return Math.min(100, p);', 'return p;'],
  ['M4 空选择被当作"全部"', 'if (selected.length === 0) return [];', 'if (selected.length === 0) return orders.filter(function(o){ return !!o; });'],
  ['M5 金额千分位分隔失效', "s[0] = s[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, \",\");", "s[0] = s[0];"],
  ['M6 非法月份记录混入图表', 'if (!o || !isMonthKey(o.month)) continue;', 'if (!o) continue;'],
  ['M7 汇总不再跳过非法金额', 'var a = o ? toAmount(o.amount) : null;\n    if (a === null) continue;\n    total += a; n++;', 'total += o.amount; n++;'],
  ['M8 筛选忽略地区条件(全返回)', "return orders.filter(function(o){ return !!o && set[o.region] === 1; });", 'return orders.filter(function(o){ return !!o; });'],
  ['M9 空态判定失效(isEmpty 恒 false)', 'var EMPTY = { total:0, orders:0, avg:0, isEmpty:true };', 'var EMPTY = { total:0, orders:0, avg:0, isEmpty:false };'],
  ['M10 柱高归零', 'bar.style.height = safePct(r.amount, top).toFixed(2) + "%";', 'bar.style.height = "0%";'],
  ['M11 图表使用原始未筛选数据', 'renderChart(groupByMonth(picked));', 'renderChart(groupByMonth(orders));'],
  ['M12 数字卡使用未筛选数据', 'renderCards(summary);', 'renderCards(computeSummary(orders));'],
  ['M13 静默吞掉非法记录提示', 'st.appendChild(span(" · 已忽略 " + clean.dropped + " 条非法记录", "warn"));', 'void 0;'],
  ['M14 移除空态文案', 'var h = document.createElement("h3"); h.textContent = "没有符合条件的数据";', 'var h = document.createElement("h3"); h.textContent = "";'],
  ['M15 归一化不校验月份格式', 'if (amt === null || region === "" || !isMonthKey(r.month)){ dropped++; continue; }', 'if (amt === null || region === ""){ dropped++; continue; }']
];

const ORACLES = (process.argv.slice(2).length ? process.argv.slice(2) : ['verify-core.js']);

const runOracle = (oracle, args) => {
  try { execFileSync(process.execPath, args, { stdio: 'pipe', timeout: 180000 }); return { code: 0 }; }
  catch (e) { return { code: (typeof e.status === 'number' ? e.status : (e.killed ? 3 : -1)) }; }
};

let killed = 0, survived = [], invalid = [];
MUTANTS.forEach(([name, from, to]) => {
  if (original.indexOf(from) < 0) { invalid.push(name + '  [变异点未命中源码，该变异无效]'); return; }
  const mutated = original.replace(from, to);
  if (mutated === original) { invalid.push(name + '  [替换无效果]'); return; }
  fs.writeFileSync('_mutant.html', mutated, 'utf8');
  let failed = false, which = [], infra = null;
  for (const oracle of ORACLES) {
    const args = oracle === 'verify-core.js' ? ['verify-core.js', '_mutant.html'] : [oracle, '_mutant.html'];
    const r = runOracle(oracle, args);
    if (r.code === 1) { failed = true; which.push(oracle); }
    else if (r.code !== 0) { infra = oracle + '(exit=' + r.code + ')'; }
  }
  if (failed) { killed++; console.log('  KILLED   ' + name + '   [by ' + which.join(', ') + ']'); }
  else if (infra) { invalid.push(name + '  [裁判异常 ' + infra + '，本次判定无效]'); console.log('  INVALID  ' + name + '   ' + infra); }
  else { survived.push(name); console.log('  SURVIVED ' + name); }
});
try { fs.unlinkSync('_mutant.html'); } catch (e) {}
const valid = MUTANTS.length - invalid.length;
console.log('#'.repeat(64));
console.log('变异总数=' + MUTANTS.length + '  有效=' + valid + '  杀死=' + killed + '  存活=' + survived.length + '  无效=' + invalid.length +
  '  杀伤率=' + (valid ? (killed / valid * 100).toFixed(1) : '0') + '%');
if (survived.length) { console.log('--- 存活变异 ---'); survived.forEach(s => console.log('  ' + s)); }
if (invalid.length) { console.log('--- 无效变异 ---'); invalid.forEach(s => console.log('  ' + s)); }
process.exit(survived.length || invalid.length ? 1 : 0);
