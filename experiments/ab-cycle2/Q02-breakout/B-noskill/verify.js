'use strict';
/**
 * app.html 自动化验收脚本
 * 用真实 Chrome(CDP over WebSocket，仅用 Node 内置模块)驱动页面，
 * 用真实输入事件(Input.dispatchKeyEvent / dispatchMouseEvent)验证交互，
 * 并收集所有未捕获异常。
 *
 * 运行: node verify.js
 */
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');

const APP = path.join(__dirname, 'app.html');
const PORT = 9400 + Math.floor(Math.random() * 400);
const PAGE_URL = 'file:///' + APP.replace(/\\/g, '/');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function pickBrowser() {
  const cands = [
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  ];
  for (const c of cands) if (fs.existsSync(c)) return c;
  return null;
}
function getJson(url) {
  return new Promise((res, rej) => {
    http.get(url, (r) => {
      let b = '';
      r.on('data', (d) => (b += d));
      r.on('end', () => { try { res(JSON.parse(b)); } catch (e) { rej(e); } });
    }).on('error', rej);
  });
}
function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    const pending = new Map();
    const events = [];
    const listeners = [];
    let id = 0;
    const api = {
      send(method, params) {
        const mid = ++id;
        return new Promise((res, rej) => {
          pending.set(mid, { res, rej });
          ws.send(JSON.stringify({ id: mid, method, params: params || {} }));
        });
      },
      on(fn) { listeners.push(fn); },
      events,
      close() { try { ws.close(); } catch (e) {} },
    };
    ws.addEventListener('open', () => resolve(api));
    ws.addEventListener('error', () => reject(new Error('websocket error')));
    ws.addEventListener('close', () => reject(new Error('websocket closed early')));
    ws.addEventListener('message', (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch (e) { return; }
      if (msg.id && pending.has(msg.id)) {
        const p = pending.get(msg.id); pending.delete(msg.id);
        if (msg.error) p.rej(new Error(JSON.stringify(msg.error))); else p.res(msg.result);
      } else if (msg.method) {
        events.push(msg);
        for (const l of listeners) { try { l(msg); } catch (e) {} }
      }
    });
  });
}

const results = [];
function check(name, pass, detail) {
  results.push({ name, pass: !!pass, detail: detail === undefined ? '' : String(detail) });
  const tag = pass ? 'PASS' : 'FAIL';
  console.log(`[${tag}] ${name}${detail !== undefined && detail !== '' ? '  -> ' + detail : ''}`);
}

const KEYS = {
  ArrowLeft: { key: 'ArrowLeft', code: 'ArrowLeft', vk: 37 },
  ArrowRight: { key: 'ArrowRight', code: 'ArrowRight', vk: 39 },
  Space: { key: ' ', code: 'Space', vk: 32 },
  KeyP: { key: 'p', code: 'KeyP', vk: 80 },
  KeyA: { key: 'a', code: 'KeyA', vk: 65 },
  KeyD: { key: 'd', code: 'KeyD', vk: 68 },
  Escape: { key: 'Escape', code: 'Escape', vk: 27 },
  Weird: { key: '\u0000', code: '', vk: 0 },
};

