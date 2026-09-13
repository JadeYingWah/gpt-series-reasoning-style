// 裁判 2/2：真实 Chrome 无头渲染 + CDP 驱动点击交互，读真实 DOM 核对数值
// 用法：node verify-e2e.js [待测文件，默认 app.html]
// 退出码：0=全过；1=断言失败（含页面内异常）；2=裁判自身故障（Chrome 未起来），该次结果作废
// 副作用：在目录内生成 _shot.png（全量态截图）与 _shot_empty.png（空态截图）作为证据
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const APP = path.resolve(process.argv[2] || 'app.html');
const PROFILE = path.join(os.tmpdir(), 'q01-chrome-' + Date.now() + '-' + Math.floor(Math.random() * 1e6));
const PORT = 9300 + Math.floor(Math.random() * 400);

const sleep = ms => new Promise(r => setTimeout(r, ms));
let pass = 0, fail = 0; const fails = [];
const eq = (n, g, w) => { if (JSON.stringify(g) === JSON.stringify(w)) pass++; else { fail++; fails.push(n + '\n    got =' + JSON.stringify(g) + '\n    want=' + JSON.stringify(w)); } };
const ok = (n, c, x) => { if (c) pass++; else { fail++; fails.push(n + (x ? ' | ' + x : '')); } };

