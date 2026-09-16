// 变异测试：证明 verify.mjs 的断言具备「杀伤力」——把要防的错误真的做一次，看它是否变红。
// 用法: node mutation-test.mjs   （报告写入 mutation-report.md，退出码 0 = 全部被杀死）
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const DIR = '<实验根目录>/ab-cycle2/BASE01-countdown/A-skill';
const MUT_DIR = join(DIR, '_verify');
mkdirSync(MUT_DIR, { recursive: true });

const src = readFileSync(join(DIR, 'app.html'), 'utf8');

// 每个变异体：注入一个真实缺陷，并声明「哪个用例必须变红」
const mutants = [
  {
    id: 'M1',
    desc: '删除「分钟数必须大于 0」校验（允许 0 启动）',
    find: "    if (n <= 0) return { ok: false, err: '分钟数必须大于 0' };\n",
    replace: '',
    mustFail: ['T3'],
  },
  {
    id: 'M2',
    desc: '归零时不显示提示横幅（静默结束）',
    find: "el.banner.classList.toggle('show', state === 'finished');",
    replace: "el.banner.classList.toggle('show', false);",
    mustFail: ['T12'],
  },
  {
    id: 'M3',
    desc: '暂停时不停止计时器（暂停后时间继续走）',
    find: "    stopTicker();\n    if (remainingMs <= 0) { finish(); return; }",
    replace: "    if (remainingMs <= 0) { finish(); return; }",
    mustFail: ['T9'],
  },
  {
    id: 'M4',
    desc: '删除空输入校验（空值不再给出「请输入分钟数」提示）',
    find: "    if (s === '') return { ok: false, err: '请输入分钟数（不能为空）' };\n",
    replace: '',
    mustFail: ['T2'],
  },
];

const rows = [];
let allKilled = true;

for (const m of mutants) {
  if (!src.includes(m.find)) {
    rows.push({ ...m, status: 'INVALID', detail: '未找到待替换源码片段，变异未生效' });
    allKilled = false;
    continue;
  }
  const mutated = src.replace(m.find, m.replace);
  const file = join(MUT_DIR, `mutant-${m.id}.html`);
  writeFileSync(file, mutated, 'utf8');

  const runOnce = (port) => spawnSync(process.execPath, [join(DIR, 'verify.mjs')], {
    env: {
      ...process.env,
      PAGE_URL: 'file:///' + file.replace(/\\/g, '/'),
      OUT_SUFFIX: `-${m.id}`,
      SHOTS: '0',
      CDP_PORT: String(port),
    },
    encoding: 'utf8',
    timeout: 180000,
  });

  const readFailed = () => {
    try {
      const raw = JSON.parse(readFileSync(join(DIR, `verify-raw-${m.id}.json`), 'utf8'));
      return raw.filter(x => !x.pass).map(x => x.id);
    } catch (e) {
      return [];
    }
  };

  let observedFailed = [];
  for (let attempt = 1; attempt <= 3; attempt++) {
    runOnce(9300 + Math.floor(Math.random() * 400));
    observedFailed = readFailed();
    // 只出现 ERR（CDP 未就绪一类的基础设施故障）时重试；出现真实用例结果即停止
    if (!(observedFailed.length === 1 && observedFailed[0] === 'ERR')) break;
  }

  const killed = m.mustFail.every(id => observedFailed.includes(id));
  if (!killed) allKilled = false;
  rows.push({
    ...m,
    status: killed ? 'KILLED' : 'SURVIVED',
    detail: `期望变红 [${m.mustFail.join(',')}]；实测变红 [${observedFailed.join(',') || '无'}]`,
  });
}

const lines = [];
lines.push('# 变异测试报告（验证自身是否具备鉴别力）');
lines.push('');
lines.push(`结论：${rows.filter(r => r.status === 'KILLED').length}/${rows.length} 个变异体被杀死`);
lines.push('');
lines.push('| 变异体 | 注入的真实缺陷 | 应被哪个用例抓住 | 结果 | 实测 |');
lines.push('| --- | --- | --- | --- | --- |');
for (const r of rows) {
  lines.push(`| ${r.id} | ${r.desc} | ${r.mustFail.join(',')} | ${r.status} | ${r.detail} |`);
}
lines.push('');
lines.push('说明：变异体 HTML 存于 `_verify/mutant-M*.html`，对应验证报告存于 `verify-report-M*.md`，可复算。');
writeFileSync(join(DIR, 'mutation-report.md'), lines.join('\n'), 'utf8');
console.log(lines.join('\n'));
process.exit(allKilled ? 0 : 1);
