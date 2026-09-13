/* 临时插桩：逐步记录物理演化（验证工装的诊断工具，不属于交付物） */
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const APP = resolve(process.argv[2] || 'app.html');
const PORT = 9777;
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const udd = mkdtempSync(join(tmpdir(), 'dbg-'));
const proc = spawn(process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  ['--headless=new', '--disable-gpu', `--remote-debugging-port=${PORT}`, `--user-data-dir=${udd}`,
   '--no-first-run', 'about:blank'], { stdio: 'ignore' });
let info;
for (let i = 0; i < 80; i++) { try { const r = await fetch(`http://127.0.0.1:${PORT}/json/version`); if (r.ok) { info = await r.json(); break; } } catch {} await wait(250); }
const ws = new WebSocket(info.webSocketDebuggerUrl);
await new Promise((res) => ws.addEventListener('open', res));
let seq = 0; const pending = new Map();
ws.addEventListener('message', (ev) => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { const p = pending.get(m.id); pending.delete(m.id); m.error ? p.rej(new Error(JSON.stringify(m.error))) : p.res(m.result); } });
const send = (method, params = {}, sessionId) => new Promise((res, rej) => { const id = ++seq; pending.set(id, { res, rej }); ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) })); });
const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
await send('Page.enable', {}, sessionId); await send('Runtime.enable', {}, sessionId);
await send('Page.navigate', { url: pathToFileURL(APP).href }, sessionId);
await wait(1500);
const ev = async (expr) => { const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }, sessionId); if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text); return r.result.value; };

const log = await ev(`(function(){
  var B=window.__breakout; B.restart();
  var s0=B.getState();
  var t=B.bricks()[0];
  B.setBall(t.x+t.w/2, t.y+t.h+t.r+2, 0, -300);
  var log=[];
  for(var i=0;i<14;i++){
    var a=B.getState();
    B.simulate(1000/120);
    var b=B.getState();
    log.push({i:i, before:[+a.ball.x.toFixed(2),+a.ball.y.toFixed(2),a.ball.vx,a.ball.vy,a.bricksAlive,a.state],
                   after:[+b.ball.x.toFixed(2),+b.ball.y.toFixed(2),b.ball.vx,b.ball.vy,b.bricksAlive,b.state]});
  }
  return {stepsPerCall: Math.round((1000/120)/1000/(1/120)), brick:{x:t.x,y:t.y,w:t.w,h:t.h}, log:log};
})()`);
console.log(JSON.stringify(log, null, 1));
ws.close(); proc.kill(); rmSync(udd, { recursive: true, force: true });
