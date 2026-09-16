// 交叉比对：Node 独立复算 ≡ Python 独立复算（5 个筛选态 × 4 项期望 + 柱值序列）。
// 任何不一致即 FAIL（多路径交叉验证的收敛检查）。
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const a = JSON.parse(readFileSync(path.join(__dirname, 'out_node.json'), 'utf8'));
const b = JSON.parse(readFileSync(path.join(__dirname, 'out_python.json'), 'utf8'));

const diffs = [];
for (const k of ['all', 'q1', 'q2', 'q3', 'q4']){
  const ea = a[k].expect, eb = b[k].expect;
  for (const f of ['kpiTotal', 'kpiAvg', 'kpiPeak', 'bars']){
    if (JSON.stringify(ea[f]) !== JSON.stringify(eb[f])){
      diffs.push(`${k}.${f}: node=${JSON.stringify(ea[f])} python=${JSON.stringify(eb[f])}`);
    }
  }
  if (JSON.stringify(ea.barValues) !== JSON.stringify(eb.barValues)){
    diffs.push(`${k}.barValues: node=${JSON.stringify(ea.barValues)} python=${JSON.stringify(eb.barValues)}`);
  }
}
if (diffs.length){
  console.error('FAIL cross-check (node vs python):\n' + diffs.join('\n'));
  process.exit(1);
}
console.log('OK cross-check: node ≡ python（5 态 × kpiTotal/kpiAvg/kpiPeak/bars/barValues 全一致）');
