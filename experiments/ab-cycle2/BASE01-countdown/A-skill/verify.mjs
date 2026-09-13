// CDP 真机验证脚本（Node 22 原生 WebSocket，无第三方依赖）
// 用法: node verify.mjs
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PAGE_URL = process.env.PAGE_URL || 'file:///<实验根目录>/ab-cycle2/BASE01-countdown/A-skill/app.html';
const OUT_DIR = '<实验根目录>/ab-cycle2/BASE01-countdown/A-skill';
const SUFFIX = process.env.OUT_SUFFIX || '';
const WITH_SHOTS = process.env.SHOTS !== '0';
const PORT = Number(process.env.CDP_PORT || 9223);
const profile = mkdtempSync(join(tmpdir(), 'cdp-prof-'));

const results = [];
let profileCleanup = true;
const rec = (id, name, pass, detail) => { results.push({ id, name, pass, detail }); };
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const chrome = spawn(CHROME, [
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', '--mute-audio', '--autoplay-policy=no-user-gesture-required',
  '--window-size=520,840', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  'about:blank'
], { stdio: 'ignore' });

let ws, msgId = 0;
const pending = new Map();
const exceptions = [];

function send(method, params = {}, sessionId) {
  const id = ++msgId;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params, sessionId }));
  });
}

async function waitForChrome() {
  for (let i = 0; i < 100; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      const list = await r.json();
      const page = list.find(t => t.type === 'page');
      if (page && page.webSocketDebuggerUrl) return page.webSocketDebuggerUrl;
    } catch {}
    await sleep(150);
  }
  throw new Error('Chrome CDP 未就绪');
}

async function evalJs(expression) {
  const r = await send('Runtime.evaluate', {
    expression, returnByValue: true, awaitPromise: true
  });
  if (r.exceptionDetails) {
    throw new Error('页面内求值抛错: ' + JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails));
  }
  return r.result.value;
}

async function shot(name) {
  if (!WITH_SHOTS) return;
  const r = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(`${OUT_DIR}/${name}${SUFFIX}.png`, Buffer.from(r.data, 'base64'));
}

// 通过真实事件驱动 UI（非直接调函数）
const clickById = (id) => evalJs(`document.getElementById(${JSON.stringify(id)}).click(), 'clicked'`);
const setInput = (v) => evalJs(`(() => {
  const el = document.getElementById('minutes');
  el.value = ${JSON.stringify(v)};
  el.dispatchEvent(new Event('input', { bubbles: true }));
  return el.value.length;
})()`);
const snap = () => evalJs('window.__countdown.getState()');

