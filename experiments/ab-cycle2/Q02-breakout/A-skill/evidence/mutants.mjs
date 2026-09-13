/**
 * 变异杀伤实验（Mutation Kill Test）
 * 目的：证明 evidence/verify.mjs 这套验证对"它要防的错误"真的有鉴别力。
 *       只跑原产物全绿不构成证据（见 references/common-failures.md 的 F6）。
 *
 * 做法：对 app.html 逐个注入单点变异（每个变异体是独立副本，原产物只读），
 *       用同一套工装跑每个变异体，记录哪些用例转红。
 *       期望：每个变异体至少被 1 个用例杀死（harness 必须 exit 1）。
 *
 * 用法： node evidence/mutants.mjs
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');
const APP = join(ROOT, 'app.html');
const MUT_DIR = join(HERE, 'mutants');
const RES_DIR = join(HERE, 'mutant-results');
mkdirSync(MUT_DIR, { recursive: true });
mkdirSync(RES_DIR, { recursive: true });

const MUTANTS = [
  {
    id: 'm01', bug: '球撞砖块后不反向（垂直方向）', predictedKill: ['C4'],
    edits: [{
      find: '        ball.vy = -ball.vy;\n        ball.y += (oT < oB) ? -minY : minY;',
      replace: '        ball.y += (oT < oB) ? -minY : minY;'
    }]
  },
  {
    id: 'm02', bug: '击碎砖块不加分', predictedKill: ['C4', 'C8'],
    edits: [{ find: '        score += b.points;\n', replace: '' }]
  },
  {
    id: 'm03', bug: '球撞挡板后不反向（继续向下穿透）', predictedKill: ['C6'],
    edits: [{
      // 必须带足上下文：仅 'ball.vy = -Math.abs(...)' 会在 launch() 与 subStep() 各出现一次，
      // 只替换第一处会造成"假存活"（m03 首轮实测教训）—— 故此处锚定挡板反弹块的唯一上下文
      find: '      ball.vx = Math.sin(ang) * ball.speed;\n      ball.vy = -Math.abs(Math.cos(ang) * ball.speed);\n      ball.y = paddle.y - ball.r - 0.01;',
      replace: '      ball.vx = Math.sin(ang) * ball.speed;\n      ball.vy = Math.abs(Math.cos(ang) * ball.speed);\n      ball.y = paddle.y - ball.r - 0.01;'
    }]
  },
  {
    id: 'm04', bug: '暂停按键失效（P/空格无法暂停）', predictedKill: ['C11', 'C13'],
    // 实测杀手：C11。C13 未捕获 —— C13 走 __breakout.pause() API 而非键盘路径，本变异体不影响它；
    // 属"预测偏严"，非工装盲区（该变异体仍被杀死）。
    edits: [{
      find: "      if (state === 'running') { setState('paused'); showOverlay('已暂停', '按 空格 / P 或点击下方按钮继续。', '继续'); return; }",
      replace: "      if (state === 'running') { return; }"
    }]
  },
  {
    id: 'm05', bug: '重开不清分数', predictedKill: ['C12'],
    // 实测杀手：C8（domStart 断言捕获残留分数 20）。C12 未捕获 —— 该场景重开前分数本就是 0，
    // 无法暴露此缺陷；属"预测偏严 + 用例场景重叠"，非工装盲区。
    edits: [{ find: '    score = 0; lives = cfg.lives;', replace: '    lives = cfg.lives;' }]
  },
  {
    id: 'm06', bug: '物理步长内持续分配对象（内存持续增长）', predictedKill: ['C21'],
    edits: [{
      find: '  function stepPhysics(dt) {\n    if (state !== \'running\') return;',
      replace: '  var __leak = [];\n  function stepPhysics(dt) {\n    __leak.push({ d: dt, pad: new Array(32).fill(1) });\n    if (state !== \'running\') return;'
    }]
  },
  {
    id: 'm07', bug: '超长文本不截断（原样塞进 HUD）', predictedKill: ['C16'],
    edits: [{ find: '    if (s.length > maxLen) s = s.slice(0, maxLen - 1) + \'…\';\n', replace: '' }]
  },
  {
    id: 'm08', bug: '空关卡数据不回退（无砖块也直接开玩）', predictedKill: ['C14', 'C15'],
    edits: [
      { find: "      if (alive === 0) { issues.push('关卡为空（无任何砖块），已回退默认关卡'); layout = DEFAULT_LAYOUT.slice(); }",
        replace: "      if (alive === 0) { issues.push('关卡为空（无任何砖块），已回退默认关卡'); }" },
      { find: "    if (bricksAlive === 0) {           // 极端兜底：无砖块也必须有可玩状态\n      cfg.layout = DEFAULT_LAYOUT.slice();\n      cfg.cols = 10; cfg.rows = 6;\n      buildBricks();\n    }\n",
        replace: '' }
    ]
  },
  {
    id: 'm09', bug: '键盘无法移动挡板', predictedKill: ['C9'],
    edits: [{ find: '    if (keys.left && !keys.right) paddle.x -= PADDLE_SPEED * dt;',
              replace: '    if (false) paddle.x -= PADDLE_SPEED * dt;' }]
  },
  {
    id: 'm10', bug: '鼠标无法移动挡板', predictedKill: ['C10'],
    edits: [{ find: '  function onPointerMove(e) { movePaddleTo(canvasX(e.clientX)); }',
              replace: '  function onPointerMove(e) { /* mutant: 鼠标失效 */ }' }]
  }
];

