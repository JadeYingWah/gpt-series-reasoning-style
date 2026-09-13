// G1-A2plus 多路径交叉验证
// 路径 2（本文件前半）：Node 提取 index.html 的 CALC-CORE 纯逻辑，对 oracle（Python 精确分数）期望值跑电池——独立于浏览器。
// 路径 3（本文件后半）：变异测试——向核心逻辑注入 5 类典型缺陷，电池必须逐一致死（鉴别力证明：回答"把要防的错误做一次，它会不会红"）。
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, '..', 'index.html'), 'utf8');
const vectors = JSON.parse(readFileSync(join(here, 'vectors.json'), 'utf8'));
const OUT = join(here, 'results');
mkdirSync(OUT, { recursive: true });

const m = html.match(/\/\*CALC-CORE-START\*\/([\s\S]*?)\/\*CALC-CORE-END\*\//);
if (!m) {
  console.error('FATAL: index.html 中未找到 CALC-CORE 标记');
  process.exit(2);
}
const coreSrc = m[1];

function loadCore(src) {
  const factory = new Function(src + '\n;return { evalExpression: evalExpression, cleanNumber: cleanNumber, formatNumber: formatNumber };');
  return factory();
}

function runBattery(core) {
  const cases = [];
  for (const v of vectors) {
    v.eval_points.forEach((p, i) => {
      const caseId = v.id + '#eq' + (i + 1);
      const r = core.evalExpression(p.expr);
      let ok, got;
      if (p.error) {
        ok = !r.ok && r.error === p.error;
        got = r.ok ? 'OK(' + r.value + ')' : 'ERR(' + (r.error || 'unknown') + ')';
      } else {
        ok = r.ok && core.formatNumber(r.value) === p.result;
        got = r.ok ? core.formatNumber(r.value) : 'ERR(' + (r.error || 'unknown') + ')';
      }
      cases.push({ case: caseId, expr: p.expr, expected: p.error !== null && p.error !== undefined ? 'ERR(' + p.error + ')' : p.result, got, pass: ok });
    });
  }
  return cases;
}

// ---- 路径 2：原始核心电池 ----
const base = loadCore(coreSrc);
const baseCases = runBattery(base);
const basePass = baseCases.filter(c => c.pass).length;
const baseFail = baseCases.length - basePass;
console.log('== 路径2: Node 核心电池 vs Python 精确分数 oracle ==');
console.log('用例数: ' + baseCases.length + '  通过: ' + basePass + '  失败: ' + baseFail);
baseCases.filter(c => !c.pass).forEach(c => console.log('  FAIL ' + c.case + ' expr=' + c.expr + ' expected=' + c.expected + ' got=' + c.got));

// ---- 路径 3：变异测试 ----
const MUTANTS = [
  { id: 'M1-precedence-broken', desc: '优先级破坏：+ 与 * 同级先算（2+3*4 应 14，变异后 20）', from: "if (op.v === '*') {", to: "if (op.v === '+' || op.v === '*') {" },
  { id: 'M2-div0-unguarded', desc: '除零守卫移除（5/0 应 ERR(DIV0)，变异后 Infinity）', from: "if (num.v === 0) return { ok: false, error: 'DIV0' };", to: "if (num.v === NaN) return { ok: false, error: 'DIV0' };" },
  { id: 'M3-decimal-stripped', desc: '小数点被剥离（0.1+0.2 应 0.3，变异后 3）', from: "tokens.push({ t: 'num', v: parseFloat(numStr) });", to: "tokens.push({ t: 'num', v: parseFloat(numStr.replace(/\\./g, '')) });" },
  { id: 'M4-clean-removed', desc: '显示清理移除（0.1+0.2 应 0.3，变异后 0.30000000000000004）', from: 'return parseFloat(n.toPrecision(12));', to: 'return n;' },
  { id: 'M5-sub-to-add', desc: '减法变加法（9-4-3 应 2，变异后 16）', from: 'else acc -= pass1[p + 1].v;', to: 'else acc += pass1[p + 1].v;' },
];

console.log('\n== 路径3: 变异测试（电池鉴别力） ==');
const mutantResults = [];
for (const mu of MUTANTS) {
  if (!coreSrc.includes(mu.from)) {
    mutantResults.push({ id: mu.id, desc: mu.desc, applied: false, killed: false, killers: [], note: '变异锚点未命中——变异体无效' });
    console.log('  [无效] ' + mu.id + '：锚点字符串未找到');
    continue;
  }
  let mutated;
  try {
    mutated = loadCore(coreSrc.replace(mu.from, mu.to));
  } catch (e) {
    mutantResults.push({ id: mu.id, desc: mu.desc, applied: true, killed: true, killers: [{ case: '<load>', got: String(e) }], note: '变异体加载即抛错（视为致死）' });
    continue;
  }
  const cases = runBattery(mutated);
  const killers = cases.filter(c => !c.pass).map(c => ({ case: c.case, expected: c.expected, got: c.got }));
  mutantResults.push({ id: mu.id, desc: mu.desc, applied: true, killed: killers.length > 0, killers });
  console.log((killers.length > 0 ? '  [杀死] ' : '  [存活!] ') + mu.id + '  杀死用例: ' + killers.map(k => k.case).join(', '));
}

const applied = mutantResults.filter(r => r.applied);
const killedCount = applied.filter(r => r.killed).length;
const verdict = baseFail === 0 && applied.length === MUTANTS.length && killedCount === MUTANTS.length ? 'PASS' : 'FAIL';
console.log('\n变异杀伤: ' + killedCount + '/' + MUTANTS.length);
console.log('总判定: ' + verdict);

writeFileSync(join(OUT, 'core-battery.json'), JSON.stringify({
  path2_battery: { total: baseCases.length, pass: basePass, fail: baseFail, cases: baseCases },
  path3_mutation: { total: MUTANTS.length, applied: applied.length, killed: killedCount, mutants: mutantResults },
  verdict,
  generated: new Date().toISOString(),
}, null, 1));

process.exit(verdict === 'PASS' ? 0 : 1);