try {
  const wsUrl = await waitForChrome();
  ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const { resolve, reject } = pending.get(m.id); pending.delete(m.id);
      m.error ? reject(new Error(JSON.stringify(m.error))) : resolve(m.result);
    } else if (m.method === 'Runtime.exceptionThrown') {
      exceptions.push(m.params.exceptionDetails?.exception?.description || JSON.stringify(m.params));
    }
  };

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Page.addScriptToEvaluateOnNewDocument', {
    source: 'window.__errCount=0;window.addEventListener("error",function(){window.__errCount++;});' +
            'window.addEventListener("unhandledrejection",function(){window.__errCount++;});'
  });
  await send('Page.navigate', { url: PAGE_URL });
  await sleep(900);

  // T0 页面加载 + 无外部依赖
  const t0 = await evalJs(`(() => {
    const res = performance.getEntriesByType('resource').map(r => r.name);
    return { readyState: document.readyState, resources: res,
             hasDisplay: !!document.getElementById('display'), title: document.title };
  })()`);
  rec('T0', '页面加载成功且无外部资源请求',
    t0.readyState === 'complete' && t0.hasDisplay && t0.resources.length === 0,
    `readyState=${t0.readyState}, resources=[${t0.resources.join(',')}]`);

  // T1 初始状态
  const s1 = await snap();
  const btns1 = await evalJs(`({start: document.getElementById('startBtn').disabled, pause: document.getElementById('pauseBtn').disabled, reset: document.getElementById('resetBtn').disabled})`);
  rec('T1', '初始状态：待机 00:00，暂停按钮禁用',
    s1.state === 'idle' && s1.display === '00:00' && s1.statusText === '待机' && btns1.pause === true && btns1.start === false,
    JSON.stringify(s1) + ' buttons=' + JSON.stringify(btns1));

  // T2 空输入
  await setInput('');
  await clickById('startBtn');
  await sleep(150);
  const s2 = await snap();
  rec('T2', '非法输入-空：拦截并提示，未进入运行',
    s2.state === 'idle' && /请输入分钟数/.test(s2.msg) && s2.hasTicker === false,
    `state=${s2.state}, msg="${s2.msg}"`);

  // T3 "0"
  await setInput('0');
  await clickById('startBtn');
  await sleep(150);
  const s3 = await snap();
  rec('T3', '非法输入-0：拦截并提示',
    s3.state === 'idle' && /必须大于 0/.test(s3.msg),
    `state=${s3.state}, msg="${s3.msg}"`);

  // T4 字母
  await setInput('abc');
  await clickById('startBtn');
  await sleep(150);
  const s4 = await snap();
  rec('T4', '非法输入-字母：拦截并提示',
    s4.state === 'idle' && /只能输入数字/.test(s4.msg),
    `state=${s4.state}, msg="${s4.msg}"`);

  // T5 超长文本（2000 字符）
  const longStr = '9'.repeat(2000);
  const len = await setInput(longStr);
  await clickById('startBtn');
  await sleep(200);
  const s5 = await snap();
  rec('T5', '边界-超长文本(2000字符)：拦截且不崩',
    s5.state === 'idle' && /输入过长/.test(s5.msg) && len === 2000,
    `inputLen=${len}, state=${s5.state}, msg="${s5.msg}"`);

  // T6 负号 / 小数非法 / 超上限
  await setInput('-5'); await clickById('startBtn'); await sleep(120);
  const s6a = (await snap()).msg;
  await setInput('1441'); await clickById('startBtn'); await sleep(120);
  const s6b = (await snap()).msg;
  await setInput('1e3'); await clickById('startBtn'); await sleep(120);
  const s6c = (await snap()).msg;
  rec('T6', '非法输入-负号/超上限/科学计数法：三种均拦截',
    /只能输入数字/.test(s6a) && /不能超过 1440/.test(s6b) && /只能输入数字/.test(s6c),
    `-5→"${s6a}" | 1441→"${s6b}" | 1e3→"${s6c}"`);

  // T7 合法启动
  await setInput('5');
  await clickById('startBtn');
  await sleep(1300);
  const s7 = await snap();
  const btns7 = await evalJs(`({start: document.getElementById('startBtn').disabled, pause: document.getElementById('pauseBtn').disabled})`);
  rec('T7', '合法输入 5 分钟：进入运行，倒计时开始递减',
    s7.state === 'running' && s7.statusText === '运行中' && s7.remainingMs > 294000 && s7.remainingMs < 300000
      && s7.hasTicker === true && btns7.start === true && btns7.pause === false,
    `state=${s7.state}, remainingMs=${s7.remainingMs}, display=${s7.display}, buttons=${JSON.stringify(btns7)}`);

  // T8 每秒刷新
  const d1 = (await snap()).display;
  await sleep(1100);
  const d2 = (await snap()).display;
  await sleep(1100);
  const d3 = (await snap()).display;
  const sec = (s) => { const p = s.split(':').map(Number); return p.length === 3 ? p[0] * 3600 + p[1] * 60 + p[2] : p[0] * 60 + p[1]; };
  rec('T8', '剩余时间每秒刷新（读数连续递减，约 1s 一档）',
    /^\d{2}:\d{2}$/.test(d1) && sec(d1) - sec(d2) === 1 && sec(d2) - sec(d3) === 1,
    `${d1} → ${d2} → ${d3}（每档递减 ${sec(d1) - sec(d2)}s / ${sec(d2) - sec(d3)}s）`);

  // T9 暂停并静止
  await clickById('pauseBtn');
  await sleep(150);
  const p1 = await snap();
  await sleep(1200);
  const p2 = await snap();
  rec('T9', '暂停：状态切换且剩余时间冻结',
    p1.state === 'paused' && p1.hasTicker === false && p2.remainingMs === p1.remainingMs
      && p2.statusText === '已暂停',
    `pause@${p1.remainingMs}ms → 1.2s 后 ${p2.remainingMs}ms`);

  // T10 继续
  await clickById('startBtn');
  await sleep(1200);
  const r10 = await snap();
  rec('T10', '继续：从暂停点恢复递减',
    r10.state === 'running' && r10.remainingMs < p1.remainingMs,
    `恢复前 ${p1.remainingMs}ms → 恢复 1.2s 后 ${r10.remainingMs}ms`);

  // T11 重置
  await clickById('resetBtn');
  await sleep(200);
  const s11 = await snap();
  rec('T11', '重置：回到待机 00:00',
    s11.state === 'idle' && s11.display === '00:00' && s11.remainingMs === 0 && s11.hasTicker === false,
    JSON.stringify(s11));

  // T12 归零提示（0.05 分钟 = 3 秒）
  await setInput('0.05');
  await clickById('startBtn');
  await sleep(1000);
  const mid = await snap();
  await shot('shot-running');
  await sleep(2600);
  const s12 = await snap();
  const banner = await evalJs(`({shown: document.getElementById('banner').classList.contains('show'), alertRole: document.getElementById('banner').getAttribute('role')})`);
  rec('T12', '归零：出现明显提示（横幅+状态+红色），且计时器停止',
    mid.state === 'running' && s12.state === 'finished' && s12.display === '00:00'
      && s12.statusText === '时间到' && banner.shown === true && banner.alertRole === 'alert'
      && s12.hasTicker === false,
    `运行中=${mid.state}/${mid.display} → 归零后 state=${s12.state}, display=${s12.display}, status=${s12.statusText}, banner=${banner.shown}`);
  await shot('shot-finished');

  // T13 刷新后回到初始
  await send('Page.reload');
  await sleep(900);
  const s13 = await snap();
  rec('T13', '刷新页面后状态回到初始（无持久化）',
    s13.state === 'idle' && s13.display === '00:00' && s13.statusText === '待机',
    JSON.stringify(s13));

  // T14 键盘 Enter 启动 + 归零后再次开始
  await setInput('9');
  await evalJs(`(() => {
    const el = document.getElementById('minutes');
    el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
  })()`);
  await sleep(300);
  const s14 = await snap();
  rec('T14', '回车键可启动（键盘可达性）',
    s14.state === 'running', `state=${s14.state}, display=${s14.display}`);
  await clickById('resetBtn');
  await sleep(150);

  // T16 视口矩阵：三种宽度下无横向溢出、关键元素完整可见
  const viewports = [[390, 780, 'mobile'], [520, 840, 'desktop'], [900, 760, 'wide']];
  const vpDetail = [];
  let vpOk = true;
  await setInput('5');
  await clickById('startBtn');
  await sleep(1100);
  for (const [w, h, name] of viewports) {
    await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: false });
    await sleep(300);
    const m = await evalJs(`(() => {
      const d = document.documentElement;
      const app = document.querySelector('.app').getBoundingClientRect();
      const vis = ['minutes','startBtn','pauseBtn','resetBtn','display'].every(id => {
        const r = document.getElementById(id).getBoundingClientRect();
        return r.width > 0 && r.height > 0 && r.top >= -1 && r.left >= -1;
      });
      return { overflow: d.scrollWidth - d.clientWidth, innerW: window.innerWidth,
               appW: Math.round(app.width), allVisible: vis };
    })()`);
    const ok = m.overflow <= 0 && m.allVisible;
    vpOk = vpOk && ok;
    vpDetail.push(`${name} ${w}×${h}: 横向溢出=${m.overflow}px, 面板宽=${m.appW}px, 元素可见=${m.allVisible}`);
    if (name === 'mobile') await shot('shot-mobile');
    if (name === 'wide') await shot('shot-wide');
  }
  await send('Emulation.clearDeviceMetricsOverride');
  await clickById('resetBtn');
  await sleep(150);
  rec('T16', '视口矩阵（390/520/900px）：无横向溢出且元素完整可见',
    vpOk, vpDetail.join(' || '));

  // T15 无未捕获异常
  const pageErrors = await evalJs('window.__errCount === undefined ? 0 : window.__errCount');
  rec('T15', '全程无未捕获异常（Runtime.exceptionThrown 监听）',
    exceptions.length === 0,
    `捕获异常数=${exceptions.length}${exceptions.length ? ' :: ' + exceptions.slice(0, 3).join(' | ') : ''}, pageErrors=${pageErrors}`);

} catch (e) {
  rec('ERR', '脚本级异常', false, String(e && e.stack ? e.stack : e));
} finally {
  try { ws && ws.close(); } catch {}
  chrome.kill();
  await sleep(800);
  if (profileCleanup) { try { rmSync(profile, { recursive: true, force: true }); } catch {} }
}

const passed = results.filter(r => r.pass).length;
const lines = [];
lines.push(`# 自动化验证结果（Chrome 真机 / CDP / ${new Date().toISOString()}）`);
lines.push('');
lines.push(`结论：${passed}/${results.length} 项通过`);
lines.push('');
lines.push('| 编号 | 用例 | 结果 | 实测细节 |');
lines.push('| --- | --- | --- | --- |');
for (const r of results) {
  lines.push(`| ${r.id} | ${r.name} | ${r.pass ? 'PASS' : 'FAIL'} | ${String(r.detail).replace(/\|/g, '\\|').replace(/\n/g, ' ')} |`);
}
writeFileSync(`${OUT_DIR}/verify-report${SUFFIX}.md`, lines.join('\n'), 'utf8');
writeFileSync(`${OUT_DIR}/verify-raw${SUFFIX}.json`, JSON.stringify(results, null, 2), 'utf8');
console.log(lines.join('\n'));
process.exit(passed === results.length ? 0 : 1);