const src = readFileSync(APP, 'utf8');
const summary = [];

console.log('== 变异杀伤实验开始 ==\n');
for (const m of MUTANTS) {
  let html = src, applied = 0;
  for (const e of m.edits) {
    const hits = html.split(e.find).length - 1;
    // 变异点必须唯一命中：命中 0 次＝工装失效；命中 >1 次＝replace 只改第一处，会造出"假存活"变异体
    if (hits !== 1) throw new Error(`${m.id} 变异点命中 ${hits} 次（要求恰好 1 次），实验无效：${JSON.stringify(e.find.slice(0, 70))}`);
    html = html.replace(e.find, e.replace);
    applied++;
  }
  if (html === src) throw new Error(`${m.id} 变异后文件未发生变化，实验无效`);
  const file = join(MUT_DIR, `${m.id}.html`);
  writeFileSync(file, html);
  const out = join(RES_DIR, `${m.id}.json`);

  let killed = [], exitCode = 0, err = '';
  try {
    execFileSync(process.execPath, [join(HERE, 'verify.mjs'), '--app', file, '--label', m.id, '--out', out],
      { stdio: 'pipe', encoding: 'utf8', timeout: 600000 });
  } catch (e) {
    exitCode = e.status === undefined ? 3 : e.status;
    err = (e.stderr || '').slice(-400);
  }
  let failedIds = [];
  try {
    const r = JSON.parse(readFileSync(out, 'utf8'));
    failedIds = r.results.filter((x) => !x.pass).map((x) => x.id);
  } catch {}
  killed = failedIds;
  // 判定口径：一个变异体"被杀死"＝工装对它的运行变红（exit 1 且至少 1 项转红）。
  // predictedKill 是我事前预测的杀手用例，单独记录并与实际对比，不参与杀死判定。
  const isKilled = exitCode === 1 && killed.length > 0;
  const predictionHits = m.predictedKill.filter((id) => killed.includes(id));
  const predictionMisses = m.predictedKill.filter((id) => !killed.includes(id));
  const predictedAll = predictionMisses.length === 0;
  summary.push({
    id: m.id, bug: m.bug, edits: applied, exitCode, killed,
    predictedKill: m.predictedKill, predictionHits, predictionMisses, predictedAll,
    verdict: isKilled ? 'KILLED' : 'SURVIVED', err
  });
  console.log(`${isKilled ? 'KILLED  ' : 'SURVIVED'} ${m.id}  ${m.bug}\n          实际死亡用例=${JSON.stringify(killed)}  预测=${JSON.stringify(m.predictedKill)}${predictedAll ? '' : '（预测偏严：' + JSON.stringify(predictionMisses) + ' 未触发）'}  exit=${exitCode}${err ? ' err=' + err : ''}`);
}

const allKilled = summary.every((s) => s.verdict === 'KILLED');
const predictionOff = summary.filter((s) => !s.predictedAll).map((s) => s.id);
writeFileSync(join(HERE, 'mutation-summary.json'),
  JSON.stringify({
    app: APP, total: summary.length,
    killed: summary.filter((s) => s.verdict === 'KILLED').length,
    allKilled,
    criterion: '被杀死 = 该变异体运行 exit 1 且至少 1 项检查转红；predictedKill 仅作事前预测对照，不参与判定',
    predictionOff, summary
  }, null, 2));
console.log(`\n== 杀伤率 ${summary.filter((s) => s.verdict === 'KILLED').length}/${summary.length} ==`);
if (predictionOff.length) console.log(`（预测偏严的变异体：${predictionOff.join(', ')} —— 实际由其它用例杀死，详见汇总）`);
console.log('汇总写入 evidence/mutation-summary.json');
process.exit(allKilled ? 0 : 1);
