// 变异测试（鉴别力证明）：验证体系若"永远绿"则不构成证据。
// 向临时目录注入 3 个真实缺陷（均在交付目录之外运行，运行后自清理），
// 断言证据脚本全部捕获（非零退出）。任何未捕获 => FAIL。
import { cpSync, mkdirSync, rmSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(__dirname);
const results = [];
let failed = false;

function runMutation(name, mutate, checkCmds){
  const dir = path.join(tmpdir(), 'g3-mutation-' + name + '-' + Date.now());
  mkdirSync(dir, { recursive: true });
  try {
    const html = readFileSync(path.join(ROOT, 'index.html'), 'utf8');
    const mutated = mutate(html);
    if (mutated === html) throw new Error('mutation did not apply');
    writeFileSync(path.join(dir, 'index.html'), mutated);
    cpSync(__dirname, path.join(dir, 'evidence'), { recursive: true });
    for (const f of ['out_node.json','out_python.json','out_contrast.json','out_shim.json','out_browser.json','out_mutation.json','out_render','page_script_extracted.js']){
      const p = path.join(dir, 'evidence', f);
      if (existsSync(p)) rmSync(p, { recursive: true, force: true });
    }
    let detected = false, trigger = '';
    for (const c of checkCmds){
      try {
        execFileSync('node', [path.join(dir, 'evidence', c)],
          { encoding: 'utf8', timeout: 180000, stdio: ['ignore', 'pipe', 'pipe'] });
      } catch(e){
        detected = true; trigger = c + ' (exit ' + e.status + ')';
        break;
      }
    }
    results.push({ mutation: name, detected, capturedBy: trigger });
    if (!detected) failed = true;
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

/* M1 峰值卡显示错误（显示第一个月而非最大月） */
runMutation('peak-display-wrong',
  h => h.replace('setCard("kpi-peak", mt.peakMonth,', 'setCard("kpi-peak", rows[0].m,'),
  ['dom_shim_test.mjs', 'browser_check.mjs']);

/* M2 筛选点击失效（setScope 变 no-op，同步更新被破坏） */
runMutation('filter-click-noop',
  h => h.replace('function setScope(k){ if (SCOPES[k]){ render(k); } }',
                 'function setScope(k){ /* mutated: no-op */ }'),
  ['dom_shim_test.mjs']);

/* M3 总额硬编码错误（显示值与内联数据脱钩） */
runMutation('total-hardcode-wrong',
  h => h.replace('setCard("kpi-total", fmtInt(mt.total),', 'setCard("kpi-total", fmtInt(9999),'),
  ['browser_check.mjs', 'dom_shim_test.mjs']);

writeFileSync(path.join(__dirname, 'out_mutation.json'), JSON.stringify(results, null, 2));
const n = results.filter(r => r.detected).length;
console.log((failed ? 'FAIL' : 'OK') + ` mutation_test: ${n}/${results.length} 个注入缺陷被捕获`);
if (failed) process.exit(1);
