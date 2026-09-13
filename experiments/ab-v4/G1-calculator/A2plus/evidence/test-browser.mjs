// G1-A2plus 多路径交叉验证
// 路径 1（本文件）：Chrome headless + CDP 实操验证——真实 DOM 上跑全部向量（鼠标点击）、
// 可信键盘事件（Input.dispatchKeyEvent）验证键盘-鼠标一致性、.pressed 视觉反馈、
// 18 按钮可见性、全程控制台 0 报错、5 阶段截图留证。
// 方案来自 chrome-cdp-frontend-verify skill（本机 Chrome + Node 22 内置 WebSocket，零安装）。
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { execSync } from 'node:child_process';

const here = dirname(fileURLToPath(import.meta.url));
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = 20000 + (process.pid % 10000);
const PAGE_URL = 'file:///<实验根目录>/ab-v4/G1-calculator/A2plus/index.html';
const OUT = join(here, 'results');
const SHOTS = join(here, 'screenshots');
mkdirSync(OUT, { recursive: true });
mkdirSync(SHOTS, { recursive: true });

const vectors = JSON.parse(readFileSync(join(here, 'vectors.json'), 'utf8'));
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---- Chrome 启动 ----
const profile = join(tmpdir(), 'g1-a2plus-cdp-' + process.pid);
const chrome = spawn(CHROME, [
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--remote-debugging-port=' + PORT, '--user-data-dir=' + profile, 'about:blank',
], { stdio: 'ignore' });

let ws = null;
let msgId = 0;
const pending = new Map();
const consoleErrors = [];
const consoleWarnings = [];
const pageExceptions = [];
let loadFired = false;

function send(method, params = {}) {
  const id = ++msgId;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
}

function waitForEvent(method, timeoutMs = 8000) {
  return new Promise((resolve, reject) => {
    const t0 = Date.now();
    const timer = setInterval(() => {
      if (loadFired && method === 'Page.loadEventFired') { clearInterval(timer); resolve(); }
      if (Date.now() - t0 > timeoutMs) { clearInterval(timer); reject(new Error('等待事件超时: ' + method)); }
    }, 50);
  });
}

async function waitTargets() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch('http://127.0.0.1:' + PORT + '/json');
      if (r.ok) {
        const t = await r.json();
        if (Array.isArray(t) && t.length) return t;
      }
    } catch { /* 尚未就绪 */ }
    await sleep(250);
  }
  throw new Error('CDP 端口 ' + PORT + ' 未就绪');
}

async function evaluate(expression) {
  const r = await send('Runtime.evaluate', { expression, returnByValue: true });
  if (r.exceptionDetails) {
    throw new Error('页面 eval 异常: ' + ((r.exceptionDetails.exception && r.exceptionDetails.exception.description) || r.exceptionDetails.text));
  }
  return r.result.value;
}

function onMessage(raw) {
  const msg = JSON.parse(raw);
  if (msg.id && pending.has(msg.id)) {
    const p = pending.get(msg.id);
    pending.delete(msg.id);
    if (msg.error) p.reject(new Error(methodStr(msg) + ' -> ' + JSON.stringify(msg.error)));
    else p.resolve(msg.result || {});
    return;
  }
  if (msg.method === 'Page.loadEventFired') loadFired = true;
  if (msg.method === 'Runtime.consoleAPICalled') {
    if (msg.params.type === 'error') consoleErrors.push(msg.params.args.map(a => a.value !== undefined ? String(a.value) : (a.description || a.type)).join(' '));
    if (msg.params.type === 'warning') consoleWarnings.push(msg.params.args.map(a => a.value !== undefined ? String(a.value) : (a.description || a.type)).join(' '));
  }
  if (msg.method === 'Runtime.exceptionThrown') {
    pageExceptions.push((msg.params.exceptionDetails.exception && msg.params.exceptionDetails.exception.description) || msg.params.exceptionDetails.text);
  }
}

function methodStr(msg) { return 'CDP 调用失败'; }