async function main() {
  const browser = pickBrowser();
  if (!browser) { console.log('找不到 Chrome/Edge'); process.exit(2); }
  const userDir = path.join(os.tmpdir(), 'bdv-' + Date.now());
  const child = spawn(browser, [
    '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--disable-extensions', '--mute-audio', '--allow-file-access-from-files',
    '--window-size=900,1000', '--remote-debugging-port=' + PORT,
    '--user-data-dir=' + userDir, PAGE_URL,
  ], { stdio: 'ignore' });

  let cdp;
  try {
    let target = null;
    for (let i = 0; i < 100 && !target; i++) {
      try {
        const list = await getJson(`http://127.0.0.1:${PORT}/json/list`);
        target = list.find((t) => t.type === 'page' && t.webSocketDebuggerUrl) || null;
      } catch (e) { /* 还没起来 */ }
      if (!target) await sleep(120);
    }
    if (!target) throw new Error('CDP 未就绪');
    cdp = await connect(target.webSocketDebuggerUrl);

    const runtimeErrors = [];
    const ignoredLogs = [];
    const netUrls = [];
    cdp.on((m) => {
      if (m.method === 'Runtime.exceptionThrown') {
        const d = m.params.exceptionDetails || {};
        runtimeErrors.push(String((d.exception && (d.exception.description || d.exception.value)) || d.text));
      }
      if (m.method === 'Log.entryAdded' && m.params.entry && m.params.entry.level === 'error') {
        const e = m.params.entry;
        const text = String(e.text || '');
        // 过滤环境噪声（file:// 下 favicon 必然 404，与被测页面无关）
        if (/favicon|ERR_FILE_NOT_FOUND/i.test(text) || e.source === 'deprecation') ignoredLogs.push(text);
        else runtimeErrors.push('log[' + e.source + ']: ' + text);
      }
      if (m.method === 'Network.requestWillBeSent' && m.params.request) netUrls.push(m.params.request.url);
    });
    await cdp.send('Runtime.enable');
    await cdp.send('Page.enable');
    await cdp.send('Log.enable');
    await cdp.send('Network.enable');

    const ev = async (expr) => {
      const r = await cdp.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
      if (r.exceptionDetails) {
        const d = r.exceptionDetails;
        throw new Error('页面内求值异常: ' + String((d.exception && d.exception.description) || d.text));
      }
      return r.result.value;
    };
    const keyDown = (k) => cdp.send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: k.key, code: k.code, windowsVirtualKeyCode: k.vk, nativeVirtualKeyCode: k.vk });
    const keyUp = (k) => cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: k.key, code: k.code, windowsVirtualKeyCode: k.vk, nativeVirtualKeyCode: k.vk });
    const tap = async (k) => { await keyDown(k); await keyUp(k); };
    const mouse = (type, x, y, button) => cdp.send('Input.dispatchMouseEvent', {
      type, x, y, button: button || 'none',
      buttons: type === 'mousePressed' ? 1 : 0,
      clickCount: type === 'mousePressed' || type === 'mouseReleased' ? 1 : 0,
    });
    const rectOf = (sel) => ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});
      if(!e) return null; const d=e.closest('details'); if(d) d.open=true;
      e.scrollIntoView({block:'center'});
      for(let i=0;i<4;i++){ const r=e.getBoundingClientRect();
        const need=r.top<2?r.top-20:(r.bottom>innerHeight-2?r.bottom-innerHeight+20:0);
        if(!need) break; window.scrollBy(0,need); }
      const r=e.getBoundingClientRect();
      return {x:r.left+r.width/2,y:r.top+r.height/2,w:r.width,h:r.height,
        vh:innerHeight,scrollY:window.scrollY,top:r.top,bottom:r.bottom};})()`);
    const clickEl = async (sel) => {
      let r = null, info = null;
      // <details> 刚展开时命中测试可能仍落在父节点，重试几次使其稳定
      for (let attempt = 0; attempt < 4; attempt++) {
        r = await rectOf(sel);
        if (!r || !r.w) throw new Error('找不到可点击元素 ' + sel);
        info = await ev(`(()=>{const el=document.elementFromPoint(${r.x},${r.y});
          const t=document.querySelector(${JSON.stringify(sel)});
          return {hit: el?(el.tagName+(el.id?'#'+el.id:'')):null, ok: !!(el&&t&&(el===t||t.contains(el)))};})()`);
        if (info.ok) break;
        await sleep(250);
      }
      if (!info.ok) {
        throw new Error(`点击坐标(${r.x.toFixed(0)},${r.y.toFixed(0)})命中的是 ${info.hit}，不是 ${sel}`
          + ` [top=${r.top.toFixed(0)},bottom=${r.bottom.toFixed(0)},vh=${r.vh},scrollY=${r.scrollY.toFixed(0)}]`);
      }
      await mouse('mouseMoved', r.x, r.y);
      await mouse('mousePressed', r.x, r.y, 'left');
      await mouse('mouseReleased', r.x, r.y, 'left');
      return r;
    };

    // 等待游戏初始化
    for (let i = 0; i < 60; i++) {
      const ok = await ev(`!!(window.Breakout && window.Breakout.state)`).catch(() => false);
      if (ok) break;
      await sleep(100);
    }

    /* ---------------- 1. 初始化状态 ---------------- */
    const init = await ev(`(()=>{const s=window.Breakout.state;return {status:s.status,score:s.score,lives:s.lives,
      bricks:s.bricks.length,left:s.bricksLeft,stuck:s.ball.stuck,overlayOn:document.getElementById('overlay').classList.contains('on'),
      hud:document.getElementById('hudStatus').textContent, scoreHud:document.getElementById('hudScore').textContent};})()`);
    check('1.1 初始状态为待开始、分数0、生命3', init.status === 'ready' && init.score === 0 && init.lives === 3, JSON.stringify(init));
    check('1.2 初始已生成砖块且未显示结束遮罩', init.bricks > 0 && init.left === init.bricks && init.overlayOn === false, `bricks=${init.bricks}`);
    check('1.3 HUD 状态文本为“待开始”', init.hud === '待开始', init.hud);

    /* ---------------- 2. 键盘发球 + 球在运动 ---------------- */
    await ev(`document.activeElement&&document.activeElement.blur()`);
    await tap(KEYS.Space);
    const afterLaunch = await ev(`(()=>{const s=window.Breakout.state;return {status:s.status,stuck:s.ball.stuck,y:s.ball.y};})()`);
    await sleep(200);
    const moved = await ev(`window.Breakout.state.ball.y`);
    check('2.1 空格发球：状态转为 running 且球脱离挡板', afterLaunch.status === 'running' && afterLaunch.stuck === false, JSON.stringify(afterLaunch));
    check('2.2 球在帧循环中真实移动', Math.abs(moved - afterLaunch.y) > 5, `Δy=${(moved - afterLaunch.y).toFixed(1)}`);

    /* ---------------- 3. 键盘控制挡板 ---------------- */
    await ev(`(()=>{const s=window.Breakout.state;s.status='running';s.paddle.x=240;s.paddle.targetX=null;return 1;})()`);
    await keyDown(KEYS.ArrowLeft);
    await sleep(300);
    await keyUp(KEYS.ArrowLeft);
    const xL = await ev(`window.Breakout.state.paddle.x`);
    await ev(`(()=>{const s=window.Breakout.state;s.paddle.targetX=null;return 1;})()`);
    await keyDown(KEYS.KeyD);
    await sleep(300);
    await keyUp(KEYS.KeyD);
    const xR = await ev(`window.Breakout.state.paddle.x`);
    check('3.1 键盘 ←/D 可移动挡板（左移/右移都生效）', xL < 238 && xR > xL + 40, `x=${xL.toFixed(1)} -> ${xR.toFixed(1)}`);

    /* ---------------- 4. 鼠标控制挡板 ---------------- */
    const cRect = await ev(`(()=>{const r=document.getElementById('cv').getBoundingClientRect();return {left:r.left,width:r.width};})()`);
    const moveTo = async (ratio) => {
      const px = cRect.left + cRect.width * ratio;
      await mouse('mouseMoved', px, 300);
      await sleep(200);
      return ev(`window.Breakout.state.paddle.x`);
    };
    const m20 = await moveTo(0.2);
    const m80 = await moveTo(0.8);
    const exp20 = 480 * 0.2, exp80 = 480 * 0.8;
    check('4.1 鼠标移动可控制挡板（与横向位置一致，误差<20px）',
      Math.abs(m20 - exp20) < 20 && Math.abs(m80 - exp80) < 20,
      `期望≈${exp20}/${exp80}，实测 ${m20.toFixed(1)}/${m80.toFixed(1)}`);

    /* ---------------- 5. 碰撞反向 + 计分 ---------------- */
    const before = await ev(`(()=>{const s=window.Breakout.state;s.status='running';
      let lo=null;for(const b of s.bricks){if(b.alive&&(!lo||b.row>lo.row))lo=b;}
      s.ball.stuck=false;s.ball.x=lo.x+lo.w/2;s.ball.y=lo.y+lo.h+s.ball.r+3;
      s.ball.vx=0;s.ball.vy=-260;s.ball.speed=260;
      return {score:s.score,left:s.bricksLeft,vy:s.ball.vy,hits:s.hits};})()`);
    await sleep(260);
    const after = await ev(`(()=>{const s=window.Breakout.state;return {score:s.score,left:s.bricksLeft,vy:s.ball.vy,
      hud:document.getElementById('hudScore').textContent,lastHit:s.lastHit};})()`);
    check('5.1 球打中砖块后反向（vy 由负变正）', before.vy < 0 && after.vy > 0, `vy: ${before.vy} -> ${after.vy.toFixed(1)}`);
    check('5.2 击碎砖块后分数递增、砖块数减少', after.score > before.score && after.left === before.left - 1,
      `score ${before.score}->${after.score}, left ${before.left}->${after.left}`);
    check('5.3 分数实时显示在 HUD 上', after.hud === String(after.score), `HUD=${after.hud}`);

    /* 5.4 侧面撞击：vx 反向（用两块砖的自定义关卡，避免直接过关） */
    const side0 = await ev(`(()=>{const B=window.Breakout;B.applyLevel('...#.#');const s=B.state;
      const k=s.bricks[0];
      s.status='running'; s.ball.stuck=false;
      s.ball.x=k.x-s.ball.r-4; s.ball.y=k.y+k.h/2; s.ball.vx=200; s.ball.vy=0; s.ball.speed=200;
      return {kx:k.x,col:k.col,left:s.bricksLeft,vx:s.ball.vx};})()`);
    await sleep(320);
    const side1 = await ev(`(()=>{const s=window.Breakout.state;return {vx:s.ball.vx,left:s.bricksLeft,lastHit:s.lastHit,errs:s.errors.length};})()`);
    check('5.4 球从侧面撞砖块时 vx 反向（水平分量翻转）', side0.left === 2 && side1.vx < 0 && side1.left === 1,
      `level=${JSON.stringify(side0)} -> vx=${side1.vx.toFixed(1)}, left=${side1.left}`);

    /* ---------------- 6. 暂停 / 继续 ---------------- */
    await ev(`(()=>{const s=window.Breakout.state;s.status='running';s.ball.stuck=false;s.ball.vx=120;s.ball.vy=-200;return 1;})()`);
    await clickEl('#btnPause');
    await sleep(60);
    const p1 = await ev(`(()=>{const s=window.Breakout.state;return {status:s.status,x:s.ball.x,y:s.ball.y,
      hud:document.getElementById('hudStatus').textContent,label:document.getElementById('btnPause').textContent};})()`);
    await sleep(450);
    const p2 = await ev(`(()=>{const s=window.Breakout.state;return {x:s.ball.x,y:s.ball.y};})()`);
    check('6.1 点击“暂停”进入已暂停状态并有明确反馈', p1.status === 'paused' && p1.hud === '已暂停' && p1.label === '继续', JSON.stringify(p1));
    check('6.2 暂停时画面冻结（球坐标不变）', Math.abs(p2.x - p1.x) < 0.001 && Math.abs(p2.y - p1.y) < 0.001,
      `Δ=(${(p2.x - p1.x).toFixed(3)},${(p2.y - p1.y).toFixed(3)})`);
    await tap(KEYS.KeyP);
    await sleep(200);
    const p3 = await ev(`(()=>{const s=window.Breakout.state;return {status:s.status,hud:document.getElementById('hudStatus').textContent,x:s.ball.x};})()`);
    check('6.3 P 键可继续且球恢复运动', p3.status === 'running' && p3.hud === '进行中' && Math.abs(p3.x - p2.x) > 1, JSON.stringify(p3));
    await tap(KEYS.Space);
    await sleep(60);
    const p4 = await ev(`window.Breakout.state.status`);
    await tap(KEYS.Space);
    await sleep(60);
    const p5 = await ev(`window.Breakout.state.status`);
    check('6.4 空格可切换暂停/继续', p4 === 'paused' && p5 === 'running', `${p4} -> ${p5}`);

    /* ---------------- 7. 游戏结束 + 真正重开 ---------------- */
    await ev(`(()=>{const s=window.Breakout.state;s.score=123;s.lives=1;s.status='running';
      s.ball.stuck=false;s.ball.x=240;s.ball.y=624;s.ball.vx=0;s.ball.vy=320;s.ball.speed=320;return 1;})()`);
    await sleep(500);
    const over = await ev(`(()=>{const s=window.Breakout.state;return {status:s.status,lives:s.lives,
      on:document.getElementById('overlay').classList.contains('on'),
      title:document.getElementById('ovTitle').textContent,btn:document.getElementById('ovBtn').textContent,
      shown:document.getElementById('ovScore').textContent,display:getComputedStyle(document.getElementById('overlay')).display};})()`);
    check('7.1 生命耗尽后进入结束状态', over.status === 'over' && over.lives === 0, JSON.stringify(over));
    check('7.2 结束遮罩可见并给出重开入口', over.on === true && over.display !== 'none' && over.btn.indexOf('重新开始') === 0 && over.shown === '123',
      `title=${over.title}, btn=${over.btn}`);
    await clickEl('#ovBtn');
    await sleep(200);
    const rst = await ev(`(()=>{const s=window.Breakout.state;return {status:s.status,score:s.score,lives:s.lives,
      left:s.bricksLeft,total:s.brickTotal,on:document.getElementById('overlay').classList.contains('on'),
      stuck:s.ball.stuck,hud:document.getElementById('hudScore').textContent};})()`);
    check('7.3 点击重开后状态与数据完全重置', rst.status === 'ready' && rst.score === 0 && rst.lives === 3 &&
      rst.left === rst.total && rst.on === false && rst.stuck === true && rst.hud === '0', JSON.stringify(rst));

    /* ---------------- 7b. 过关路径（最后一砖 -> 下一关） ---------------- */
    await ev(`(()=>{const s=window.Breakout.state;
      for(let i=1;i<s.bricks.length;i++) s.bricks[i].alive=false;
      s.bricks[0].alive=true; s.bricks[0].hp=1;
      s.bricksLeft=1; s.lives=3; s.status='running'; s.ball.stuck=false;
      const k=s.bricks[0];
      s.ball.x=k.x+k.w/2; s.ball.y=k.y+k.h+s.ball.r+3;
      s.ball.vx=0; s.ball.vy=-260; s.ball.speed=260; return 1;})()`);
    await sleep(320);
    const win = await ev(`(()=>{const s=window.Breakout.state;return {status:s.status,left:s.bricksLeft,
      on:document.getElementById('overlay').classList.contains('on'),
      btn:document.getElementById('ovBtn').textContent,title:document.getElementById('ovTitle').textContent};})()`);
    check('7.4 打掉最后一块砖进入过关状态', win.status === 'win' && win.left === 0 && win.on === true, JSON.stringify(win));
    check('7.5 过关遮罩给出“下一关”入口', win.btn === '下一关' && win.title === '过关！', `${win.title}/${win.btn}`);
    await clickEl('#ovBtn');
    await sleep(200);
    const nx = await ev(`(()=>{const s=window.Breakout.state;return {level:s.levelIndex,total:s.brickTotal,left:s.bricksLeft,
      status:s.status,on:document.getElementById('overlay').classList.contains('on')};})()`);
    check('7.6 点击“下一关”真的进入下一关', nx.level === 1 && nx.total > 0 && nx.left === nx.total && nx.on === false, JSON.stringify(nx));

    /* ---------------- 8. 生命扣减后可再次发球 ---------------- */
    await ev(`(()=>{const s=window.Breakout.state;s.lives=3;s.status='running';
      s.ball.stuck=false;s.ball.x=240;s.ball.y=628;s.ball.vx=0;s.ball.vy=340;s.ball.speed=340;return 1;})()`);
    await sleep(400);
    const life = await ev(`(()=>{const s=window.Breakout.state;return {lives:s.lives,status:s.status,stuck:s.ball.stuck,
      dy:s.paddle.y-s.ball.y};})()`);
    check('8.1 漏球扣 1 命并回到待发球（球吸附挡板）',
      life.lives === 2 && life.status === 'ready' && life.stuck === true && life.dy > 0, JSON.stringify(life));

    /* ---------------- 9. 边界：空数据 ---------------- */
    await ev(`document.getElementById('levelInput').value=''`);
    await clickEl('#btnApply');
    await sleep(100);
    const emptyRes = await ev(`(()=>{const s=window.Breakout.state;return {left:s.bricksLeft,status:s.status,
      notice:s.notice,noticeDom:document.getElementById('notice').textContent};})()`);
    check('9.1 空关卡不崩溃并回退默认关卡', emptyRes.left > 0 && emptyRes.notice.indexOf('空数据') === 0, JSON.stringify(emptyRes));
    check('9.2 空数据提示已显示在页面上', emptyRes.noticeDom.length > 0 && emptyRes.noticeDom.indexOf('空数据') >= 0, emptyRes.noticeDom);

    /* ---------------- 10. 边界：无砖块关卡 ---------------- */
    await ev(`document.getElementById('levelInput').value='....\\n....\\n....'`);
    await clickEl('#btnApply');
    const noBrick = await ev(`window.Breakout.state.notice`);
    check('10.1 全部为空格的关卡同样回退默认', noBrick.indexOf('空数据') === 0, noBrick);

    /* ---------------- 11. 边界：非法输入（类型） ---------------- */
    const badTypes = await ev(`(()=>{const B=window.Breakout;const out=[];
      const vals=[null,undefined,123,-0.5,NaN,true,{},[],[['#']],function(){},new Date(),/x/];
      for(const v of vals){ try{ B.applyLevel(v); out.push({t:Object.prototype.toString.call(v),notice:B.state.notice,left:B.state.bricksLeft}); }
        catch(e){ out.push({t:String(v),notice:'THROW: '+e.message,left:-1}); } }
      return out;})()`);
    const threw = badTypes.filter((r) => String(r.notice).indexOf('THROW') === 0 || r.left <= 0);
    check('11.1 非法类型输入（null/数字/对象/数组/函数/日期/正则）均不抛异常且回退',
      threw.length === 0, `样例=${badTypes.length}, 失败=${threw.length}`);
    check('11.2 非法输入提示文案可见', badTypes.every((r) => String(r.notice).indexOf('非法输入') === 0 || String(r.notice).indexOf('空数据') === 0),
      JSON.stringify(badTypes.slice(0, 3)));

    /* ---------------- 12. 边界：超长文本 ---------------- */
    const huge = await ev(`(()=>{const B=window.Breakout;const out=[];
      let t0=performance.now(); B.applyLevel('#'.repeat(200000)); out.push(Math.round(performance.now()-t0));
      const rows=[]; for(let i=0;i<5000;i++) rows.push('###.'); 
      t0=performance.now(); B.applyLevel(rows.join('\\n')); out.push(Math.round(performance.now()-t0));
      t0=performance.now(); B.applyLevel('#'+'@'.repeat(199999)); out.push(Math.round(performance.now()-t0));
      const s=B.state; return {ms:out,left:s.bricksLeft,total:s.brickTotal,notice:s.notice,bricks:s.bricks.length};})()`);
    check('12.1 超长文本（20万字符/5000行）不抛异常且耗时<1s',
      huge.ms.every((m) => m < 1000) && huge.bricks > 0, `耗时=${huge.ms.join('/')}ms, bricks=${huge.bricks}`);
    check('12.2 超长/超行数被截断并提示', /截断|忽略/.test(huge.notice), huge.notice);
    check('12.3 砖块数不超过网格上限 12x12', huge.bricks <= 144, `bricks=${huge.bricks}`);

    /* ---------------- 13. 边界：非法字符 / 结构 ---------------- */
    await ev(`document.getElementById('levelInput').value='@@##\\n中文砖块😀test\\n.###.'`);
    await clickEl('#btnApply');
    const inv = await ev(`(()=>({notice:window.Breakout.state.notice,left:window.Breakout.state.bricksLeft,status:window.Breakout.state.status}))()`);
    check('13.1 非法字符（符号/中文/emoji）被按空格处理且提示', inv.left > 0 && inv.notice.indexOf('非法字符') >= 0, JSON.stringify(inv));

    /* ---------------- 14. 纯函数 parseLevel 的异常输入 ---------------- */
    const pure = await ev(`(()=>{const p=window.Breakout.parseLevel;const out=[];
      const vals=[null,undefined,NaN,123,'',{a:1},[],'\\n\\n\\n','   ','@#$','x'.repeat(50000)];
      for(const v of vals){ try{ const r=p(v); out.push({ok:r.ok,bricks:r.warn.brickCount}); }catch(e){ out.push({ok:'THROW'}); } }
      return out;})()`);
    check('14.1 parseLevel 对任意输入都不抛异常', pure.every((r) => r.ok !== 'THROW'), JSON.stringify(pure));

    /* ---------------- 15. 帧循环稳定性 ---------------- */
    await ev(`window.Breakout.applyDefaultLevel()`);
    const stability = await ev(`(()=>{const B=window.Breakout,s=B.state;
      const base={parts:s.particles.length,bricks:s.bricks.length,frame:s.frame};
      window.__lc = 0; const orig = EventTarget.prototype.addEventListener;
      EventTarget.prototype.addEventListener = function(){ window.__lc++; return orig.apply(this, arguments); };
      return base;})()`);
    await ev(`(()=>{const B=window.Breakout;const s=B.state;s.lives=99999;s.status='running';
      window.__drive=setInterval(()=>{const st=B.state;if(st.status==='ready')B.start();},150);return 1;})()`);
    const heap0 = await ev(`performance.memory?performance.memory.usedJSHeapSize:null`);
    await sleep(5000);
    const after5s = await ev(`(()=>{const B=window.Breakout,s=B.state;return {parts:s.particles.length,bricks:s.bricks.length,
      frame:s.frame,errs:B.errors().length,listeners:window.__lc,score:s.score,bricksLeft:s.bricksLeft,
      finite:isFinite(s.ball.x)&&isFinite(s.ball.y)&&isFinite(s.score)&&isFinite(s.paddle.x),
      canvas:document.querySelectorAll('canvas').length,status:s.status,heap:performance.memory?performance.memory.usedJSHeapSize:null};})()`);
    await ev(`clearInterval(window.__drive)`);
    check('15.1 5 秒连续运行无未捕获异常且数值有效',
      after5s.errs === 0 && runtimeErrors.length === 0 && after5s.finite === true,
      `errors=${after5s.errs}, runtime=${runtimeErrors.length}, finite=${after5s.finite}`);
    check('15.2 帧数持续增长（帧循环在跑）', after5s.frame - stability.frame > 100, `frames=${after5s.frame - stability.frame}`);
    check('15.3 无内存持续增长：粒子池/砖块数组长度恒定，运行期不再注册事件监听',
      after5s.parts === stability.parts && after5s.bricks === stability.bricks && after5s.listeners === 0,
      `particles ${stability.parts}->${after5s.parts}, bricks ${stability.bricks}->${after5s.bricks}, newListeners=${after5s.listeners}`);
    check('15.4 只有 1 个 canvas（渲染资源不重复创建）', after5s.canvas === 1, `canvas=${after5s.canvas}`);
    if (heap0 && after5s.heap) {
      const grow = (after5s.heap - heap0) / 1048576;
      check('15.5 [参考] 5 秒堆内存增量 < 30MB', grow < 30, `Δheap=${grow.toFixed(2)}MB`);
    }

    /* ---------------- 16. 长时间定步长仿真（含多关卡、碰撞、胜负路径） ---------------- */
    const sim = await ev(`(()=>{const B=window.Breakout,s=B.state;
      s.lives=99999;s.score=0;s.status='running';s.ball.stuck=false;
      s.ball.x=240;s.ball.y=420;s.ball.vx=170;s.ball.vy=-230;s.ball.speed=280;
      let err=null,transitions=0,last=s.status;const t0=performance.now();
      try{
        for(let i=0;i<30000;i++){
          if(s.status==='ready') B.start();
          else if(s.status==='win') B.nextLevel();
          B.stepGame(s,1/120);
          if(s.status!==last){transitions++;last=s.status;}
        }
      }catch(e){err=String((e&&e.message)||e);}
      return {err,ms:Math.round(performance.now()-t0),frame:s.frame,parts:s.particles.length,bricks:s.bricks.length,
        finite:isFinite(s.ball.x)&&isFinite(s.ball.y)&&isFinite(s.score)&&isFinite(s.paddle.x),
        score:s.score,status:s.status,transitions,errs:B.errors().length,hits:s.hits};})()`);
    check('16.1 30000 步定步长仿真（约250秒游戏时间）无异常', sim.err === null && sim.finite === true, JSON.stringify({ err: sim.err, finite: sim.finite, ms: sim.ms, hits: sim.hits }) );
    check('16.2 仿真中经历多次状态切换（碰撞/过关/重开路径被覆盖）', sim.transitions >= 3, `transitions=${sim.transitions}, status=${sim.status}`);
    check('16.3 仿真后内存结构仍有界（粒子池恒定、砖块<=144）', sim.parts === stability.parts && sim.bricks <= 144, `particles=${sim.parts}, bricks=${sim.bricks}`);

    /* ---------------- 17. 非法输入：键盘 / 指针 ---------------- */
    await ev(`document.activeElement&&document.activeElement.blur()`);
    let keySurvived = true;
    try {
      for (const k of [KEYS.Weird, { key: 'F13', code: 'F13', vk: 124 }, { key: 'Unidentified', code: '', vk: 0 }]) {
        await keyDown(k); await keyUp(k);
      }
      await cdp.send('Input.dispatchKeyEvent', { type: 'rawKeyDown', windowsVirtualKeyCode: 65, nativeVirtualKeyCode: 65 });
      await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', windowsVirtualKeyCode: 65, nativeVirtualKeyCode: 65 });
    } catch (e) { keySurvived = false; }
    const keyState = await ev(`(()=>{const s=window.Breakout.state;return {ok:isFinite(s.paddle.x)&&!!s.status,errs:window.Breakout.errors().length};})()`);
    check('17.1 非法/异常键盘事件不抛异常', keySurvived && keyState.ok && keyState.errs === 0, JSON.stringify(keyState));

    const ptr = await ev(`(()=>{const B=window.Breakout,s=B.state,cv=document.getElementById('cv');const r=[];
      // 浏览器不允许构造 clientX 非有限的 PointerEvent，故构造后改写属性，把非法值真实送进监听器
      const mk=(x)=>{try{const e=new PointerEvent('pointermove',{bubbles:true});Object.defineProperty(e,'clientX',{value:x});
        cv.dispatchEvent(e);return 'ok';}catch(err){return 'THROW:'+err.message;}};
      r.push(mk(NaN),mk(Infinity),mk(-Infinity),mk(-1e9),mk(1e9),mk(undefined),mk('abc'),mk(null),mk({}),mk([]),mk(300));
      try{cv.dispatchEvent(new Event('pointermove',{bubbles:true}));r.push('ok');}catch(err){r.push('THROW:'+err.message);}
      try{const e=new PointerEvent('pointerdown',{bubbles:true});Object.defineProperty(e,'clientX',{value:Infinity});cv.dispatchEvent(e);r.push('ok');}catch(err){r.push('THROW:'+err.message);}
      return {r,px:s.paddle.x,target:s.paddle.targetX,status:s.status,errs:B.errors().length};})()`);
    check('17.2 非法指针坐标被夹取在场地内且不抛异常',
      ptr.r.every((x) => x === 'ok') && ptr.px >= 56 && ptr.px <= 424 && ptr.errs === 0,
      `results=${JSON.stringify(ptr.r)}, paddle.x=${ptr.px}, status=${ptr.status}, errs=${ptr.errs}`);

    /* ---------------- 18. 离线/无外部依赖 ---------------- */
    const html = fs.readFileSync(APP, 'utf8');
    const attrRe = /<(?:script|link|img|iframe|audio|video|source)\b[^>]*\b(?:src|href)\s*=/gi;
    const externals = html.match(attrRe) || [];
    const urlsInFile = html.match(/https?:\/\/[^\s"'<)]+/gi) || [];
    const netHttp = netUrls.filter((u) => /^https?:/i.test(u));
    check('18.1 页面无外链资源（无 <script src>/<link href>/CDN）', externals.length === 0, `匹配到=${JSON.stringify(externals)}`);
    check('18.1b 文件内不含任何 http(s) URL', urlsInFile.length === 0, JSON.stringify(urlsInFile.slice(0, 3)));
    check('18.2 未发起任何 http(s) 网络请求（离线可运行）',
      netHttp.length === 0 && netUrls.every((u) => u === PAGE_URL || u.indexOf('file:///') === 0),
      `请求=${netUrls.length}: ${JSON.stringify(netUrls.slice(0, 4))}`);
    check('18.3 无 script[src]/link/img/iframe 等外部节点',
      (await ev(`document.querySelectorAll('script[src],link[rel=stylesheet],img,iframe,audio,video').length`)) === 0);

    /* ---------------- 19. 最终异常账本 ---------------- */
    const finalErrors = await ev(`window.Breakout.errors()`);
    check('19.1 全程未出现未捕获异常（页面自记账 + CDP 双通道）',
      finalErrors.length === 0 && runtimeErrors.length === 0,
      `页面记账=${JSON.stringify(finalErrors)}, CDP=${JSON.stringify(runtimeErrors)}`);

    const pass = results.filter((r) => r.pass).length;
    console.log('\n================ 汇总 ================');
    console.log(`通过 ${pass}/${results.length}`);
    const failed = results.filter((r) => !r.pass);
    if (failed.length) failed.forEach((f) => console.log('  FAIL: ' + f.name + ' | ' + f.detail));
    fs.writeFileSync(path.join(__dirname, 'verify-result.json'), JSON.stringify({ total: results.length, pass, failed, results }, null, 2), 'utf8');
    console.log('明细已写入 verify-result.json');
    cdp.close();
  } catch (e) {
    console.log('运行失败: ' + (e && e.stack || e));
    process.exitCode = 1;
  } finally {
    try { cdp && cdp.close(); } catch (e) {}
    try { child.kill(); } catch (e) {}
    await sleep(300);
    try { fs.rmSync(userDir, { recursive: true, force: true }); } catch (e) {}
  }
  if (results.some((r) => !r.pass)) process.exitCode = 1;
  process.exit(process.exitCode || 0);   // 显式退出，避免 CDP/子进程句柄让 node 挂住
}

main();
