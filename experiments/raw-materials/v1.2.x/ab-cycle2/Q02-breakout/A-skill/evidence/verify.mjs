/**
 * Q02-breakout / A-skill 验证工装（第三方可复算）
 * 用法： node evidence/verify.mjs [--app <app.html 路径>] [--label <标签>] [--out <json 输出路径>]
 *
 * 设计要点
 *  - 真实浏览器：Chrome headless + CDP，file:// 打开产物，走真实 rAF/DOM/Canvas。
 *  - 物理用例在单次 Runtime.evaluate 内同步完成（JS 单线程原子），结果确定可复算。
 *  - 互动用例（键盘/鼠标/按钮）通过 CDP Input 域派发真实输入事件。
 *  - 每次都核验：window.onerror / unhandledrejection / Runtime.exceptionThrown / Log.entryAdded。
 */
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
function argOf(name, def) { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; }
const APP = resolve(argOf('--app', 'app.html'));
const LABEL = argOf('--label', 'app');
const OUT = resolve(argOf('--out', `evidence/results-${LABEL}.json`));
const SHOTS = resolve(dirname(OUT), 'shots');
const PORT = 9333 + Math.floor(Math.random() * 400);
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
let failures = 0;
function check(id, name, pass, detail, evidence) {
  results.push({ id, name, pass: !!pass, detail, evidence });
  if (!pass) failures++;
  console.log(`${pass ? 'PASS' : 'FAIL'}  ${id}  ${name}${detail ? '  :: ' + detail : ''}`);
}

/* ------------------------------ CDP 客户端 ------------------------------ */
class CDP {
  constructor(ws) {
    this.ws = ws; this.seq = 0; this.pending = new Map(); this.onEvent = () => {};
    ws.addEventListener('message', (ev) => {
      let m; try { m = JSON.parse(ev.data); } catch { return; }
      if (m.id && this.pending.has(m.id)) {
        const { res, rej } = this.pending.get(m.id); this.pending.delete(m.id);
        m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result);
      } else if (m.method) this.onEvent(m);
    });
  }
  send(method, params = {}, sessionId) {
    const id = ++this.seq;
    return new Promise((res, rej) => {
      this.pending.set(id, { res, rej });
      this.ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
    });
  }
}
function openWs(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url);
    ws.addEventListener('open', () => res(ws));
    ws.addEventListener('error', (e) => rej(new Error('ws error')));
  });
}

let chromeProc = null, userDataDir = null;
async function launchChrome() {
  userDataDir = mkdtempSync(join(tmpdir(), 'qb-udd-'));
  const a = [
    '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--disable-extensions', '--disable-background-networking', '--mute-audio',
    `--remote-debugging-port=${PORT}`, `--user-data-dir=${userDataDir}`,
    '--enable-precise-memory-info', '--js-flags=--expose-gc',
    '--window-size=1000,1000', '--allow-file-access-from-files', 'about:blank'
  ];
  chromeProc = spawn(CHROME, a, { stdio: 'ignore' });
  for (let i = 0; i < 80; i++) {
    try { const r = await fetch(`http://127.0.0.1:${PORT}/json/version`); if (r.ok) return await r.json(); } catch {}
    await wait(250);
  }
  throw new Error('Chrome 未在预期时间内就绪');
}

/* ------------------------------ 主流程 ------------------------------ */
const fileUrl = pathToFileURL(APP).href;
let cdp, session, exceptions = [], netRequests = [], consoleErrors = [];

async function newPage(url) {
  exceptions = []; netRequests = []; consoleErrors = [];
  const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
  session = sessionId;
  await cdp.send('Page.enable', {}, session);
  await cdp.send('Runtime.enable', {}, session);
  await cdp.send('Log.enable', {}, session);
  await cdp.send('Network.enable', {}, session);
  await cdp.send('Page.addScriptToEvaluateOnNewDocument', {
    source: `window.__errors=[];
      window.onerror=function(m,s,l,c,e){window.__errors.push('onerror: '+m)};
      window.addEventListener('unhandledrejection',function(e){window.__errors.push('rejection: '+e.reason)});
      window.__raf=0;(function tick(){window.__raf++;requestAnimationFrame(tick)})();`
  }, session);
  const loaded = new Promise((res) => {
    const h = (m) => { if (m.sessionId === session && m.method === 'Page.loadEventFired') res(); };
    const prev = cdp.onEvent; cdp.onEvent = (m) => { prev(m); h(m); };
  });
  await cdp.send('Page.navigate', { url }, session);
  await Promise.race([loaded, wait(15000)]);
  await wait(250);
  // 防"测错文件"：确认页面真的加载了本次指定的产物（变异实验中每个变异体是独立文件）
  const got = await evalJs('location.pathname');
  if (decodeURIComponent(got) !== decodeURIComponent(new URL(url).pathname)) {
    throw new Error(`页面未加载目标文件：got=${got} want=${new URL(url).pathname}`);
  }
  return sessionId;
}
const evalJs = async (expr) => {
  const r = await cdp.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }, session);
  if (r.exceptionDetails) {
    const d = r.exceptionDetails.exception?.description || r.exceptionDetails.text;
    throw new Error('页面内未捕获异常: ' + d);
  }
  return r.result.value;
};
const pageErrors = async () => {
  const inPage = await evalJs('window.__errors ? window.__errors.slice() : ["no-collector"]');
  return { inPage, cdp: exceptions.slice(), logs: consoleErrors.slice() };
};
async function shot(name) {
  const r = await cdp.send('Page.captureScreenshot', { format: 'png' }, session);
  mkdirSync(SHOTS, { recursive: true });
  const p = join(SHOTS, `${LABEL}-${name}.png`);
  writeFileSync(p, Buffer.from(r.data, 'base64'));
  return p;
}
function key(type, key, code, vk) {
  return cdp.send('Input.dispatchKeyEvent', {
    type, key, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk,
    text: type === 'keyDown' && key.length === 1 ? key : undefined
  }, session);
}

