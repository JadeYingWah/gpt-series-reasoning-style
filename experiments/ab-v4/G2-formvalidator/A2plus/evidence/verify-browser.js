'use strict';
/*
 * G2/A2+ 路径1：浏览器实操验证（自包含 CDP 驱动，headless Chromium）
 * 以真实输入事件（Input.insertText / 鼠标按下-抬起点击）驱动交付页 index.html，
 * 逐项断言 DOM 状态（错误/成功文案、class、aria-invalid、提交门控、焦点管理），
 * 采集 console 错误与页面异常，输出关键状态截图。全部证据落 evidence/。
 * 用法：node verify-browser.js
 */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const http = require('http');

const CHROME = 'C:/Users/<用户名>/AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe';
const PAGE = 'file:///' + path.resolve(__dirname, '..', 'index.html').replace(/\\/g, '/');
const SHOTS = path.join(__dirname, 'shots');
const PORT = 9333;

let exitCode = 0;
process.on('uncaughtException', (e) => console.log('[UNCAUGHT] ' + (e && e.stack || e)));
process.on('unhandledRejection', (e) => console.log('[UNREJECTED] ' + (e && (e.stack || e.message) || e)));
function report(ok, tag, detail) {
  if (!ok) exitCode = 1;
  console.log((ok ? '[PASS] ' : '[FAIL] ') + tag + (detail ? ' — ' + detail : ''));
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
function getJSON(p) {
  return new Promise((res, rej) => {
    http.get({ host: '127.0.0.1', port: PORT, path: p }, (r) => {
      let d = ''; r.on('data', (c) => (d += c)); r.on('end', () => { try { res(JSON.parse(d)); } catch (e) { rej(e); } });
    }).on('error', rej);
  });
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'g2-cdp-profile-'));
  const chrome = spawn(CHROME, [
    '--remote-debugging-port=' + PORT, '--user-data-dir=' + profile,
    '--no-first-run', '--disable-extensions', '--window-size=520,780',
    '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', 'about:blank'
  ], { stdio: 'ignore' });

  const targets = await (async () => { for (let i = 0; i < 30; i++) { try { const t = await getJSON('/json/list'); if (t.length) return t; } catch (e) {} await sleep(500); } throw new Error('CDP 端口未就绪'); })();
  const page = targets.find((t) => t.type === 'page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

  let msgId = 0; const pending = new Map(); const events = [];
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { const p = pending.get(m.id); pending.delete(m.id); m.error ? p.rej(new Error(m.error.message)) : p.res(m.result); }
    else if (m.method) events.push(m);
  };
  const send = (method, params) => new Promise((res, rej) => { const id = ++msgId; pending.set(id, { res, rej }); ws.send(JSON.stringify({ id, method, params: params || {} })); });
  async function evaljs(expr) {
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error('eval 失败: ' + JSON.stringify(r.exceptionDetails.exception || {}).slice(0, 200));
    return r.result.value;
  }
  async function fill(sel, text) {
    await evaljs("var e=document.querySelector('" + sel + "'); e.value=''; e.focus(); 'ok'");
    await send('Input.insertText', { text: text });
  }
  async function blurActive() { return evaljs("document.activeElement.blur(); 'ok'"); }
  async function clickCenter(sel) {
    const b = await evaljs("(function(){var r=document.querySelector('" + sel + "').getBoundingClientRect();return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2})})()");
    const c = JSON.parse(b);
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: c.x, y: c.y, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: c.x, y: c.y, button: 'left', clickCount: 1 });
  }
  async function shot(file) {
    const r = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(path.join(SHOTS, file), Buffer.from(r.data, 'base64'));
  }
  const stateExpr = "JSON.stringify({" +
    "email:{msg:document.getElementById('emailMsg').textContent,cls:document.getElementById('email').className,ai:document.getElementById('email').getAttribute('aria-invalid')}," +
    "phone:{msg:document.getElementById('phoneMsg').textContent,cls:document.getElementById('phone').className,ai:document.getElementById('phone').getAttribute('aria-invalid')}," +
    "password:{msg:document.getElementById('passwordMsg').textContent,cls:document.getElementById('password').className,ai:document.getElementById('password').getAttribute('aria-invalid')}," +
    "submitted:document.getElementById('formSuccess').classList.contains('show')," +
    "focus:document.activeElement.id})";

  await send('Page.enable'); await send('Runtime.enable'); await send('Log.enable');
  const navDone = send('Page.navigate', { url: PAGE });
  await sleep(1200); await navDone;
  await sleep(500);

  const S = JSON.parse(await evaljs(stateExpr));
  const A = async (sel, text) => { await fill(sel, text); await blurActive(); await sleep(60); return JSON.parse(await evaljs(stateExpr)); };
  const emailBad = '邮箱格式不正确，应形如 name@example.com（不含空格，@ 后需有域名）';

  console.log('== 邮箱字段（失焦即时校验） ==');
  await evaljs("document.getElementById('email').focus(); 'ok'"); await blurActive(); await sleep(60);
  let st = JSON.parse(await evaljs(stateExpr));
  report(st.email.msg === '邮箱不能为空' && st.email.cls.includes('error') && st.email.ai === 'true', 'E1 空值失焦→错误态', st.email.msg);
  st = await A('#email', 'plainaddress');
  report(st.email.cls.includes('error') && st.email.msg === emailBad, 'E2 无@格式错', st.email.msg);
  st = await A('#email', 'a b@example.com');
  report(st.email.cls.includes('error') && st.email.msg === emailBad, 'E3 含空格特殊字符', st.email.msg);
  st = await A('#email', 'a@@b.com');
  report(st.email.cls.includes('error') && st.email.msg === emailBad, 'E4 双@特殊字符', st.email.msg);
  st = await A('#email', 'a'.repeat(250) + '@x.com');
  report(st.email.cls.includes('error') && st.email.msg.indexOf('超过 254') >= 0, 'E5 超长256字符', st.email.msg);
  st = await A('#email', 'user+tag@example.com');
  report(st.email.cls.includes('success') && st.email.ai === 'false', 'E6 合法(+号)→成功态', st.email.msg);

  console.log('== 手机号字段 ==');
  await evaljs("document.getElementById('phone').focus(); 'ok'"); await blurActive(); await sleep(60);
  st = JSON.parse(await evaljs(stateExpr));
  report(st.phone.msg === '手机号不能为空' && st.phone.cls.includes('error'), 'P1 空值失焦→错误态', st.phone.msg);
  st = await A('#phone', '138 0013 8000');
  report(st.phone.cls.includes('error') && st.phone.msg.indexOf('只能包含数字') >= 0, 'P2 含空格特殊字符', st.phone.msg);
  st = await A('#phone', '138001380001');
  report(st.phone.cls.includes('error') && st.phone.msg.indexOf('超过 11 位') >= 0, 'P3 12位超长', st.phone.msg);
  st = await A('#phone', '10800138000');
  report(st.phone.cls.includes('error') && st.phone.msg.indexOf('3-9') >= 0, 'P4 第2位为0格式错', st.phone.msg);
  st = await A('#phone', '13800138000');
  report(st.phone.cls.includes('success'), 'P5 合法→成功态', st.phone.msg);

  console.log('== 密码字段 ==');
  await evaljs("document.getElementById('password').focus(); 'ok'"); await blurActive(); await sleep(60);
  st = JSON.parse(await evaljs(stateExpr));
  report(st.password.msg === '密码不能为空' && st.password.cls.includes('error'), 'W1 空值失焦→错误态', st.password.msg);
  st = await A('#password', 'abcdefgh');
  report(st.password.cls.includes('error') && st.password.msg.indexOf('缺少数字') >= 0, 'W2 缺数字', st.password.msg);
  st = await A('#password', '12345678');
  report(st.password.cls.includes('error') && st.password.msg.indexOf('缺少字母') >= 0, 'W3 缺字母', st.password.msg);
  st = await A('#password', 'abc');
  report(st.password.cls.includes('error') && st.password.msg.indexOf('至少 8 位') >= 0, 'W4 3位太短', st.password.msg);
  st = await A('#password', 'a1' + 'x'.repeat(63));
  report(st.password.cls.includes('error') && st.password.msg.indexOf('超过 64') >= 0, 'W5 65字符超长', st.password.msg);
  st = await A('#password', 'abc12345!@#');
  report(st.password.cls.includes('success'), 'W6 含特殊字符合法→成功态', st.password.msg);

  console.log('== 提交门控 ==');
  await fill('#email', 'bad@format'); await sleep(60);
  await clickCenter('button[type=submit]'); await sleep(120);
  st = JSON.parse(await evaljs(stateExpr));
  report(st.submitted === false, 'S1 有错提交被阻止（无成功反馈）', 'submitted=' + st.submitted);
  report(st.email.cls.includes('error') && st.phone.cls.includes('success') && st.password.cls.includes('success'), 'S1 错误/成功态并存且各自正确', st.email.msg);
  report(st.focus === 'email', 'S1 焦点自动定位到首个错误字段', 'focus=' + st.focus);
  await shot('01-submit-blocked.png');
  await A('#email', 'user+tag@example.com');
  await clickCenter('button[type=submit]'); await sleep(120);
  st = JSON.parse(await evaljs(stateExpr));
  report(st.submitted === true, 'S2 全部合法→提交成功反馈可见', 'submitted=' + st.submitted);
  await shot('02-submit-success.png');

  console.log('== 控制台与页面异常 ==');
  await sleep(300);
  const consoleErrors = events.filter((e) => e.method === 'Runtime.consoleAPICalled' && ['error', 'warning'].includes(e.params.type));
  const pageErrors = events.filter((e) => e.method === 'Runtime.exceptionThrown');
  const logErrors = events.filter((e) => e.method === 'Log.entryAdded' && ['error', 'warning'].includes(e.params.entry.level));
  report(consoleErrors.length === 0, 'console error/warning = ' + consoleErrors.length);
  report(pageErrors.length === 0, '未捕获页面异常 = ' + pageErrors.length);
  report(logErrors.length === 0, '浏览器日志 error/warning = ' + logErrors.length);
  if (consoleErrors.length || pageErrors.length || logErrors.length) {
    console.log('错误明细: ' + JSON.stringify([...consoleErrors, ...pageErrors, ...logErrors]).slice(0, 800));
  }

  try { ws.close(); } catch (e) {}
  chrome.kill();
  await sleep(300);
  fs.rmSync(profile, { recursive: true, force: true });
  console.log('== 结论 ==');
  console.log(exitCode === 0 ? 'ALL GREEN：浏览器实操验证全部通过，无控制台报错' : '存在 FAIL 项，见上方标记');
  process.exitCode = exitCode;
})().catch((e) => { console.log('[FATAL] ' + (e && e.message || e)); process.exitCode = 2; });
