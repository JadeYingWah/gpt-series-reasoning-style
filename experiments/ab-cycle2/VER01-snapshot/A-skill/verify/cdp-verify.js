/**
 * 真实浏览器验证：用 Chrome headless + 原生 CDP（无第三方依赖）打开 tool.html，
 * 用 Input.dispatchMouseEvent 发真实鼠标点击（非 synthetic JS click），
 * 每步读取真实 DOM 表格顺序并截图留证。
 */
const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = 9300 + (Date.now() % 400); // 每次运行换端口，避免连到上一次残留实例
const ROOT = path.resolve(__dirname, '..');
const TOOL = path.join(ROOT, 'tool.html');
const SHOTS = path.join(__dirname, 'shots');
const RUN_ID = String(process.env.RUN_ID || Date.now());
// Chrome 临时 profile 放到系统临时目录，避免污染交付目录
const USER_DIR = path.join(require('os').tmpdir(), 'ver01-chrome-' + RUN_ID);
const LOG = [];
const results = { steps: [], verdict: 'UNKNOWN' };

function log(s) { LOG.push(s); }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function httpJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => { try { resolve(JSON.parse(d)); } catch (e) { reject(e); } });
    }).on('error', reject);
  });
}

class Cdp {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.events = []; }
  static async connect(url) {
    const ws = new WebSocket(url);
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
    const c = new Cdp(ws);
    ws.onmessage = ev => {
      const msg = JSON.parse(ev.data);
      if (msg.id && c.pending.has(msg.id)) {
        const { resolve, reject } = c.pending.get(msg.id);
        c.pending.delete(msg.id);
        msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
      } else if (msg.method) { c.events.push(msg.method); }
    };
    return c;
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async evaluate(expr) {
    const r = await this.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error('JS 异常: ' + JSON.stringify(r.exceptionDetails.exception));
    return r.result.value;
  }
  async click(x, y) {
    for (const type of ['mousePressed', 'mouseReleased']) {
      await this.send('Input.dispatchMouseEvent', {
        type, x, y, button: 'left', clickCount: 1, buttons: type === 'mousePressed' ? 1 : 0
      });
      await sleep(30);
    }
  }
  async shot(file) {
    const r = await this.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(file, Buffer.from(r.data, 'base64'));
  }
}

// 读取表格当前状态（真实 DOM）
const SNAPSHOT_JS = `(() => {
  const heads = [...document.querySelectorAll('#head-row th')].map(th => ({
    label: (th.querySelector('button')?.textContent || '').replace(/[▲▼↕]/g,'').trim(),
    key: th.getAttribute('data-key'),
    active: th.getAttribute('data-active'),
    ariaSort: th.getAttribute('aria-sort'),
    arrow: (th.querySelector('.arrow')?.textContent) || ''
  }));
  const rows = [...document.querySelectorAll('#body tr')].map(tr =>
    [...tr.children].map(td => td.textContent)
  );
  return { heads, rows, status: document.getElementById('status').textContent.trim() };
})()`;