/* ------------------------------ 静态检查 ------------------------------ */
{
  const html = readFileSync(APP, 'utf8');
  const patterns = [
    ['<script src=', /<script[^>]+src\s*=/i],
    ['<link href=', /<link[^>]+href\s*=/i],
    ['@import', /@import/i],
    ['url(http', /url\(\s*['"]?https?:/i],
    ['fetch(', /\bfetch\s*\(/],
    ['XMLHttpRequest', /XMLHttpRequest/],
    ['WebSocket', /new\s+WebSocket/],
    ['import(', /\bimport\s*\(/],
    ['http(s) 字面量', /https?:\/\//i]
  ];
  const hits = patterns.filter(([, re]) => re.test(html)).map(([n]) => n);
  check('S1', '静态：无外部 CDN / 无网络请求代码', hits.length === 0,
    hits.length ? '命中：' + hits.join(', ') : '扫描 9 类模式，0 命中',
    { bytes: html.length, patterns: patterns.map(([n]) => n) });
  // 已知靶子：证明扫描正则会命中（避免"0 命中其实是扫描器坏了"）
  const probe = `<script src="https://cdn.example.com/a.js"></script>`;
  const probeHit = /<script[^>]+src\s*=/i.test(probe) && /https?:\/\//i.test(probe);
  check('S1b', '静态：扫描器自证（对已知靶子必须命中）', probeHit, '人工构造的 CDN 片段被同一组正则命中',
    { probe });
  check('S2', '产物为单文件、含内联 CSS 与 JS', /<style[\s\S]*<\/style>/i.test(html) && /<script[\s\S]*<\/script>/i.test(html),
    '样式与脚本均内联', { bytes: html.length });
}

/* ------------------------------ 运行时检查 ------------------------------ */
(async () => {
  const info = await launchChrome();
  const ws = await openWs(info.webSocketDebuggerUrl);
  cdp = new CDP(ws);
  cdp.onEvent = (m) => {
    if (m.sessionId !== session) return;
    if (m.method === 'Runtime.exceptionThrown') exceptions.push(m.params.exceptionDetails?.exception?.description || m.params.exceptionDetails?.text);
    if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') consoleErrors.push(m.params.entry.text);
    if (m.method === 'Network.requestWillBeSent') netRequests.push(m.params.request.url);
  };

  /* ---- C1：加载 + 初始渲染 ---- */
  await newPage(fileUrl);
  const boot = await evalJs(`(function(){
    var c=document.getElementById('stage'),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data,n=0;
    for(var i=0;i<d.length;i+=4){ if(d[i]|d[i+1]|d[i+2]) n++; }
    var s=window.__breakout.getState();
    return {nonBlankPixels:n,state:s.state,bricksAlive:s.bricksAlive,score:s.score,lives:s.lives,title:s.levelTitle,
            overlayHidden:document.getElementById('overlay').hidden, ovBtn:document.getElementById('ovBtn').textContent,
            canvasPixels:c.width*c.height};
  })()`);
  check('C1', '加载：无异常 + Canvas 非空白 + 初始状态正确',
    boot.nonBlankPixels > boot.canvasPixels * 0.1 && boot.state === 'held' && boot.bricksAlive > 0,
    `非空像素 ${boot.nonBlankPixels}/${boot.canvasPixels}，state=${boot.state}，砖块 ${boot.bricksAlive}，分数 ${boot.score}，命 ${boot.lives}`,
    boot);
  await shot('01-boot');

  const net = netRequests.slice();
  const external = net.filter((u) => !/^(file|data|blob):/.test(u));
  check('C2', '运行时网络：全部请求均为本地 file/data（离线可运行）',
    external.length === 0, `共捕获 ${net.length} 个请求；非本地请求 ${external.length} 个`, { net });

  const e1 = await pageErrors();
  check('C3', '加载后：无未捕获异常 / 无 error 级控制台日志',
    e1.inPage.length === 0 && e1.cdp.length === 0 && e1.logs.length === 0, JSON.stringify(e1), e1);

  /* ---- C4：球-砖碰撞反向 + 扣血 + 计分（确定性物理，单砖隔离关卡） ---- */
  const c4 = await evalJs(`(function(){
    var B=window.__breakout;
    B.applyConfig({cols:3, rows:1, layout:['010']});      // 单砖隔离，排除相邻砖块干扰
    var bs=B.bricks(), t=null;
    for(var i=0;i<bs.length;i++){ if(bs[i].alive){t=bs[i];break;} }
    var s0=B.getState();
    B.setBall(t.x+t.w/2, t.y+t.h+s0.ball.r+2, 0, -300);   // 从砖块正下方朝上运动
    var before=B.getState();
    var after=B.simulate(80);
    return {brick:t, vyBefore:before.ball.vy, vyAfter:after.ball.vy,
            yBefore:before.ball.y, yAfter:after.ball.y, bricksInLevel:bs.length,
            aliveBefore:s0.bricksAlive, aliveAfter:after.bricksAlive,
            scoreBefore:s0.score, scoreAfter:after.score};
  })()`);
  check('C4', '交互1：球撞击砖块后垂直速度反向，砖块数 -1，分数增加',
    c4.vyBefore < 0 && c4.vyAfter > 0 && c4.aliveAfter === c4.aliveBefore - 1 && c4.scoreAfter > c4.scoreBefore,
    `单砖关卡(共${c4.bricksInLevel}块) 目标砖(${c4.brick.x.toFixed(0)},${c4.brick.y.toFixed(0)}) vy ${c4.vyBefore}→${c4.vyAfter}（y ${c4.yBefore.toFixed(1)}→${c4.yAfter.toFixed(1)}）；砖块 ${c4.aliveBefore}→${c4.aliveAfter}；分数 ${c4.scoreBefore}→${c4.scoreAfter}`,
    c4);

  /* ---- C5：侧向撞砖 → 水平反向（同样单砖隔离） ---- */
  const c5b = await evalJs(`(function(){
    var B=window.__breakout;
    B.applyConfig({cols:3, rows:1, layout:['010']});
    var bs=B.bricks(), t=null;
    for(var i=0;i<bs.length;i++){ if(bs[i].alive){t=bs[i];break;} }
    var before0=B.getState();
    B.setBall(t.x - before0.ball.r - 2, t.y + t.h/2, 300, 0);   // 从左向右撞砖块左边缘
    var before=B.getState();
    var after=B.simulate(80);
    return {brick:t, vxBefore:before.ball.vx, vxAfter:after.ball.vx,
            aliveBefore:before0.bricksAlive, aliveAfter:after.bricksAlive,
            scoreBefore:before0.score, scoreAfter:after.score};
  })()`);
  check('C5', '交互1b：侧向撞砖 → 水平速度反向，砖块销毁并计分',
    c5b.vxBefore > 0 && c5b.vxAfter < 0 && c5b.aliveAfter === c5b.aliveBefore - 1 && c5b.scoreAfter > c5b.scoreBefore,
    `目标砖(${c5b.brick.x.toFixed(0)},${c5b.brick.y.toFixed(0)}) vx ${c5b.vxBefore}→${c5b.vxAfter}；砖块 ${c5b.aliveBefore}→${c5b.aliveAfter}；分数 ${c5b.scoreBefore}→${c5b.scoreAfter}`,
    c5b);

  /* ---- C6：挡板反弹（向下 → 向上，且方向由击球点决定） ---- */
  const c6 = await evalJs(`(function(){
    var B=window.__breakout; B.restart(); B.setPaddle(400);
    B.setBall(400, 520, 0, 300);              // 正中挡板
    var before=B.getState();
    var after=B.simulate(300);
    var B2=window.__breakout; B2.restart(); B2.setPaddle(400);
    B2.setBall(445, 520, 0, 300);             // 击中挡板右半侧（板宽 110，跨度 345..455）
    var after2=B2.simulate(300);
    return {vyBefore:before.ball.vy,vyAfter:after.ball.vy,
            straightVx:after.ball.vx, rightHitVx:after2.ball.vx, rightHitVy:after2.ball.vy,
            paddleSpan:[before.paddle.x-before.paddle.w/2, before.paddle.x+before.paddle.w/2]};
  })()`);
  check('C6', '交互1c：球撞挡板后反向（vy<0）；击球点偏移产生横向速度',
    c6.vyBefore > 0 && c6.vyAfter < 0 && Math.abs(c6.straightVx) < 1 && c6.rightHitVx > 0 && c6.rightHitVy < 0,
    `正中 vy ${c6.vyBefore}→${c6.vyAfter} vx=${c6.straightVx.toFixed(2)}；右侧击中 vx=${c6.rightHitVx.toFixed(2)} vy=${c6.rightHitVy.toFixed(2)}；板跨度 ${c6.paddleSpan[0]}..${c6.paddleSpan[1]}`,
    c6);

  /* ---- C7：墙体反弹（单砖关卡，球路避开砖块） ---- */
  const c7 = await evalJs(`(function(){
    var B=window.__breakout; B.applyConfig({cols:10, rows:1, layout:['1000000000']});
    B.setBall(30,300,-300,0);  var a=B.simulate(300);     // 左下区域，远离砖块
    B.setBall(600,20,0,-300);  var b=B.simulate(300);     // 右上区域，远离砖块
    return {leftVx:a.ball.vx, leftX:a.ball.x, leftY:a.ball.y, rightAfterVx:a.ball.vx,
            topVy:b.ball.vy, topY:b.ball.y, topX:b.ball.x, bricksAlive:a.bricksAlive};
  })()`);
  check('C7', '交互1d：左右墙与顶墙反弹，球不越界',
    c7.leftVx > 0 && c7.leftX >= 8 - 0.5 && c7.topVy > 0 && c7.topY >= 8 - 0.5 && c7.bricksAlive === 1,
    `左墙 vx=-300→${c7.leftVx}，x=${c7.leftX.toFixed(2)}；顶墙 vy=-300→${c7.topVy}，y=${c7.topY.toFixed(2)}；砖块仍为 ${c7.bricksAlive}`,
    c7);

  /* ---- C8：分数实时显示（DOM 与内部状态一致） ---- */
  const c8 = await evalJs(`(function(){
    var B=window.__breakout;
    B.applyConfig({cols:3, rows:1, layout:['010'], basePoints:7});
    var bs=B.bricks(), t=null;
    for(var i=0;i<bs.length;i++){ if(bs[i].alive){t=bs[i];break;} }
    var s0=B.getState();
    var domStart=document.getElementById('score').textContent;
    B.setBall(t.x+t.w/2, t.y+t.h+s0.ball.r+2, 0, -300);
    var after=B.simulate(80);
    return {domStart:domStart, domAfter:document.getElementById('score').textContent, internal:after.score,
            expected:t.points, bricksAlive:after.bricksAlive, basePoints:7, rows:1};
  })()`);
  check('C8', '交互2：分数随击碎砖块递增且 DOM 实时显示与内部一致',
    Number(c8.domStart) === 0 && Number(c8.domAfter) === c8.internal && c8.internal === c8.expected && c8.internal > 0,
    `DOM ${c8.domStart}→${c8.domAfter}，内部 ${c8.internal}，单砖分值 ${c8.expected}（basePoints=${c8.basePoints} × 行系数）`, c8);

  /* ---- C9：键盘真实按键控制挡板 ---- */
  {
    await evalJs(`window.__breakout.restart(); window.__breakout.setBall(400,300,200,-150);`);
    const x0 = await evalJs('window.__breakout.getState().paddle.x');
    await key('keyDown', 'ArrowRight', 'ArrowRight', 39);
    await wait(500);
    const x1 = await evalJs('window.__breakout.getState().paddle.x');
    await key('keyUp', 'ArrowRight', 'ArrowRight', 39);
    await key('keyDown', 'a', 'KeyA', 65);
    await wait(500);
    const x2 = await evalJs('window.__breakout.getState().paddle.x');
    await key('keyUp', 'a', 'KeyA', 65);
    check('C9', '交互4：真实键盘事件（ArrowRight / A）驱动挡板左右移动',
      x1 > x0 + 20 && x2 < x1 - 20,
      `初始 ${x0.toFixed(1)} → 按→ ${x1.toFixed(1)} → 按A ${x2.toFixed(1)}`, { x0, x1, x2 });
  }

  /* ---- C10：真实鼠标移动控制挡板 ---- */
  {
    await evalJs(`window.__breakout.restart();`);
    const rect = await evalJs(`(function(){var r=document.getElementById('stage').getBoundingClientRect();return {l:r.left,t:r.top,w:r.width,h:r.height};})()`);
    const targetX = 700;
    const vx = rect.l + rect.w * (targetX / 800);
    const vy = rect.t + rect.h * 0.5;
    await cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: vx, y: vy, button: 'none', buttons: 0, pointerType: 'mouse' }, session);
    await wait(150);
    const px = await evalJs('window.__breakout.getState().paddle.x');
    const cdpMouseWorked = Math.abs(px - targetX) < 12;
    let px2 = null, domMouseWorked = false;
    if (!cdpMouseWorked) {
      await evalJs(`(function(){var c=document.getElementById('stage');var r=c.getBoundingClientRect();
        var x=r.left+r.width*(120/800), y=r.top+r.height*0.5;
        c.dispatchEvent(new PointerEvent('pointermove',{clientX:x,clientY:y,bubbles:true}));})()`);
      await wait(120);
      px2 = await evalJs('window.__breakout.getState().paddle.x');
      domMouseWorked = Math.abs(px2 - 120) < 12;
    }
    check('C10', '交互4b：鼠标移动驱动挡板跟随（CDP Input 或 PointerEvent 派发）',
      cdpMouseWorked || domMouseWorked,
      cdpMouseWorked ? `CDP 鼠标 x=700 → 挡板 ${px.toFixed(1)}` : `CDP 鼠标未生效，改用 PointerEvent → 挡板 ${px2}`,
      { cdpMouseWorked, px, px2, rect, channel: cdpMouseWorked ? 'Input.dispatchMouseEvent' : 'PointerEvent' });
  }

  /* ---- C11：暂停 / 继续（真实按键 + 按钮） ---- */
  {
    await evalJs(`window.__breakout.restart(); window.__breakout.setBall(400,300,200,-150);`);
    await key('keyDown', 'p', 'KeyP', 80); await key('keyUp', 'p', 'KeyP', 80);
    await wait(120);
    const p1 = await evalJs(`(function(){return {state:window.__breakout.getState().state,hidden:document.getElementById('overlay').hidden,btn:document.getElementById('ovBtn').textContent};})()`);
    await shot('11-paused');
    await key('keyDown', 'p', 'KeyP', 80); await key('keyUp', 'p', 'KeyP', 80);
    await wait(120);
    const p2 = await evalJs(`(function(){return {state:window.__breakout.getState().state,hidden:document.getElementById('overlay').hidden};})()`);
    // 用叠加层按钮再走一次 暂停→继续
    await key('keyDown', 'p', 'KeyP', 80); await key('keyUp', 'p', 'KeyP', 80);
    await wait(120);
    await evalJs(`document.getElementById('ovBtn').click()`);
    await wait(120);
    const p3 = await evalJs(`(function(){return {state:window.__breakout.getState().state,hidden:document.getElementById('overlay').hidden};})()`);
    check('C11', '交互3：暂停/继续（P 键与按钮均可），状态与遮罩同步',
      p1.state === 'paused' && p1.hidden === false && p1.btn === '继续' && p2.state === 'running' && p2.hidden === true && p3.state === 'running' && p3.hidden === true,
      `P键→${p1.state}(遮罩${p1.hidden ? '隐' : '显'},按钮「${p1.btn}」) →P键→${p2.state} →按钮→${p3.state}`, { p1, p2, p3 });
  }

  /* ---- C11b：开局遮罩按钮「开始游戏」真的开始（真实点击） ---- */
  {
    await newPage(fileUrl);
    const before = await evalJs(`(function(){var s=window.__breakout.getState();
      return {state:s.state,hidden:document.getElementById('overlay').hidden,btn:document.getElementById('ovBtn').textContent,speed:Math.abs(s.ball.vx)+Math.abs(s.ball.vy)};})()`);
    await evalJs(`document.getElementById('ovBtn').click()`);
    await wait(150);
    const after = await evalJs(`(function(){var s=window.__breakout.getState();
      return {state:s.state,hidden:document.getElementById('overlay').hidden,speed:Math.abs(s.ball.vx)+Math.abs(s.ball.vy)};})()`);
    check('C11b', '开局入口：点「开始游戏」后遮罩消失、进入进行中并真的发球',
      before.state === 'held' && before.hidden === false && before.btn === '开始游戏' && before.speed === 0 &&
      after.state === 'running' && after.hidden === true && after.speed > 100,
      `点击前 ${before.state}/遮罩${before.hidden ? '隐' : '显'}/球速${before.speed} → 点击后 ${after.state}/遮罩${after.hidden ? '隐' : '显'}/球速${after.speed.toFixed(0)}`,
      { before, after });
  }

  /* ---- C12：游戏结束 → 重开入口 → 真重开 ---- */
  {
    const over = await evalJs(`(function(){
      var B=window.__breakout; B.restart();
      var hits=[];
      for(var i=0;i<5;i++){ B.setBall(400,700,0,100); hits.push(B.simulate(20)); }
      var s=B.getState();
      return {state:s.state,lives:s.lives,hidden:document.getElementById('overlay').hidden,btn:document.getElementById('ovBtn').textContent,title:document.getElementById('ovTitle').textContent,score:s.score,text:document.getElementById('ovText').textContent};
    })()`);
    await shot('12-gameover');
    const after = await evalJs(`(function(){
      document.getElementById('ovBtn').click();
      var B=window.__breakout, s=B.getState();
      return {state:s.state,lives:s.lives,score:s.score,alive:s.bricksAlive,hidden:document.getElementById('overlay').hidden,ball:{x:s.ball.x,y:s.ball.y}};
    })()`);
    await wait(450);
    const border = await evalJs(`getComputedStyle(document.getElementById('stageWrap')).borderTopColor`);
    await shot('13-restarted');
    check('C12', '交互3b：球掉底扣命 → 生命耗尽显示结束与重开入口 → 点击真正重开',
      over.state === 'over' && over.lives === 0 && over.hidden === false && over.btn === '重新开始' &&
      after.state === 'held' && after.lives === 3 && after.score === 0 && after.alive > 0 && after.hidden === true,
      `结束态：${over.state}/命${over.lives}/按钮「${over.btn}」/文案「${over.text}」；重开后：${after.state}/命${after.lives}/分数${after.score}/砖块${after.alive}/遮罩${after.hidden ? '隐' : '显'}`,
      { over, after, border });
    check('C12b', '受击红框动画结束后不残留（重开后边框恢复常态色）',
      !/255,\s*107,\s*129/.test(border), `重开后 border-top-color = ${border}`, { border });
  }

  /* ---- C13：暂停时物理冻结 ---- */
  {
    const froze = await evalJs(`(function(){
      var B=window.__breakout; B.restart(); B.setBall(400,300,200,-150);
      B.simulate(50);
      var a=B.getState(); B.pause();
      B.simulate(500);
      var b=B.getState();
      return {x1:a.ball.x,y1:a.ball.y,x2:b.ball.x,y2:b.ball.y,state:b.state};
    })()`);
    check('C13', '暂停时物理确实冻结（simulate 不推进状态）',
      froze.x1 === froze.x2 && froze.y1 === froze.y2 && froze.state === 'paused',
      `暂停前(${froze.x1.toFixed(2)},${froze.y1.toFixed(2)}) 推进 500ms 后(${froze.x2.toFixed(2)},${froze.y2.toFixed(2)})`, froze);
  }

  /* ---- C14：边界 — 空数据 ---- */
  {
    await newPage(fileUrl + '?cfg=' + encodeURIComponent(JSON.stringify({ layout: [] })));
    const r = await evalJs(`(function(){var s=window.__breakout.getState();
      return {alive:s.bricksAlive,issues:s.issues,state:s.state,notice:document.getElementById('notice').textContent,canvas:window.__breakout.bricks().length};})()`);
    const e = await pageErrors();
    check('C14', '边界-空数据：layout=[] 不抛异常，回退为可玩关卡并给出提示',
      r.alive > 0 && r.state === 'held' && r.issues.length > 0 && /空/.test(r.issues.join()) && e.inPage.length === 0 && e.cdp.length === 0,
      `砖块 ${r.alive}，issues=${JSON.stringify(r.issues)}，页面内异常 ${e.inPage.length}`,
      { r, e });
  }

  /* ---- C15：边界 — 全 0 布局（等价空关卡） ---- */
  {
    await newPage(fileUrl + '?cfg=' + encodeURIComponent(JSON.stringify({ layout: ['0000000000', '0000000000'] })));
    const r = await evalJs(`(function(){var s=window.__breakout.getState();return {alive:s.bricksAlive,issues:s.issues};})()`);
    const e = await pageErrors();
    check('C15', '边界-空关卡（全 0 行）：回退默认关卡，不抛异常',
      r.alive > 0 && r.issues.join().indexOf('空') >= 0 && e.inPage.length === 0 && e.cdp.length === 0,
      `砖块 ${r.alive}，issues=${JSON.stringify(r.issues)}`, { r, e });
  }

  /* ---- C16：边界 — 超长文本 ---- */
  {
    const long = 'x'.repeat(500);
    await newPage(fileUrl + '?cfg=' + encodeURIComponent(JSON.stringify({ title: long })));
    const r = await evalJs(`(function(){var el=document.getElementById('levelName');
      return {len:el.textContent.length,scrollW:el.scrollWidth,clientW:el.clientWidth,issues:window.__breakout.getState().issues,
              internalTitle:window.__breakout.getState().levelTitle.length,overflow:getComputedStyle(el).textOverflow};})()`);
    const e = await pageErrors();
    const layoutOk = await evalJs(`(function(){var r=document.getElementById('hud').getBoundingClientRect(),a=document.getElementById('app').getBoundingClientRect();return r.right<=a.right+1;})()`);
    await shot('16-longtitle');
    check('C16', '边界-超长文本：500 字关卡名被截断，HUD 不撑破布局，无异常',
      r.len <= 24 && r.internalTitle <= 24 && r.overflow === 'ellipsis' && layoutOk && e.inPage.length === 0 && e.cdp.length === 0,
      `显示长度 ${r.len}（内部 ${r.internalTitle}），text-overflow=${r.overflow}，HUD 未溢出=${layoutOk}，异常 ${e.inPage.length}`,
      { r, e, layoutOk });
  }

  /* ---- C17：边界 — 非法输入（坏 JSON / 乱码） ---- */
  {
    await newPage(fileUrl + '?cfg=' + encodeURIComponent('{not-json'));
    const r = await evalJs(`(function(){var s=window.__breakout.getState();return {alive:s.bricksAlive,state:s.state,issues:s.issues,score:document.getElementById('score').textContent};})()`);
    await newPage(fileUrl + '?cfg=%E4%B8%AD%E6%96%87%E9%9D%9E%20JSON %%%%');
    const r2 = await evalJs(`(function(){var s=window.__breakout.getState();return {alive:s.bricksAlive,state:s.state,issues:s.issues};})()`);
    const e = await pageErrors();
    check('C17', '边界-非法输入：坏 JSON / 畸形百分号编码 → 回退默认并提示，不抛异常',
      r.alive > 0 && r.state === 'held' && r.issues.length > 0 && r2.alive > 0 && e.inPage.length === 0 && e.cdp.length === 0,
      `坏JSON：砖块${r.alive}/issues=${JSON.stringify(r.issues)}；畸形编码：砖块${r2.alive}/issues=${JSON.stringify(r2.issues)}`,
      { r, r2, e });
  }

  /* ---- C18：边界 — 非法数值（越界 / 非数字 / 超大 / 负数 / 错误类型） ---- */
  {
    await newPage(fileUrl + '?cfg=' + encodeURIComponent(JSON.stringify({
      cols: 99999, rows: -3, lives: 1e9, brickHP: 'abc', basePoints: null,
      ballSpeed: -1, paddleWidth: 'abc', title: {}, layout: 12345
    })));
    const r = await evalJs(`(function(){var s=window.__breakout.getState();
      return {state:s.state,alive:s.bricksAlive,lives:s.lives,paddleW:s.paddle.w,ballSpeed:s.ball.speed,issues:s.issues,rows:s.brickCount};})()`);
    const e = await pageErrors();
    check('C18', '边界-非法输入：越界/非数字/错误类型全部被钳制或回退，区间内且不抛异常',
      r.state === 'held' && r.alive > 0 && r.lives >= 1 && r.lives <= 9 && r.paddleW >= 40 && r.paddleW <= 400 &&
      r.ballSpeed >= 120 && r.ballSpeed <= 900 && r.issues.length >= 3 && e.inPage.length === 0 && e.cdp.length === 0,
      `命${r.lives}/板宽${r.paddleW}/球速${r.ballSpeed}/砖块${r.alive}/issues ${r.issues.length} 条/异常${e.inPage.length}`,
      { r, e });
  }

  /* ---- C19：边界 — 超宽/超行/含非法字符的布局 ---- */
  {
    await newPage(fileUrl + '?cfg=' + encodeURIComponent(JSON.stringify({ cols: 4, rows: 3, layout: ['11XX1111', '', 42, '111', null, '99999999999999'] })));
    const r = await evalJs(`(function(){var s=window.__breakout.getState();
      var bs=window.__breakout.bricks();var maxRight=0;for(var i=0;i<bs.length;i++){maxRight=Math.max(maxRight,bs[i].x+bs[i].w);}
      return {alive:s.bricksAlive,issues:s.issues,maxRight:maxRight,state:s.state};})()`);
    const e = await pageErrors();
    check('C19', '边界-非法布局：非法字符/空行/数字/null 行被剔除，列宽与超宽行被钳制，不越界不抛异常',
      r.state === 'held' && r.alive > 0 && r.maxRight <= 760.5 && r.issues.length > 0 && e.inPage.length === 0 && e.cdp.length === 0,
      `砖块${r.alive}，最右 ${r.maxRight.toFixed(1)}（场地右界 760），issues=${JSON.stringify(r.issues)}`, { r, e });
  }

  /* ---- C20：帧循环稳定性（真实 rAF 15 秒） + 无异常 ---- */
  {
    await newPage(fileUrl);
    await evalJs(`window.__breakout.restart(); window.__breakout.launch();`);
    const r = await evalJs(`new Promise(function(res){
      var n=0,t0=performance.now(),t=setInterval(function(){ if(performance.now()-t0>8000){clearInterval(t);res(n);} },200);
      (function f(){ n++; requestAnimationFrame(f); })();
    })`);
    const fps = r / 8;
    await shot('20-running');
    const s = await evalJs(`(function(){var s=window.__breakout.getState();return {state:s.state,frameRaf:window.__raf};})()`);
    const e = await pageErrors();
    check('C20', '交互5：主循环持续 8 秒无中断（帧率充足）+ 全程无未捕获异常',
      fps >= 30 && e.inPage.length === 0 && e.cdp.length === 0 && e.logs.length === 0,
      `8 秒内 ${r} 帧 ≈ ${fps.toFixed(1)} fps；页面内异常 ${e.inPage.length}，CDP 异常 ${e.cdp.length}，error 日志 ${e.logs.length}`,
      { frames: r, fps, e });
  }

  /* ---- C21：内存不持续增长（热身后 25 轮完整对局 + gc 前后对比） ---- */
  {
    const heap = await evalJs(`(function(){
      var B=window.__breakout;
      if (typeof gc === 'function') { gc(); gc(); }
      for(var w=0;w<5;w++){ B.restart(); B.launch(); B.simulate(20000); }
      if (typeof gc === 'function') { gc(); gc(); }
      var h0 = performance.memory ? performance.memory.usedJSHeapSize : null;
      var pools = B.stats();
      for(var i=0;i<25;i++){ B.restart(); B.launch(); B.simulate(20000); }
      if (typeof gc === 'function') { gc(); gc(); }
      var h1 = performance.memory ? performance.memory.usedJSHeapSize : null;
      var st = B.stats();
      return {h0:h0,h1:h1,delta:(h0!==null&&h1!==null)?(h1-h0):null,
              brickPoolBefore:pools.brickPoolLength,brickPoolAfter:st.brickPoolLength,
              brickArrayBefore:pools.brickArrayLength,brickArrayAfter:st.brickArrayLength,
              precise: !!(performance.memory&&performance.memory.jsHeapSizeLimit),hasGC: typeof gc==='function'};
    })()`);
    const ok = heap.delta !== null && heap.delta < 3 * 1024 * 1024 &&
      heap.brickPoolAfter === heap.brickPoolBefore && heap.brickArrayAfter === heap.brickArrayBefore;
    check('C21', '交互5b：25 轮完整对局后堆内存未持续增长，砖块池不膨胀',
      ok,
      `堆 ${heap.h0}→${heap.h1}（Δ${heap.delta} 字节）；砖块池 ${heap.brickPoolBefore}→${heap.brickPoolAfter}；数组长度 ${heap.brickArrayBefore}→${heap.brickArrayAfter}`,
      heap);
  }

  /* ---- C22：随机输入模糊测试（非法/极端输入不抛异常） ---- */
  {
    const fuzz = await evalJs(`(function(){
      var B=window.__breakout, errs=0, applied=0;
      var keysA=['a','d','ArrowLeft','ArrowRight','A','D',' ','p','P','r','R','Enter','F5','\u0000','\uD800','x'.repeat(300),'中文',{}];
      try{
        for(var i=0;i<400;i++){
          var k=keysA[i%keysA.length];
          B.key(k, i%2===0);
          if(i%7===0) B.setPaddle((i*97)%1601-400);
          if(i%11===0) B.setBall((i*53)%1200-200,(i*31)%900-100, (i%5-2)*900, (i%7-3)*900);
          if(i%23===0) B.simulate(120);
          if(i%29===0) { B.restart(); }
          if(i%37===0) { applied++; }
        }
        var nan=0; var s=B.getState();
        var nums=[s.ball.x,s.ball.y,s.ball.vx,s.ball.vy,s.paddle.x,s.score,s.lives];
        for(var j=0;j<nums.length;j++) if(!isFinite(nums[j])) nan++;
        return {errs:errs,nan:nan,state:s.state,score:s.score,lives:s.lives,loops:400,applied:applied};
      }catch(e){ return {errs:1,message:String(e&&e.message||e)}; }
    })()`);
    const e = await pageErrors();
    check('C22', '边界-模糊输入：400 次随机按键/极端数值/NaN 输入后状态仍有限且无异常',
      fuzz.errs === 0 && fuzz.nan === 0 && e.inPage.length === 0 && e.cdp.length === 0 && e.logs.length === 0,
      `异常 ${fuzz.errs}，非有限数值 ${fuzz.nan}，末态 ${fuzz.state}/分数${fuzz.score}/命${fuzz.lives}；页面内异常 ${e.inPage.length}`,
      { fuzz, e });
  }

  /* ---- C23：赢局路径（自上而下逐块击碎，球不会掉出底部） ---- */
  {
    const win = await evalJs(`(function(){
      var B=window.__breakout;
      B.applyConfig({cols:10, rows:6, lives:3, basePoints:10,
        layout:['1111111111','1111111111','0222222220','0222222220','0033333300','0000330000']});
      var guard=0, destroyed=0;
      while(B.getState().state!=='win' && guard<400){
        guard++;
        var s=B.getState();
        if(s.state==='over') break;
        var bs=B.bricks(), t=null;
        for(var i=0;i<bs.length;i++){ if(bs[i].alive){t=bs[i];break;} }
        if(!t) break;
        var before=s.bricksAlive;
        B.setBall(t.x+t.w/2, t.y-s.ball.r-2, 0, 300);   // 从砖块正上方朝下撞，撞后向上弹离底部
        B.simulate(80);
        if(B.getState().bricksAlive < before) destroyed++;
      }
      var s2=B.getState();
      return {state:s2.state,alive:s2.bricksAlive,score:s2.score,guard:guard,destroyed:destroyed,
              btn:document.getElementById('ovBtn').textContent,hidden:document.getElementById('overlay').hidden,
              title:document.getElementById('ovTitle').textContent,lives:s2.lives};
    })()`);
    await shot('23-win');
    check('C23', '通关路径：击碎全部砖块 → 通关遮罩 + 可重开入口（无掉命）',
      win.state === 'win' && win.alive === 0 && win.hidden === false && win.score > 0 && win.lives === 3,
      `state=${win.state} 剩余砖块=${win.alive} 分数=${win.score} 命=${win.lives} 按钮「${win.btn}」 逐块销毁 ${win.destroyed} 次/迭代 ${win.guard}`,
      win);
  }

  const fin = await evalJs('window.__errors ? window.__errors.slice() : ["no-collector"]');
  check('C24', '全流程汇总：所有用例执行完毕，页面内未捕获错误累计为 0',
    fin.length === 0, `window.__errors = ${JSON.stringify(fin)}`, { fin });

  /* ------------------------------ 收尾 ------------------------------ */
  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, JSON.stringify({ label: LABEL, app: APP, fileUrl, total: results.length, failed: failures, results }, null, 2));
  console.log(`\n== ${LABEL}: ${results.length - failures}/${results.length} 通过，失败 ${failures} ==`);
  console.log(`结果写入 ${OUT}`);
  try { ws.close(); } catch {}
  try { chromeProc.kill(); } catch {}
  try { rmSync(userDataDir, { recursive: true, force: true }); } catch {}
  process.exit(failures === 0 ? 0 : 1);
})().catch(async (err) => {
  console.error('HARNESS ERROR: ' + (err && err.stack || err));
  try { chromeProc && chromeProc.kill(); } catch {}
  try { userDataDir && rmSync(userDataDir, { recursive: true, force: true }); } catch {}
  process.exit(2);
});