const KEYDEF = {
  '0': { key: '0', code: 'Digit0', vk: 48, text: '0' }, '1': { key: '1', code: 'Digit1', vk: 49, text: '1' },
  '2': { key: '2', code: 'Digit2', vk: 50, text: '2' }, '3': { key: '3', code: 'Digit3', vk: 51, text: '3' },
  '4': { key: '4', code: 'Digit4', vk: 52, text: '4' }, '5': { key: '5', code: 'Digit5', vk: 53, text: '5' },
  '6': { key: '6', code: 'Digit6', vk: 54, text: '6' }, '7': { key: '7', code: 'Digit7', vk: 55, text: '7' },
  '8': { key: '8', code: 'Digit8', vk: 56, text: '8' }, '9': { key: '9', code: 'Digit9', vk: 57, text: '9' },
  '.': { key: '.', code: 'Period', vk: 190, text: '.' },
  '+': { key: '+', code: 'Equal', vk: 187, text: '+', shift: true },
  '-': { key: '-', code: 'Minus', vk: 189, text: '-' },
  '*': { key: '*', code: 'Digit8', vk: 56, text: '*', shift: true },
  '/': { key: '/', code: 'Slash', vk: 191, text: '/' },
  '=': { key: '=', code: 'Equal', vk: 187, text: '=' },
  'C': { key: 'Escape', code: 'Escape', vk: 27 },
  'back': { key: 'Backspace', code: 'Backspace', vk: 8 },
  'Enter': { key: 'Enter', code: 'Enter', vk: 13 },
  'x': { key: 'x', code: 'KeyX', vk: 88, text: 'x' },
  'Delete': { key: 'Delete', code: 'Delete', vk: 46 },
};

async function trustedKeyDown(d) {
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: d.key, code: d.code, windowsVirtualKeyCode: d.vk, nativeVirtualKeyCode: d.vk, text: d.text, unmodifiedText: d.text, modifiers: d.shift ? 8 : 0 });
}
async function trustedKeyUp(d) {
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: d.key, code: d.code, windowsVirtualKeyCode: d.vk, nativeVirtualKeyCode: d.vk });
}

async function runByClicks(keys) {
  for (const k of keys) {
    const found = await evaluate('(function(k){var b=document.querySelector(".keys button[data-key=\\"" + k + "\\"]");if(!b)return false;b.click();return true;})(' + JSON.stringify(k) + ')');
    if (!found) throw new Error('按钮不存在: ' + k);
  }
}

async function runByKeys(keys, equalsViaEnter = false) {
  for (const k of keys) {
    if (equalsViaEnter && k === '=') {
      await trustedKeyDown(KEYDEF.Enter); await trustedKeyUp(KEYDEF.Enter);
      continue;
    }
    const d = KEYDEF[k];
    if (!d) throw new Error('键盘映射缺失: ' + k);
    await trustedKeyDown(d);
    await trustedKeyUp(d);
  }
}

async function readState() {
  return evaluate('(function(){return { main: document.getElementById("current").textContent, top: document.getElementById("expression").textContent, errs: window.__errs ? window.__errs.length : -1 };})()');
}

async function clearAll() { await runByClicks(['C']); }

async function screenshot(name) {
  const r = await send('Page.captureScreenshot', { format: 'png' });
  const p = join(SHOTS, name);
  writeFileSync(p, Buffer.from(r.data, 'base64'));
  return p;
}

let verdict = true;
const fail = msg => { verdict = false; console.log('  FAIL: ' + msg); };
const ok = msg => console.log('  ok: ' + msg);

