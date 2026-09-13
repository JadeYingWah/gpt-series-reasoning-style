'use strict';
/** 截图冒烟检查：把初始态 / 进行态 / 暂停态 / 结束态各存一张 PNG */
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');

const APP = path.join(__dirname, 'app.html');
const OUT = path.join(__dirname, 'shots');
const PORT = 9800 + Math.floor(Math.random() * 200);
const PAGE_URL = 'file:///' + APP.replace(/\\/g, '/');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function pickBrowser() {
  const cands = [
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  ];
  for (const c of cands) if (fs.existsSync(c)) return c;
  return null;
}
function getJson(url) {
  return new Promise((res, rej) => {
    http.get(url, (r) => { let b = ''; r.on('data', (d) => (b += d)); r.on('end', () => { try { res(JSON.parse(b)); } catch (e) { rej(e); } }); }).on('error', rej);
  });
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const userDir = path.join(os.tmpdir(), 'shot-' + Date.now());
  const child = spawn(pickBrowser(), ['--headless=new', '--disable-gpu', '--no-first-run', '--mute-audio',
    '--allow-file-access-from-files', '--window-size=560,1300',
    '--remote-debugging-port=' + PORT, '--user-data-dir=' + userDir, PAGE_URL], { stdio: 'ignore' });
  let ws;
  try {
    let t = null;
    for (let i = 0; i < 100 && !t; i++) {
      try { t = (await getJson(`http://127.0.0.1:${PORT}/json/list`)).find((x) => x.type === 'page'); } catch (e) {}
      if (!t) await sleep(120);
    }
    ws = new WebSocket(t.webSocketDebuggerUrl);
    const pending = new Map(); let id = 0;
    await new Promise((res) => ws.addEventListener('open', res));
    ws.addEventListener('message', (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id); }
    });
    const send = (method, params) => new Promise((res) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params: params || {} })); });
    const ev = async (e) => (await send('Runtime.evaluate', { expression: e, returnByValue: true })).result.value;
    const shot = async (name) => {
      const { data } = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
      fs.writeFileSync(path.join(OUT, name), Buffer.from(data, 'base64'));
      console.log('saved ' + name);
    };
    await send('Runtime.enable');
    await send('Page.enable');
    for (let i = 0; i < 50; i++) { if (await ev('!!(window.Breakout && window.Breakout.state)')) break; await sleep(100); }
    await sleep(300);
    await shot('01-ready.png');
    await ev(`window.Breakout.start()`);
    await sleep(1200);
    await shot('02-running.png');
    await ev(`window.Breakout.state.status='running'; window.Breakout.applyLevel('2.2.2.2.2.2.\\n.3.#.#.#.3..\\n..#2#2#2#...\\n.33..#..33..\\n2.2.2.2.2.2.'); window.Breakout.start()`);
    await sleep(1500);
    await shot('03-custom-level.png');
    await ev(`window.Breakout.togglePause()`);
    await sleep(200);
    await shot('04-paused.png');
    await ev(`(()=>{const s=window.Breakout.state;s.lives=1;s.status='running';s.ball.stuck=false;s.ball.x=240;s.ball.y=624;s.ball.vy=320;s.ball.vx=0;return 1;})()`);
    await sleep(600);
    await shot('05-gameover.png');
  } catch (e) {
    console.log('截图失败: ' + (e && e.message || e));
  } finally {
    try { ws && ws.close(); } catch (e) {}
    try { child.kill(); } catch (e) {}
    await sleep(300);
    try { fs.rmSync(userDir, { recursive: true, force: true }); } catch (e) {}
  }
  process.exit(0);
})();
