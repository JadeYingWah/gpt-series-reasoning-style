// DIR01 · A 臂 · 证据脚本（可复跑）
// 用法：node evidence/verify.mjs
// 1) 静态核对 art.html（体积 / keyframes / SMIL / 外部引用）
// 2) 真实 Chrome（headless, CDP）加载 file:// 页面，采集控制台错误
// 3) 调用页内 window.GLIDE 复算耦合链，并做「任意帧重放确定性」差分
// 4) 冻结一帧截图，落盘 evidence/shot.png
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');
const ART = resolve(ROOT, 'art.html');
const PORT = 9333 + Math.floor(Math.random() * 400);
const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'
].find(p => existsSync(p));

const out = { static: {}, runtime: {}, replay: {}, console: [] };

/* ---------- 1) 静态核对 ---------- */
const src = readFileSync(ART, 'utf8');
out.static.bytes = Buffer.byteLength(src, 'utf8');
out.static.keyframes_defs = (src.match(/@keyframes\s+[\w-]+\s*\{/g) || []).map(s => s.trim());
out.static.keyframes_count = out.static.keyframes_defs.length;
out.static.animateTransform_count = (src.match(/<animateTransform/g) || []).length;
out.static.animate_count = (src.match(/<animate\s/g) || []).length;
out.static.parallax_layer_ids = (src.match(/id="lyr-[\w-]+"/g) || []);
out.static.layer_bases = [...src.matchAll(/id:\s*"(lyr-[\w-]+)",\s*dur:\s*([\d.]+),\s*base:\s*(\d+)/g)]
  .map(m => ({ id: m[1], dur_s: +m[2], base_px_s: +m[3] }));
const ext = src.split('\n').map((l, i) => [i + 1, l])
  .filter(([, l]) => /https?:\/\/|<link\b|<script[^>]+src=|<img[^>]+src=|@import|url\(\s*['"]?https?:/i.test(l))
  .filter(([, l]) => !/xmlns(:\w+)?=/.test(l) || /https?:\/\/(?!www\.w3\.org)/i.test(l));
out.static.external_refs = ext;
out.static.grades = { gte_8KB: out.static.bytes >= 8192, no_external: ext.length === 0 };

/* ---------- CDP 小客户端 ---------- */
function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url);
    ws.onopen = () => res(ws);
    ws.onerror = e => rej(new Error('ws error ' + (e.message || '')));
  });
}
function rpc(ws, method, params = {}) {
  const id = rpc.n = (rpc.n || 0) + 1;
  return new Promise((res, rej) => {
    const onMsg = ev => {
      const m = JSON.parse(ev.data);
      if (m.id === id) { ws.removeEventListener('message', onMsg); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }
      else {
        if (m.method === 'Runtime.exceptionThrown') out.console.push({ kind: 'exception', text: m.params.exceptionDetails?.exception?.description || m.params.exceptionDetails?.text });
        if (m.method === 'Runtime.consoleAPICalled' && ['error', 'warning'].includes(m.params.type)) out.console.push({ kind: 'console.' + m.params.type, text: (m.params.args || []).map(a => a.value ?? a.description).join(' ') });
        if (m.method === 'Log.entryAdded' && ['error', 'warning'].includes(m.params.entry.level)) out.console.push({ kind: 'log.' + m.params.entry.level, text: m.params.entry.text });
      }
    };
    ws.addEventListener('message', onMsg);
    ws.send(JSON.stringify({ id, method, params }));
  });
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

const url = 'file:///' + ART.replace(/\\/g, '/');
const profile = resolve(HERE, '_chrome-profile-' + process.pid);
mkdirSync(profile, { recursive: true });

const chrome = spawn(CHROME, [
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--hide-scrollbars', '--window-size=1200,700', '--force-device-scale-factor=1',
  '--remote-debugging-port=' + PORT, '--user-data-dir=' + profile, url
], { stdio: 'ignore' });

try {
  let page = null;
  for (let i = 0; i < 80; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      const list = await r.json();
      page = list.find(t => t.type === 'page' && /art\.html/.test(t.url || '') && t.webSocketDebuggerUrl)
          || list.find(t => t.type === 'page' && t.webSocketDebuggerUrl && !/^about:/.test(t.url || ''));
      if (page && /art\.html/.test(page.url || '')) break;
    } catch { /* 端口未起 */ }
    await sleep(250);
  }
  if (!page) throw new Error('未找到 art.html 页面目标');
  const ws = await connect(page.webSocketDebuggerUrl);
  await rpc(ws, 'Runtime.enable');
  await rpc(ws, 'Log.enable');
  await rpc(ws, 'Page.enable');
  // 等页面与脚本就绪
  for (let i = 0; i < 40; i++) {
    try {
      const r = await rpc(ws, 'Runtime.evaluate', { expression: 'document.readyState + "|" + (typeof window.GLIDE)', returnByValue: true });
      if (/complete\|object/.test(r.result.value || '')) break;
    } catch { /* ignore */ }
    await sleep(250);
  }
  await sleep(900); // 让 SMIL / rAF 跑一会儿，暴露潜在异常

  const ev = async (expr) => {
    const r = await rpc(ws, 'Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(expr + ' -> ' + JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails.text));
    return r.result.value;
  };

  out.runtime.svg_ok = await ev('document.getElementById("stage") && document.getElementById("stage").tagName');
  out.runtime.glide_exposed = await ev('typeof window.GLIDE');
  out.runtime.console_errors_seen_so_far = out.console.length;

  out.runtime.verify_t3 = await ev('window.GLIDE.verify(3.0)');
  out.runtime.verify_t20 = await ev('window.GLIDE.verify(20.0)');
  out.runtime.state_t_1_5 = await ev('(function(){var s=window.GLIDE.stateAt(1.5);var o={alt:s.alt,pitch:s.pitch,vfac:s.vfac,layers:[]};for(var i=0;i<s.layers.length;i++){var L=s.layers[i];o.layers.push({id:L.id,dur:L.dur,speed:Number(L.speed.toFixed(4)),dx:Number(L.dx.toFixed(3))});}return o;})()');
  out.runtime.speeds_distinct = await ev('(function(){var a=window.GLIDE.stateAt(1.0).layers,v=[];for(var i=0;i<a.length;i++){v.push(Number(a[i].speed.toFixed(4)));}return {speeds:v,distinct:new Set(v).size};})()');
  out.runtime.appendage_vs_vehicle = await ev('(function(){var d=window.GLIDE.params;return {vehicle_T:d.T,leg_ratio:d.LEG_RATIO,vehicle_period_differs_from_leg:!(d.T===1.2)};})()');

  /* ---------- 任意帧重放确定性：同一帧两次冻结必须完全一致 ---------- */
  const readState = async (t) => ev(`(function(){window.GLIDE.freeze(${t});var ids=["lyr-far","lyr-mid","lyr-near","lyr-fore"],L=[];for(var i=0;i<ids.length;i++){L.push(document.getElementById(ids[i]).getAttribute("transform"));}return {g:document.getElementById("glider").getAttribute("transform"),L:L};})()`);
  const a1 = await readState(2.4);
  const a2 = await readState(2.4);
  const b1 = await readState(4.9);
  out.replay = {
    frame_2_4_run1: a1, frame_2_4_run2: a2, frame_4_9: b1,
    reproducible: JSON.stringify(a1) === JSON.stringify(a2),
    frame_differs: JSON.stringify(a1) !== JSON.stringify(b1)
  };

  /* ---------- 截图（冻结在若干帧） ---------- */
  out.runtime.screenshots = [];
  for (const t of [0.0, 1.5, 3.0, 4.5]) {
    await ev(`window.GLIDE.freeze(${t})`);
    await sleep(120);
    const shot = await rpc(ws, 'Page.captureScreenshot', { format: 'png' });
    const name = 'shot-t' + t.toFixed(1).replace('.', '_') + '.png';
    writeFileSync(resolve(HERE, name), Buffer.from(shot.data, 'base64'));
    out.runtime.screenshots.push(name);
  }

  await ev('window.GLIDE.resume()');
  await sleep(400);
  out.console_final = out.console;
  ws.close();
} catch (e) {
  out.error = String(e && e.stack || e);
} finally {
  chrome.kill();
  await sleep(300);
}

writeFileSync(resolve(HERE, 'verify-result.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2));