(async () => {
  const chrome = spawn(CHROME, [
    '--headless=new', '--remote-debugging-port=' + PORT, '--user-data-dir=' + PROFILE,
    '--no-first-run', '--no-default-browser-check', '--disable-extensions',
    '--disable-gpu', '--hide-scrollbars', '--window-size=1200,900',
    '--allow-file-access-from-files',
    'file:///' + APP.replace(/\\/g, '/')
  ], { stdio: 'ignore' });

  // 等待调试端口
  let target = null;
  const WANT = path.basename(APP);
  for (let i = 0; i < 60 && !target; i++) {
    await sleep(300);
    try {
      const list = await (await fetch('http://127.0.0.1:' + PORT + '/json/list')).json();
      target = list.find(t => t.type === 'page' && decodeURIComponent(t.url).indexOf(WANT) >= 0);
    } catch (e) { }
  }
  if (!target) { console.log('INFRA: 无法连接 Chrome 调试端口（非被测页面的问题）'); chrome.kill(); process.exit(2); }

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0; const pending = new Map(); const events = [];
  ws.onmessage = ev => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) { const p = pending.get(msg.id); pending.delete(msg.id); p(msg); }
    else if (msg.method) events.push(msg);
  };
  const send = (method, params) => new Promise(res => {
    const myId = ++id; pending.set(myId, res);
    ws.send(JSON.stringify({ id: myId, method, params: params || {} }));
  });
  const evaluate = async (expr) => {
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true, userGesture: true });
    if (r.result && r.result.exceptionDetails) {
      const err = new Error('页面内异常: ' + JSON.stringify(r.result.exceptionDetails.exception && r.result.exceptionDetails.exception.description));
      err.isPage = true; throw err;
    }
    return r.result.result.value;
  };

  await send('Runtime.enable');
  await send('Page.enable');
  // 在文档创建前捕获所有未捕获异常
  await send('Page.addScriptToEvaluateOnNewDocument', {
    source: 'window.__err=[];window.addEventListener("error",function(e){window.__err.push(String(e.message))});window.addEventListener("unhandledrejection",function(e){window.__err.push("unhandledrejection:"+String(e.reason))});'
  });
  const loaded = new Promise(res => { const t = setInterval(() => { const i = events.findIndex(e => e.method === 'Page.loadEventFired'); if (i >= 0) { clearInterval(t); res(); } }, 50); });
  await send('Page.reload', { ignoreCache: true });
  await loaded;
  await sleep(500);

  // 诊断
  console.log('[诊断] 目标文件=' + APP);
  console.log('[诊断] url=' + await evaluate('location.href'));
  console.log('[诊断] title=' + await evaluate('document.title'));
  console.log('[诊断] ids=' + await evaluate('[].slice.call(document.querySelectorAll("[id]")).map(function(e){return e.id}).join(",")'));
  console.log('[诊断] readyState=' + await evaluate('document.readyState'));
  console.log('[诊断] bodyLen=' + await evaluate('document.body ? document.body.innerHTML.length : -1'));
  // 自检：确认真的加载了指定文件（防止裁判与被测对象错配）
  ok('加载的确实是目标文件', decodeURIComponent(await evaluate('location.pathname')).replace(/^\//, '').toLowerCase().endsWith(path.basename(APP).toLowerCase()));

  // ---------- 1. 初始渲染（真实 DOM 读值） ----------
  const snapshot = () => evaluate(`(function(){
    var cards=[].slice.call(document.querySelectorAll('#cards .card')).map(function(c){
      return {k:c.querySelector('.k').textContent,v:c.querySelector('.v').textContent};
    });
    var bars=[].slice.call(document.querySelectorAll('#bars .col')).map(function(c){
      return {val:c.querySelector('.col-val').textContent,h:c.querySelector('.bar').style.height,title:c.title};
    });
    var chips=[].slice.call(document.querySelectorAll('#chips .chip')).map(function(b){
      return {t:b.textContent,p:b.getAttribute('aria-pressed')};
    });
    return {
      cards:cards, bars:bars, chips:chips,
      emptyVisible: document.getElementById('emptyState').textContent.trim().length>0 && document.getElementById('chartWrap').style.display==='none',
      emptyText: document.getElementById('emptyState').textContent.trim(),
      chartShown: document.getElementById('chartWrap').style.display!=='none',
      status: document.getElementById('status').textContent,
      yAxis: [].slice.call(document.querySelectorAll('#yAxis span')).map(function(s){return s.textContent}),
      xAxis: [].slice.call(document.querySelectorAll('#xAxis span')).map(function(s){return s.textContent}),
      errBox: document.getElementById('errBox').style.display,
      errText: document.getElementById('errBox').textContent
    };
  })()`);

  const s0 = await snapshot();
  eq('页面无错误框', s0.errBox, 'none');
  eq('错误框无内容', s0.errText, '');
  eq('三张数字卡', s0.cards.map(c => c.k), ['总销售额', '订单数', '客单价']);
  eq('初始 总销售额', s0.cards[0].v, '¥2,655,300.00');
  eq('初始 订单数', s0.cards[1].v, '28');
  eq('初始 客单价', s0.cards[2].v, '¥94,832.14');
  eq('五个地区按钮', s0.chips.map(c => c.t).length, 5);
  ok('初始全部地区为选中态', s0.chips.every(c => c.p === 'true'), JSON.stringify(s0.chips.map(c => c.p)));
  eq('初始 6 根柱', s0.bars.length, 6);
  eq('X 轴为 1-6 月', s0.xAxis, ['1月', '2月', '3月', '4月', '5月', '6月']);
  eq('初始图表可见（非空态）', s0.chartShown, true);
  eq('初始空态容器为空', s0.emptyVisible, false);
  console.log('【DOM 实测·初始】' + s0.cards.map(c => c.k + '=' + c.v).join('，'));
  console.log('  柱顶标签: ' + s0.bars.map(b => b.val).join(' | '));
  console.log('  柱高(%) : ' + s0.bars.map(b => b.h).join(' | '));
  console.log('  Y 轴: ' + s0.yAxis.join(' / '));
  console.log('  状态栏: ' + s0.status);

  // 柱高与数值一致性：每根柱高必须等于「金额 / 轴上限」，且金额更大的柱更高
  const amt = s0.bars.map(b => parseFloat(b.title.split('：')[1].replace(/[¥,]/g, '')));
  const hgt = s0.bars.map(b => parseFloat(b.h));
  const axisTop = parseFloat(s0.yAxis[0].replace('¥', '').replace('万', '')) * 10000;
  const expectedH = amt.map(a => +(a / axisTop * 100).toFixed(2));
  ok('每根柱高=金额/轴上限（真实 DOM）',
    hgt.every((h, i) => Math.abs(h - expectedH[i]) < 0.02),
    JSON.stringify({ amt, hgt, expectedH, axisTop }));
  ok('柱高均严格>0', hgt.every(h => h > 0), JSON.stringify(hgt));
  ok('最高柱高>50%（非退化）', Math.max(...hgt) > 50, 'max=' + Math.max(...hgt));
  const sorted = amt.map((a, i) => i).sort((a, b) => amt[a] - amt[b]);
  ok('金额更大则柱更高（严格）',
    sorted.every((idx, i) => i === 0 || (amt[idx] > amt[sorted[i - 1]] ? hgt[idx] > hgt[sorted[i - 1]] : hgt[idx] === hgt[sorted[i - 1]])),
    JSON.stringify({ amt, hgt }));
  ok('柱高均在 0~100%', hgt.every(h => h >= 0 && h <= 100), JSON.stringify(hgt));
  eq('柱 title 金额=独立复算', amt.map(Math.round), [490400, 403500, 422700, 438000, 421000, 479700]);

  // ---------- 2. 点击「清空」→ 空态 ----------
  await evaluate(`document.getElementById('btnNone').click()`);
  await sleep(120);
  const s1 = await snapshot();
  eq('清空后 总销售额归零', s1.cards[0].v, '¥0.00');
  eq('清空后 订单数归零', s1.cards[1].v, '0');
  eq('清空后 客单价归零(非NaN)', s1.cards[2].v, '¥0.00');
  eq('清空后 柱子为 0 根', s1.bars.length, 0);
  eq('清空后 显示空态(chartWrap 隐藏)', s1.chartShown, false);
  ok('清空后 空态文案含"没有符合条件的数据"', s1.emptyText.indexOf('没有符合条件的数据') >= 0, s1.emptyText);
  ok('清空后 空态给出操作指引', s1.emptyText.indexOf('至少选择一个地区') >= 0, s1.emptyText);
  eq('清空后 所有按钮为未选中态', s1.chips.map(c => c.p), ['false', 'false', 'false', 'false', 'false']);
  eq('清空后 状态栏显示（无）', s1.status.indexOf('（无）') >= 0, true);
  ok('清空后状态栏命中 0 条', s1.status.indexOf('0') >= 0, s1.status);
  console.log('【DOM 实测·空态】' + s1.emptyText.replace(/\s+/g, ' '));
  console.log('  数字卡: ' + s1.cards.map(c => c.k + '=' + c.v).join('，'));
  console.log('  状态栏: ' + s1.status);
  eq('空态下无错误框', s1.errBox, 'none');

  // ---------- 3. 单选「华东」→ 数字卡与图表同步 ----------
  await evaluate(`[].slice.call(document.querySelectorAll('#chips .chip')).filter(function(b){return b.textContent==='华东'})[0].click()`);
  await sleep(120);
  const s2 = await snapshot();
  eq('华东 总销售额', s2.cards[0].v, '¥1,025,100.00');
  eq('华东 订单数', s2.cards[1].v, '8');
  eq('华东 客单价', s2.cards[2].v, '¥128,137.50');
  eq('华东 柱数', s2.bars.length, 6);
  const amt2 = s2.bars.map(b => parseFloat(b.title.split('：')[1].replace(/[¥,]/g, '')));
  const hgt2 = s2.bars.map(b => parseFloat(b.h));
  const axisTop2 = parseFloat(s2.yAxis[0].replace('¥', '').replace('万', '')) * 10000;
  ok('华东 每根柱高=金额/轴上限',
    hgt2.every((h, i) => Math.abs(h - +(amt2[i] / axisTop2 * 100).toFixed(2)) < 0.02),
    JSON.stringify({ amt2, hgt2, axisTop2 }));
  ok('华东 轴上限随筛选后最大值重算(≤30万)', axisTop2 <= 300000, 'axisTop2=' + axisTop2);
  ok('华东 柱金额合计=数字卡总额', Math.abs(s2.bars.map(b => parseFloat(b.title.split('：')[1].replace(/[¥,]/g, ''))).reduce((a, b) => a + b, 0) - 1025100) < 0.001, JSON.stringify(s2.bars.map(b => b.title)));
  eq('华东 按钮选中态唯一', s2.chips.filter(c => c.p === 'true').map(c => c.t), ['华东']);
  eq('华东 空态隐藏', s2.chartShown, true);
  console.log('【DOM 实测·筛选华东】' + s2.cards.map(c => c.k + '=' + c.v).join('，') + '  柱=' + s2.bars.map(b => b.val).join(','));
  console.log('  柱 title: ' + s2.bars.map(b => b.title).join(' | '));

  // ---------- 4. 多选 华东+华南 ----------
  await evaluate(`[].slice.call(document.querySelectorAll('#chips .chip')).filter(function(b){return b.textContent==='华南'})[0].click()`);
  await sleep(120);
  const s3 = await snapshot();
  eq('多选 总销售额=两块之和', s3.cards[0].v, '¥1,689,200.00');
  eq('多选 订单数=8+6', s3.cards[1].v, '14');
  ok('多选柱金额合计=数字卡总额', Math.abs(s3.bars.map(b => parseFloat(b.title.split('：')[1].replace(/[¥,]/g, ''))).reduce((a, b) => a + b, 0) - 1689200) < 0.001);
  eq('多选 选中两个', s3.chips.filter(c => c.p === 'true').length, 2);
  console.log('【DOM 实测·多选华东+华南】' + s3.cards.map(c => c.k + '=' + c.v).join('，'));

  // ---------- 5. 取消勾选回到空态，再全选恢复 ----------
  await evaluate(`[].slice.call(document.querySelectorAll('#chips .chip')).filter(function(b){return b.getAttribute('aria-pressed')==='true'}).forEach(function(b){b.click()})`);
  await sleep(120);
  const s4 = await snapshot();
  eq('逐个取消→再次空态', s4.chartShown, false);
  eq('逐个取消→订单数 0', s4.cards[1].v, '0');
  await evaluate(`document.getElementById('btnAll').click()`);
  await sleep(120);
  const s5 = await snapshot();
  eq('全选→恢复 28 条', s5.cards[1].v, '28');
  eq('全选→恢复总额', s5.cards[0].v, '¥2,655,300.00');
  eq('全选→6 根柱', s5.bars.length, 6);
  console.log('【DOM 实测·恢复】订单数=' + s5.cards[1].v + '，总额=' + s5.cards[0].v);

  // ---------- 6. 超长文本：注入超长地区名，检查布局不被撑破 ----------
  const longTest = await evaluate(`(function(){
    var host=document.getElementById('chips');
    var b=document.createElement('button');
    b.className='chip'; b.type='button';
    b.textContent='超长地区名称'.repeat(200);
    host.appendChild(b);
    var panel=host.parentElement.parentElement;
    var res={chipW:b.getBoundingClientRect().width, chipH:b.getBoundingClientRect().height,
             panelScrollW:panel.scrollWidth, panelClientW:panel.clientWidth,
             docScrollW:document.documentElement.scrollWidth, docClientW:document.documentElement.clientWidth};
    host.removeChild(b);
    return res;
  })()`);
  ok('超长地区名不撑破筛选面板', longTest.panelScrollW <= longTest.panelClientW + 1, JSON.stringify(longTest));
  ok('超长地区名不产生横向滚动条', longTest.docScrollW <= longTest.docClientW + 1, JSON.stringify(longTest));
  ok('超长地区名被限制在 220px 内', longTest.chipW <= 222, 'chipW=' + longTest.chipW);
  console.log('【DOM 实测·超长文本】chip宽=' + Math.round(longTest.chipW) + 'px，面板无横向溢出');

  // ---------- 7. 注入非法记录：应被忽略并给出提示，而不是崩掉 ----------
  const sBad = await evaluate(`(function(){
    RAW_ORDERS.push(
      {id:'BAD1',region:'华东',month:'2026-99',amount:-1},
      {id:'BAD2',region:'',month:'2026-01',amount:5},
      {id:'BAD3',region:'华东',month:'2026-01',amount:NaN},
      null
    );
    document.getElementById('btnAll').click();
    return 1;
  })()`) && await snapshot();
  eq('注入 4 条非法记录后仍无错误框', sBad.errBox, 'none');
  eq('非法记录不计入订单数', sBad.cards[1].v, '28');
  eq('非法记录不计入总额', sBad.cards[0].v, '¥2,655,300.00');
  ok('状态栏提示已忽略非法记录', sBad.status.indexOf('已忽略 4 条非法记录') >= 0, sBad.status);
  ok('状态栏仍显示 28 条命中', sBad.status.indexOf('命中订单 28 条') >= 0, sBad.status);
  console.log('【DOM 实测·非法数据】' + sBad.status);
  await evaluate(`(function(){ RAW_ORDERS.splice(RAW_ORDERS.length-4,4); document.getElementById('btnAll').click(); return 1; })()`);
  await sleep(120);

  // ---------- 8. 无外部网络请求 / 无未捕获异常 ----------
  const res = await evaluate(`performance.getEntriesByType('resource').map(function(r){return r.name})`);
  const external = res.filter(u => u.indexOf('file://') !== 0);
  eq('无任何外部资源请求', external, []);
  ok('资源请求数为 0（全部内联）', res.length === 0 || res.every(u => u.indexOf('file://') >= 0), JSON.stringify(res));
  const errs = await evaluate('window.__err');
  eq('无未捕获异常', errs, []);
  const consoleErrs = events.filter(e => e.method === 'Runtime.exceptionThrown');
  eq('CDP 未捕获到异常事件', consoleErrs.length, 0);
  const sFinal = await snapshot();
  eq('交互后仍无错误提示框', sFinal.errBox, 'none');
  eq('交互后仍无错误文本', sFinal.errText, '');

  // ---------- 9. 截图存证 ----------
  const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
  fs.writeFileSync('_shot.png', Buffer.from(shot.result.data, 'base64'));
  await evaluate(`document.getElementById('btnNone').click()`);
  await sleep(200);
  const shot2 = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
  fs.writeFileSync('_shot_empty.png', Buffer.from(shot2.result.data, 'base64'));

  console.log('#'.repeat(64));
  console.log('E2E PASS=' + pass + '  FAIL=' + fail);
  if (fails.length) { console.log('--- FAILURES ---'); fails.forEach(f => console.log('  ' + f)); }

  ws.close(); chrome.kill();
  await sleep(300);
  process.exit(fail ? 1 : 0);
})().catch(e => {
  if (e && e.isPage) { console.log('FAIL(页面内异常): ' + e.message); process.exit(1); }
  console.log('INFRA: ' + e.message); process.exit(2);
});