// 目标列按钮中心坐标
const CENTER_JS = (key) => `(() => {
  const th = document.querySelector('#head-row th[data-key="${key}"]');
  const r = th.querySelector('button').getBoundingClientRect();
  return { x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2) };
})()`;

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  fs.mkdirSync(USER_DIR, { recursive: true });

  const chrome = spawn(CHROME, [
    '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--remote-debugging-port=' + PORT, '--user-data-dir=' + USER_DIR,
    '--window-size=1280,900', '--allow-file-access-from-files',
    'file:///' + TOOL.replace(/\\/g, '/')
  ], { stdio: 'ignore' });

  try {
    // 等待 CDP 端点就绪
    let targets = null;
    for (let i = 0; i < 60; i++) {
      try {
        const list = await httpJson(`http://127.0.0.1:${PORT}/json/list`);
        const wanted = 'file:///' + TOOL.replace(/\\/g, '/');
        const page = list.find(t => t.type === 'page' && t.webSocketDebuggerUrl && t.url === wanted)
                  || list.find(t => t.type === 'page' && t.webSocketDebuggerUrl);
        if (page) { targets = page; break; }
      } catch (e) {}
      await sleep(250);
    }
    if (!targets) throw new Error('未能在 15s 内连上 Chrome CDP 端点');
    log('CDP 端点已连接: ' + targets.url);

    const cdp = await Cdp.connect(targets.webSocketDebuggerUrl);
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    try {
      const v = await cdp.send('Browser.getVersion');
      results.browser = { product: v.product, protocolVersion: v.protocolVersion, jsVersion: v.jsVersion };
      log('浏览器: ' + v.product);
    } catch (e) { log('浏览器版本读取失败: ' + e.message); }

    // 等待真实渲染完成：脚本已执行且表头按钮已挂载
    let ready = false;
    for (let i = 0; i < 60; i++) {
      try {
        const ok = await cdp.evaluate(
          "document.readyState === 'complete' && !!document.querySelector('#head-row button.sort') && document.querySelectorAll('#body tr').length > 0"
        );
        if (ok) { ready = true; break; }
      } catch (e) {}
      await sleep(200);
    }
    if (!ready) throw new Error('页面在 12s 内未完成表格渲染');

    const s0 = await cdp.evaluate(SNAPSHOT_JS);
    await cdp.shot(path.join(SHOTS, '01-initial.png'));
    results.steps.push({ step: '初始加载', state: s0 });

    // 断言 1：数据条数
    results.recordCount = s0.rows.length;

    // 点击「价格（元）」→ 升序
    const p1 = await cdp.evaluate(CENTER_JS('price'));
    await cdp.click(p1.x, p1.y);
    await sleep(120);
    const s1 = await cdp.evaluate(SNAPSHOT_JS);
    await cdp.shot(path.join(SHOTS, '02-price-asc.png'));
    results.steps.push({ step: '点击「价格（元）」', clickAt: p1, state: s1 });

    // 再次点击 → 降序
    const p2 = await cdp.evaluate(CENTER_JS('price'));
    await cdp.click(p2.x, p2.y);
    await sleep(120);
    const s2 = await cdp.evaluate(SNAPSHOT_JS);
    await cdp.shot(path.join(SHOTS, '03-price-desc.png'));
    results.steps.push({ step: '再次点击「价格（元）」', clickAt: p2, state: s2 });

    // 点击「名称」→ 中文文本列升序
    const p3 = await cdp.evaluate(CENTER_JS('name'));
    await cdp.click(p3.x, p3.y);
    await sleep(120);
    const s3 = await cdp.evaluate(SNAPSHOT_JS);
    await cdp.shot(path.join(SHOTS, '04-name-asc.png'));
    results.steps.push({ step: '点击「名称」', clickAt: p3, state: s3 });

    // 点击「更新日期」→ 日期列
    const p4 = await cdp.evaluate(CENTER_JS('updated'));
    await cdp.click(p4.x, p4.y);
    await sleep(120);
    const s4 = await cdp.evaluate(SNAPSHOT_JS);
    await cdp.shot(path.join(SHOTS, '05-date-asc.png'));
    results.steps.push({ step: '点击「更新日期」', clickAt: p4, state: s4 });

    // ---- 判定 ----
    const checks = [];
    checks.push(['JSON 记录数 = 5', s0.rows.length === 5]);
    const priceCol = 3;
    const priceAsc = s1.rows.map(r => Number(r[priceCol].replace(/,/g, '')));
    const priceDesc = s2.rows.map(r => Number(r[priceCol].replace(/,/g, '')));
    checks.push(['价格升序数值递增', priceAsc.every((v, i) => i === 0 || priceAsc[i - 1] <= v)]);
    checks.push(['价格降序数值递减', priceDesc.every((v, i) => i === 0 || priceDesc[i - 1] >= v)]);
    checks.push(['降序 = 升序逆序', JSON.stringify(priceDesc) === JSON.stringify(priceAsc.slice().reverse())]);
    checks.push(['价格列 aria-sort 正确', s1.heads[priceCol].ariaSort === 'ascending' && s2.heads[priceCol].ariaSort === 'descending']);
    checks.push(['切换列后旧列取消高亮', s3.heads[priceCol].active === 'false' && s3.heads[1].active === 'true']);
    const names = s3.rows.map(r => r[1]);
    const collator = new Intl.Collator('zh-Hans-CN');
    const namesOracle = s0.rows.map(r => r[1]).sort(collator.compare);
    checks.push(['中文名称列升序与中国区排序规则（ICU zh-Hans-CN）一致',
      names.join('|') === namesOracle.join('|')]);
    results.nameOrder = { page: names, oracle: namesOracle };
    // 排序后行集合必须与原集合完全相同（不丢行、不重复）
    const sig = rows => rows.map(r => r[0] + '@' + r[1]).sort().join('|');
    checks.push(['各步排序均为原集合的排列（无丢行/重复）',
      [s1, s2, s3, s4].every(s => sig(s.rows) === sig(s0.rows))]);
    const dates = s4.rows.map(r => r[5]);
    checks.push(['日期列升序', dates.join('|') === ['2025-11-25', '2026-01-08', '2026-03-11', '2026-05-19', '2026-07-02'].join('|')]);
    checks.push(['表头显示排序指示箭头', s1.heads[priceCol].arrow === '▲' && s2.heads[priceCol].arrow === '▼']);
    checks.push(['状态栏随排序更新', /价格（元）/.test(s1.status) && /降序/.test(s2.status)]);

    results.checks = checks.map(([name, pass]) => ({ name, pass }));
    results.verdict = checks.every(c => c[1]) ? 'PASS' : 'FAIL';
    results.failed = checks.filter(c => !c[1]).map(c => c[0]);
  } catch (err) {
    results.verdict = 'ERROR';
    results.error = String(err && err.stack || err);
  } finally {
    try { chrome.kill(); } catch (e) {}
    results.log = LOG;
    fs.writeFileSync(path.join(__dirname, 'cdp-result.json'), JSON.stringify(results, null, 2));

    // 同步生成人读摘要，避免二次脚本出错导致摘要与结果不一致
    const lines = [];
    lines.push('verdict=' + results.verdict);
    lines.push('browser=' + (results.browser ? results.browser.product + ' (CDP ' + results.browser.protocolVersion + ')' : '未读到'));
    lines.push('recordCount=' + results.recordCount);
    for (const c of (results.checks || [])) lines.push((c.pass ? 'PASS' : 'FAIL') + '  ' + c.name);
    if (results.error) lines.push('error=' + results.error);
    fs.writeFileSync(path.join(__dirname, 'summary.txt'), lines.join('\n') + '\n');
  }
})();
