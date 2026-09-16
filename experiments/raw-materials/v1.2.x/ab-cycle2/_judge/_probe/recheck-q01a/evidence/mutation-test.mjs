// 杀伤率审计（变异测试）：证明前面那套「33/33 全过」不是橡皮图章。
// 对 app.html 逐个注入**真实典型缺陷**，重跑静态自检 + 浏览器验收；
// 每个变异只要让至少一项检查由 PASS 翻成 FAIL，就算被「杀死」。
// 用法：node evidence/mutation-test.mjs
import { readFileSync, writeFileSync, existsSync, unlinkSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const SRC = join(root, 'app.html');
const MUT = join(root, '_mutant.html');
const original = readFileSync(SRC, 'utf8');

const MUTATIONS = [
  { id: 'M1', desc: 'KPI 总额 +1（数字卡与数据脱钩）', find: 'setNum(document.querySelector(\'[data-testid="kpi-total"]\'), fmt2(st.total));', replace: 'setNum(document.querySelector(\'[data-testid="kpi-total"]\'), fmt2(st.total + 1));', expect: ['kpi-ALL'] },
  { id: 'M2', desc: '按月聚合每笔多加 1 元（图表与数据脱钩）', find: 'map[r.month] += amt;', replace: 'map[r.month] += amt + 1;', expect: ['bars-ALL'] },
  { id: 'M3', desc: '空态不显示（删除 empty.classList.add(\'show\')）', find: "empty.classList.add('show');", replace: '/* mutation: 空态不显示 */;', expect: ['C3-empty-real', 'C4a-empty-dataset'] },
  { id: 'M4', desc: '非法筛选值不设防（直接调用 v.toUpperCase()）', find: 'state.invalidValue = v;', replace: 'state.invalidValue = v.toUpperCase();', expect: ['C4c-null', 'C4c-undefined', 'C4c-数字'] },
  { id: 'M5', desc: '引入外部 CDN 脚本（破坏离线单文件）', find: '</body>', replace: '<script src="https://cdn.example.com/echarts.js"></script>\n</body>', expect: ['static-check'] },
  { id: 'M6', desc: '月份轴随筛选塌缩（失去稳定轴）', find: 'var axis = state.axis;', replace: 'var axis = monthAxis(rows);', expect: ['C2b-axis-stable'] },
  { id: 'M7', desc: '筛选控件变更事件未接线（筛选失效）', find: "window.__app.setFilter(e && e.target ? e.target.value : ALL);", replace: '/* mutation: 未接线 */;', expect: ['C2-filter-applied'] },
  { id: 'M8', desc: '柱体 tooltip 文案被移除', find: "tip.textContent = it.month + '：¥' + fmt2(it.value) + '（' + fmtInt(countOf(it.month)) + ' 笔）';", replace: "tip.textContent = '';", expect: ['C1-tooltip'] },
  { id: 'M9', desc: '超长文本省略号截断被移除（徽标不再 ellipsis）', find: '.badge .txt{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}', replace: '.badge .txt{}', expect: ['C4d-long-text'] },
  { id: 'M10', desc: '客单价改为「总销售额」（客单价算错）', find: 'setNum(document.querySelector(\'[data-testid="kpi-avg"]\'), fmt2(st.avg));', replace: 'setNum(document.querySelector(\'[data-testid="kpi-avg"]\'), fmt2(st.total));', expect: ['kpi-ALL'] },
];

function runStatic(target) {
  try {
    const out = execFileSync(process.execPath, [join(here, 'static-check.mjs')], {
      env: { ...process.env, Q01_TARGET: target }, encoding: 'utf8',
    });
    return { pass: true, out };
  } catch (e) { return { pass: false, out: String(e.stdout || e.message) }; }
}
function runBrowser(target, outName) {
  try {
    execFileSync(process.execPath, [join(here, 'browser-check.mjs')], {
      env: { ...process.env, Q01_TARGET: target, Q01_OUT: outName, Q01_SHOTS: 'shots-mutant', Q01_QUIET: '1' },
      encoding: 'utf8', stdio: 'pipe',
    });
    return true;
  } catch { return false; }
}
function loadResults(outName) {
  const p = join(here, outName);
  if (!existsSync(p)) return null;
  const j = JSON.parse(readFileSync(p, 'utf8'));
  const map = {};
  for (const r of j.results) map[r.id] = r.pass;
  return map;
}

console.log('== 基线 ==');
const baseStatic = runStatic('app.html');
console.log('基线 static-check:', baseStatic.pass ? 'PASS' : 'FAIL');
runBrowser('app.html', 'bc-baseline.json');
const base = loadResults('bc-baseline.json');
const baseFail = Object.entries(base).filter(([, v]) => !v).map(([k]) => k);
console.log(`基线 browser-check: ${Object.values(base).filter(Boolean).length}/${Object.keys(base).length} PASS`);
if (!baseStatic.pass || baseFail.length) { console.error('基线不干净，终止：', baseFail); process.exit(2); }

const rows = [];
let killed = 0;
for (const m of MUTATIONS) {
  if (!original.includes(m.find)) { rows.push({ id: m.id, killed: null, note: '变异锚点未命中（脚本需更新）' }); console.log(`SKIP ${m.id} 锚点未命中`); continue; }
  writeFileSync(MUT, original.replace(m.find, m.replace), 'utf8');
  const st = runStatic('_mutant.html');
  runBrowser('_mutant.html', 'bc-mutant.json');
  const mut = loadResults('bc-mutant.json') || {};
  const flipped = [
    ...(st.pass ? [] : ['static-check']),
    ...Object.keys(mut).filter((k) => base[k] === true && mut[k] === false),
  ];
  // 变异体自身若因语法错误整体崩掉，也算被检出（但需标注）
  const isKilled = flipped.length > 0;
  const hitExpected = m.expect.some((e) => flipped.includes(e));
  if (isKilled) killed++;
  rows.push({ id: m.id, desc: m.desc, killed: isKilled, hitExpected, flipped, expect: m.expect, mutantsPassed: Object.values(mut).filter(Boolean).length, mutantsTotal: Object.keys(mut).length });
  console.log(`${isKilled ? 'KILLED' : 'SURVIVED'} ${m.id} ${m.desc}`);
  console.log(`        翻红项: ${flipped.join(', ') || '(无)'}  期望命中: ${m.expect.join('/')} => ${hitExpected ? '命中' : '未命中'}`);
}

try { unlinkSync(MUT); } catch {}
const summary = {
  ranAt: new Date().toISOString(),
  baseline: { staticCheck: baseStatic.pass, browserTotal: Object.keys(base).length, browserPassed: Object.values(base).filter(Boolean).length },
  mutationsTotal: MUTATIONS.length,
  killed,
  survived: MUTATIONS.length - killed,
  killRate: +(killed / MUTATIONS.length).toFixed(3),
  rows,
};
writeFileSync(join(here, 'mutation-test.json'), JSON.stringify(summary, null, 2) + '\n', 'utf8');
console.log(`\n==== 杀伤率 ${killed}/${MUTATIONS.length} = ${(killed / MUTATIONS.length * 100).toFixed(0)}% ====`);
console.log('（杀伤率 = 注入真实缺陷后检查翻红的比例；越低说明这套检查越像橡皮图章）');
process.exit(0);