async function main() {
  const targets = await waitTargets();
  const page = targets.find(t => t.type === 'page');
  if (!page) throw new Error('未找到 page target');

  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  ws.onmessage = e => onMessage(e.data);

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Page.addScriptToEvaluateOnNewDocument', {
    source: 'window.__errs = []; window.addEventListener("error", function(e){ window.__errs.push(String(e.message)); }); window.addEventListener("unhandledrejection", function(e){ window.__errs.push("rejection: " + String(e.reason)); });',
  });

  const loadWait = waitForEvent('Page.loadEventFired');
  await send('Page.navigate', { url: PAGE_URL });
  await loadWait;
  await sleep(200);

  // ---- A. 初始状态 ----
  let st = await readState();
  if (st.main !== '0' || st.top !== '') fail('初始状态 main=' + JSON.stringify(st.main) + ' top=' + JSON.stringify(st.top));
  else ok('初始状态 main=0 top=(空)');
  const shotInitial = await screenshot('1-initial.png');

  // ---- B. 按钮清单与可见性（18 个） ----
  const btnInfo = await evaluate('(function(){var bs=document.querySelectorAll(".keys button");var out={count:bs.length,invisible:[]};for(var i=0;i<bs.length;i++){var r=bs[i].getBoundingClientRect();if(!(r.width>0&&r.height>0&&bs[i].offsetParent!==null))out.invisible.push(bs[i].dataset.key);}return out;})()');
  if (btnInfo.count !== 18) fail('按钮数量 ' + btnInfo.count + ' ≠ 18');
  else ok('按钮数量 18');
  if (btnInfo.invisible.length) fail('不可见按钮: ' + btnInfo.invisible.join(','));
  else ok('全部按钮可见（width/height>0 且 offsetParent 非空）');

  // ---- C. 鼠标点击路径：全部 26 向量 ----
  console.log('== 鼠标点击向量 ==');
  const clickResults = [];
  let shotExpression = null, shotResult = null, shotError = null;
  for (const v of vectors) {
    await clearAll();
    await runByClicks(v.keys);
    const s = await readState();
    const pass = s.main === v.expected_main && s.top === v.expected_top;
    clickResults.push({ id: v.id, via: 'clicks', expected_main: v.expected_main, expected_top: v.expected_top, got_main: s.main, got_top: s.top, pass });
    if (!pass) fail(v.id + ' main: 期望 ' + JSON.stringify(v.expected_main) + ' 实得 ' + JSON.stringify(s.main) + ' | top: 期望 ' + JSON.stringify(v.expected_top) + ' 实得 ' + JSON.stringify(s.top));
    if (v.id === 'chain') {
      // chain 在 "=" 之前补拍表达式态截图：重放前半段
      await clearAll();
      await runByClicks(['1', '2', '+', '3', '.', '5', '*', '2']);
      shotExpression = await screenshot('2-expression.png');
      await runByClicks(['=']);
      shotResult = await screenshot('3-result.png');
      const s2 = await readState();
      if (s2.main !== '19') fail('chain 截图重放后 main=' + s2.main);
    }
    if (v.id === 'div_zero') shotError = await screenshot('4-error.png');
  }
  const clickPass = clickResults.filter(r => r.pass).length;
  console.log('点击路径: ' + clickPass + '/' + clickResults.length + ' 通过');

  // ---- D. 键盘路径（可信输入事件）与键盘-鼠标一致性 ----
  console.log('== 键盘路径（Input.dispatchKeyEvent） ==');
  const keyResults = [];
  for (const vid of ['chain', 'precedence', 'float_add']) {
    const v = vectors.find(x => x.id === vid);
    await clearAll();
    await runByKeys(v.keys, vid === 'precedence'); // precedence 用 Enter 触发等号，其余用 = 键
    const s = await readState();
    const pass = s.main === v.expected_main && s.top === v.expected_top;
    keyResults.push({ id: vid + (vid === 'precedence' ? '(Enter)' : '(=)'), expected_main: v.expected_main, got_main: s.main, got_top: s.top, pass });
    if (!pass) fail('键盘 ' + vid + ' main: 期望 ' + JSON.stringify(v.expected_main) + ' 实得 ' + JSON.stringify(s.main));
  }
  // 键盘-鼠标一致性：同序列逐字符一致
  const chainV = vectors.find(x => x.id === 'chain');
  const clicksFinal = clickResults.find(r => r.id === 'chain');
  const keysFinal = keyResults.find(r => r.id === 'chain(=)');
  const consistent = clicksFinal.got_main === keysFinal.got_main && clicksFinal.got_top === keysFinal.got_top && keysFinal.got_main === chainV.expected_main;
  if (!consistent) fail('键盘与鼠标行为不一致: clicks=' + clicksFinal.got_main + ' keys=' + keysFinal.got_main);
  else ok('键盘与鼠标行为一致（chain 序列逐字符相同: ' + clicksFinal.got_main + '）');

  // ---- E. 按键视觉反馈（.pressed 类） ----
  await clearAll();
  await trustedKeyDown(KEYDEF['5']);
  const pressedOn = await evaluate('document.querySelector(".keys button[data-key=\\"5\\"]").classList.contains("pressed")');
  await trustedKeyUp(KEYDEF['5']);
  await sleep(300);
  const pressedOff = await evaluate('document.querySelector(".keys button[data-key=\\"5\\"]").classList.contains("pressed")');
  if (!pressedOn) fail('键盘按下未出现 .pressed 视觉反馈');
  if (pressedOff) fail('松键 300ms 后 .pressed 未移除');
  if (pressedOn && !pressedOff) ok('键盘按下 .pressed 出现并按时移除（视觉反馈生效）');
  const shotFlash = await screenshot('5-keyboard.png'); // 截图时 5 刚被按下（显示 5）

  // ---- F. 补充键盘映射：x 乘号、Delete 清除、c 清除 ----
  await clearAll();
  await runByKeys(['5', 'x', '2', 'Enter']);
  st = await readState();
  if (st.main !== '10') fail('x 乘号 + Enter 求值: 期望 10 实得 ' + st.main);
  else ok('x→*、Enter→= 映射正确（5x2=10）');
  await trustedKeyDown(KEYDEF.Delete); await trustedKeyUp(KEYDEF.Delete);
  st = await readState();
  if (st.main !== '0' || st.top !== '') fail('Delete 未清除: ' + JSON.stringify(st));
  else ok('Delete 清除生效');

  // ---- G. 控制台干净度 ----
  const errsPage = await evaluate('window.__errs.slice()');
  const totalErrors = consoleErrors.length + pageExceptions.length + errsPage.length;
  console.log('== 控制台 ==');
  console.log('console.error: ' + consoleErrors.length + ' | 页面异常事件: ' + pageExceptions.length + ' | window.onerror 收集: ' + errsPage.length + ' | warning: ' + consoleWarnings.length);
  if (consoleErrors.length) console.log(consoleErrors);
  if (pageExceptions.length) console.log(pageExceptions);
  if (errsPage.length) console.log(errsPage);
  if (totalErrors !== 0) fail('存在 ' + totalErrors + ' 条控制台错误/异常');
  else ok('全程 0 控制台错误/异常');

  // ---- 汇总 ----
  const allVectorPass = clickPass === clickResults.length && keyResults.every(r => r.pass);
  verdict = verdict && allVectorPass && totalErrors === 0;
  console.log('\n总判定: ' + (verdict ? 'PASS' : 'FAIL'));

  writeFileSync(join(OUT, 'browser-results.json'), JSON.stringify({
    url: PAGE_URL,
    buttons: btnInfo,
    click_results: clickResults,
    keyboard_results: keyResults,
    keyboard_click_consistent: consistent,
    pressed_feedback: { on: pressedOn, offAfter300ms: !pressedOff },
    console: { errors: totalErrors, warnings: consoleWarnings.length, consoleErrors, pageExceptions, windowOnerror: errsPage },
    screenshots: { initial: shotInitial, expression: shotExpression, result: shotResult, error: shotError, keyboard: shotFlash },
    verdict: verdict ? 'PASS' : 'FAIL',
    generated: new Date().toISOString(),
  }, null, 1));

  return verdict;
}

main()
  .then(v => { cleanup(v ? 0 : 1); })
  .catch(e => { console.error('FATAL:', e); cleanup(2); });

function cleanup(code) {
  try { if (ws) ws.close(); } catch { /* ignore */ }
  try { chrome.kill(); } catch { /* ignore */ }
  try { execSync('taskkill /PID ' + chrome.pid + ' /T /F', { stdio: 'ignore' }); } catch { /* 进程可能已退出 */ }
  setTimeout(() => {
    for (let i = 0; i < 3; i++) {
      try { if (existsSync(profile)) rmSync(profile, { recursive: true, force: true }); break; } catch { /* 锁未释放，重试 */ }
      sleepSync(300);
    }
    process.exit(code);
  }, 400);
}

function sleepSync(ms) {
  const end = Date.now() + ms;
  while (Date.now() < end) { /* 忙等 300ms */ }
}
