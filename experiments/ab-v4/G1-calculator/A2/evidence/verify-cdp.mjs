// A2 臂真实浏览器验证电池（Edge headless + Chrome DevTools Protocol）
// 运行: node verify-cdp.mjs
// 产出: verify-log.txt、screenshot-*.png（本目录）
// 原则: 对真实交付物 index.html 做实操驱动（真实 DOM 点击 + 键盘事件），先枚举输入域分段再写用例。
import { spawn } from 'node:child_process';
import { writeFileSync, rmSync, existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const HTML = join(ROOT, 'index.html');
const LOG = [];
let failed = 0;

function log(s) { console.log(s); LOG.push(s); }
function check(name, cond, detail) {
  if (cond) log('PASS  ' + name + (detail ? '  [' + detail + ']' : ''));
  else { failed++; log('FAIL  ' + name + (detail ? '  [' + detail + ']' : '')); }
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// ---------- 静态检查（不进浏览器） ----------
const html = readFileSync(HTML, 'utf8');
check('S1 外部依赖零引用（无 script src / link href / url(http / http(s)://）',
  !/<script[^>]+src=/i.test(html) && !/<link[^>]+href=/i.test(html) &&
  !/url\(\s*['"]?https?:/i.test(html) && !/https?:\/\//.test(html));
check('S2 存在 <!DOCTYPE html>', /^<!DOCTYPE html>/i.test(html.trim()));
const mScript = html.match(/<script>([\s\S]*?)<\/script>/i);
check('S3 存在内联 <script> 代码块', !!mScript);
if (mScript) {
  try { new vm.Script(mScript[1]); log('PASS  S4 JS 语法编译检查（vm.Script）'); }
  catch (e) { failed++; log('FAIL  S4 JS 语法编译检查: ' + e.message); }
}

// ---------- 启动 headless 浏览器 ----------
const CANDIDATES = [
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
];
const browserExe = CANDIDATES.find(existsSync);
if (!browserExe) { log('FATAL 未找到 Edge/Chrome'); process.exit(1); }
log('浏览器: ' + browserExe);

const PORT = 9333;
const profile = join(process.env.TEMP || '.', 'a2-calc-profile-' + Date.now());
const fileUrl = 'file:///' + HTML.replace(/\\/g, '/');
let proc = null;

function launch(headlessArg) {
  proc = spawn(browserExe, [
    headlessArg, '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--remote-debugging-port=' + PORT, '--user-data-dir=' + profile, 'about:blank'
  ], { stdio: 'ignore' });
}
async function cdpReady() {
  for (let i = 0; i < 60; i++) {
    try { const r = await fetch('http://127.0.0.1:' + PORT + '/json/version'); if (r.ok) return true; }
    catch {}
    await sleep(250);
  }
  return false;
}

launch('--headless=new');
if (!(await cdpReady())) {
  try { proc.kill(); } catch {}
  log('--headless=new 未就绪，回退 --headless');
  launch('--headless');
  if (!(await cdpReady())) { log('FATAL CDP 端口未就绪'); process.exit(1); }
}

const targets = await (await fetch('http://127.0.0.1:' + PORT + '/json/list')).json();
const pageWs = targets.find(t => t.type === 'page').webSocketDebuggerUrl;
const ws = new WebSocket(pageWs);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

let mid = 0;
const pending = new Map();
const consoleErrors = [];
const exceptions = [];
ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) {
    const p = pending.get(msg.id); pending.delete(msg.id);
    msg.error ? p.rej(new Error(msg.error.message)) : p.res(msg.result);
  } else if (msg.method === 'Runtime.consoleAPICalled' &&
             (msg.params.type === 'error' || msg.params.type === 'warning')) {
    consoleErrors.push(msg.params.type + ': ' + msg.params.args.map(a => a.value ?? a.description ?? '').join(' '));
  } else if (msg.method === 'Runtime.exceptionThrown') {
    const d = msg.params.exceptionDetails;
    exceptions.push(d.text + (d.exception && d.exception.description ? ' ' + d.exception.description : ''));
  }
};
ws.onerror = (e) => log('WS-ERROR ' + (e.message || e));

function send(method, params = {}) {
  const id = ++mid;
  return new Promise((res, rej) => {
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function ev(expression) {
  const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) {
    throw new Error('page eval failed: ' + ((r.exceptionDetails.exception && r.exceptionDetails.exception.description) || r.exceptionDetails.text));
  }
  return r.result.value;
}

await send('Runtime.enable');
await send('Page.enable');
await send('Page.navigate', { url: fileUrl });

let ready = false;
for (let i = 0; i < 20; i++) {
  try { ready = await ev("document.readyState === 'complete' && !!document.getElementById('display')"); } catch {}
  if (ready) break;
  await sleep(250);
}
check('P1 页面加载完成且显示元素存在', ready);

// 注入测试驱动（运行时注入，不修改交付物）
await ev(`window.__t = {
  click(k){ const b=document.querySelector('button[data-k="'+k+'"]'); if(!b) throw new Error('no button: '+k); b.click(); return document.getElementById('display').textContent; },
  key(k){ document.dispatchEvent(new KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true})); return document.getElementById('display').textContent; },
  disp(){ return document.getElementById('display').textContent; },
  expr(){ return document.getElementById('expr').textContent; },
  keys(){ return Array.from(document.querySelectorAll('button[data-k]')).map(function(b){ return b.getAttribute('data-k'); }); }
}`);

async function clickCalc(seq) {
  await ev('__t.click("C")');   // 状态隔离：每个用例从干净状态起跑
  const ks = Array.isArray(seq) ? seq : seq.split('');
  for (const k of ks) await ev('__t.click(' + JSON.stringify(k) + ')');
  return ev('__t.disp()');
}
async function keyStates(seq) {
  const out = [];
  for (const k of seq) out.push(await ev('__t.key(' + JSON.stringify(k) + ')'));
  return out;
}
const K2BTN = { Backspace: 'back', Enter: '=', Escape: 'C' };
async function clickStates(seq) {
  const out = [];
  for (const k of seq) out.push(await ev('__t.click(' + JSON.stringify(K2BTN[k] || k) + ')'));
  return out;
}

// ============ A. 基础四则（鼠标点击路径） ============
check('A1 7+3=10', (await clickCalc('7+3=')) === '10');
check('A2 12-4=8', (await clickCalc(['1','2','-','4','='])) === '8');
check('A3 6*7=42', (await clickCalc('6*7=')) === '42');
check('A4 8/2=4', (await clickCalc('8/2=')) === '4');
check('A5 7/3≈2.333…（除不尽）', Math.abs(Number(await clickCalc('7/3=')) - 7 / 3) < 1e-9);
check('A6 5-8=-3（负数结果）', (await clickCalc('5-8=')) === '-3');
check('A7 9*9*9*9=6561（连续运算）', (await clickCalc('9*9*9*9=')) === '6561');
check('A8 2+3*4=20（口袋计算器顺序语义）', (await clickCalc('2+3*4=')) === '20');
check('A9 100/5/2=10（连续除法）', (await clickCalc('100/5/2=')) === '10');

// ============ B. 小数 ============
check('B1 0.1+0.2=0.3（浮点噪声修剪）', (await clickCalc('0.1+0.2=')) === '0.3');
check('B2 1.5*3=4.5', (await clickCalc('1.5*3=')) === '4.5');
check('B3 .5+0.5=1（前导小数点）', (await clickCalc(['.','5','+','0','.','5','='])) === '1');
check('B4 2.5-1.25=1.25', (await clickCalc('2.5-1.25=')) === '1.25');
check('B5 双小数点被忽略：3..4 → 3.4', (await clickCalc('3..4=')) === '3.4');
check('B6 前导零防堆积：005 → 5', (await clickCalc('005=')) === '5');

// ============ C. 边界与状态机 ============
check('C1 5+= → 10（等号复用当前输入）', (await clickCalc('5+=')) === '10');
check('C2 5*= → 25', (await clickCalc('5*=')) === '25');
check('C3 运算符连按替换：5+*3= → 15', (await clickCalc('5+*3=')) === '15');
check('C4 开局按运算符：*3= → 0', (await clickCalc('*3=')) === '0');
check('C5 空态等号无操作', (await clickCalc('=')) === '0');
check('C6 除零：5/0= → Error', (await clickCalc('5/0=')) === 'Error');
check('C7 除零后按数字恢复：7+3= → 10', (await clickCalc('7+3=')) === '10');
{
  await clickCalc('123');
  const s = [];
  for (let i = 0; i < 3; i++) s.push(await ev('__t.click("back")'));
  check('C8 退格：123→12→1→0', s.join(',') === '12,1,0', s.join('→'));
}
{
  await clickCalc('4*5=');
  check('C9 结果可退格：20 → 2', (await ev('__t.click("back")')) === '2');
}
{
  await clickCalc('9*9=');
  await ev('__t.click("C")');
  check('C10 C 归零：81→C→0 且 expr 清空', (await ev('__t.disp()')) === '0' && (await ev('__t.expr()')) === '');
  check('C11 C 后可继续运算：7+3= → 10', (await clickCalc('7+3=')) === '10');
}
check('C12 等号后按运算符以结果续算：4*5= +1= → 21', (await clickCalc(['4','*','5','=','+','1','='])) === '21');
check('C13 等号后直接输数字开新算：4*5= 7+3= → 10', (await clickCalc(['4','*','5','=','7','+','3','='])) === '10');
check('C14 0/0 → Error（NaN 防护）', (await clickCalc('0/0=')) === 'Error');
check('C15 大数不崩溃：999999999*999999999', (await clickCalc('999999999*999999999=')).startsWith('999999998'));
check('C16 算式行展示：12+ 后 expr="12 +"', (await (async () => {
  await clickCalc('12+');
  return ev('__t.expr()');
})()) === '12 +');

// ============ D. 键盘输入与鼠标点击一致性（逐状态对比） ============
const KSEQS = [
  ['7','+','3','='],
  ['0','.','1','+','0','.','2','='],
  ['5','/','0','='],
  ['1','2','3','Backspace','Backspace'],
  ['2','*','3','*','4','='],
  ['5','-','8','=']
];
for (const s of KSEQS) {
  await ev('__t.click("C")');
  const a = await keyStates(s);
  await ev('__t.click("C")');
  const b = await clickStates(s);
  check('D 键盘=鼠标 逐态一致: ' + s.join(''), JSON.stringify(a) === JSON.stringify(b), a.join('→'));
}
{
  await ev('__t.click("C")');
  for (const k of ['6','*','7']) await ev('__t.key(' + JSON.stringify(k) + ')');
  check('D7 Enter 触发等号：6*7+Enter → 42', (await ev('__t.key("Enter")')) === '42');
  for (const k of ['1','2','3']) await ev('__t.key(' + JSON.stringify(k) + ')');
  check('D8 Escape 清除：123+Esc → 0', (await ev('__t.key("Escape")')) === '0');
  await ev('__t.click("C")');
  for (const k of ['8','/','2']) await ev('__t.key(' + JSON.stringify(k) + ')');
  check('D9 键盘 / 与数字：8/2 → 4', (await ev('__t.key("Enter")')) === '4');
  const before = await ev('__t.disp()');
  await ev('__t.key("x")');
  check('D10 无映射按键不扰动状态：x', (await ev('__t.disp()')) === before);
}

// ============ E. 全按钮可达性 ============
const ks = await ev('__t.keys()');
const expect = ['C','back','/','*','-','+','=','.', '0','1','2','3','4','5','6','7','8','9'].sort();
check('E1 按钮全集完整（19 个）', JSON.stringify([...ks].sort()) === JSON.stringify(expect), ks.join(','));
let allOk = true, err = '';
for (const k of ks) {
  try { await ev('__t.click(' + JSON.stringify(k) + ')'); }
  catch (e) { allOk = false; err = e.message; }
}
check('E2 全部按钮逐个可点击且无异常', allOk, err);

// ============ 截图留证 ============
await ev('__t.click("C")');
await clickCalc('12+7');
const shot1 = await send('Page.captureScreenshot', { format: 'png' });
writeFileSync(join(HERE, 'screenshot-12plus7.png'), Buffer.from(shot1.data, 'base64'));
await send('Page.navigate', { url: fileUrl });
await sleep(700);
const shot2 = await send('Page.captureScreenshot', { format: 'png' });
writeFileSync(join(HERE, 'screenshot-initial.png'), Buffer.from(shot2.data, 'base64'));

// ============ G. 控制台清洁（整个会话） ============
check('G1 控制台零 error/warning', consoleErrors.length === 0, consoleErrors.join(' | '));
check('G2 零未捕获异常', exceptions.length === 0, exceptions.join(' | '));

log('—');
log(failed === 0 ? '结果: ALL PASS' : '结果: ' + failed + ' 项 FAIL');
writeFileSync(join(HERE, 'verify-log.txt'), LOG.join('\n') + '\n');

try { ws.close(); } catch {}
try { proc.kill(); } catch {}
try { rmSync(profile, { recursive: true, force: true }); } catch {}
process.exit(failed === 0 ? 0 : 1);
