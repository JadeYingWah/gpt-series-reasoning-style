/* 真实浏览器端到端交互验证（零依赖，用 node 内置 WebSocket 直连 CDP）
   运行：node verify-browser.js
   做的是：起 headless Chrome -> 打开 tool.html -> 真实 click() 表头 -> 读回 tbody 行序 */
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PAGE_URL = "file:///" + path.join(__dirname, "tool.html").replace(/\\/g, "/");
const PORT = 9333;

let pass = 0; const fails = [];
const ok = (n, c, e) => { c ? (pass++, console.log("PASS  " + n)) : (fails.push(n), console.log("FAIL  " + n + (e ? "  <- " + e : ""))); };
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "cdp-"));
  const chrome = spawn(CHROME, [
    "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
    "--remote-debugging-port=" + PORT, "--user-data-dir=" + profile,
    "--window-size=1280,900", PAGE_URL
  ], { stdio: "ignore" });

  const cleanup = () => {
    try { chrome.kill(); } catch (_) {}
    try { fs.rmSync(profile, { recursive: true, force: true }); } catch (_) {}
  };
  process.on("exit", cleanup);

  // 找到 page target
  let target = null;
  for (let i = 0; i < 60 && !target; i++) {
    await sleep(250);
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      target = list.find(t => t.type === "page" && t.webSocketDebuggerUrl);
    } catch (_) {}
  }
  if (!target) { console.log("FAIL  无法连接 CDP"); cleanup(); process.exit(1); }

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0; const pending = new Map();
  const exceptions = [];   // 真实收集页面未捕获异常
  ws.onmessage = ev => {
    const msg = JSON.parse(ev.data);
    if (msg.method === "Runtime.exceptionThrown") {
      const d = msg.params.exceptionDetails;
      exceptions.push(d.text + (d.exception && d.exception.description ? " | " + d.exception.description.split("\n")[0] : ""));
    }
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  };
  const send = (method, params) => new Promise(res => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params: params || {} })); });
  const evaluate = async expr => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails));
    return r.result.result.value;
  };

  await send("Runtime.enable");
  await send("Page.enable");

  // 等页面加载完成
  for (let i = 0; i < 40; i++) {
    const ready = await evaluate("document.readyState === 'complete' && document.querySelectorAll('#body tr').length > 0");
    if (ready) break;
    await sleep(150);
  }

  // 读表工具
  const colIndex = await evaluate("(() => { const b=[...document.querySelectorAll('#head-row button')]; return Object.fromEntries(b.map((x,i)=>[x.textContent.replace(/[▲▼]/g,'').trim(), i])); })()");
  const col = k => {
    const i = colIndex[k];
    return `[...document.querySelectorAll('#body tr')].map(tr => tr.children[${i}].textContent)`;
  };
  const click = k => `document.querySelectorAll('#head-row button')[${colIndex[k]}].click()`;

  ok("浏览器已渲染 6 列表头", Object.keys(colIndex).length === 6, JSON.stringify(Object.keys(colIndex)));
  ok("浏览器已渲染 5 行数据", (await evaluate("document.querySelectorAll('#body tr').length")) === 5);

  // 默认排序：编号 升序
  ok("默认按编号升序", JSON.stringify(await evaluate(col("编号"))) === JSON.stringify(["1", "2", "3", "4", "5"]),
     JSON.stringify(await evaluate(col("编号"))));

  // 真实点击「数量」表头 -> 数值升序（字典序会得到 120,15,3,42,8）
  await evaluate(click("数量")); await sleep(80);
  const qtyAsc = await evaluate(col("数量"));
  ok("点击「数量」后按数值升序", JSON.stringify(qtyAsc) === JSON.stringify(["3", "8", "15", "42", "120"]), JSON.stringify(qtyAsc));

  // 再次点击同列 -> 降序
  await evaluate(click("数量")); await sleep(80);
  const qtyDesc = await evaluate(col("数量"));
  ok("再点「数量」切降序", JSON.stringify(qtyDesc) === JSON.stringify(["120", "42", "15", "8", "3"]), JSON.stringify(qtyDesc));

  // 点击「单价」切换列并重置为升序；顺带核验千分位/小数格式
  await evaluate(click("单价(元)")); await sleep(80);
  const priceAsc = await evaluate(col("单价(元)"));
  ok("切换列后重置为升序", JSON.stringify(priceAsc) === JSON.stringify(["89.50", "259.90", "499", "1299", "1899"]), JSON.stringify(priceAsc));

  // 点击「入库日期」
  await evaluate(click("入库日期")); await sleep(80);
  const dateAsc = await evaluate(col("入库日期"));
  ok("按日期升序（跨年正确）", JSON.stringify(dateAsc) === JSON.stringify(["2025-11-30", "2026-01-07", "2026-03-14", "2026-05-22", "2026-07-02"]), JSON.stringify(dateAsc));

  // 点击「名称」（中文）：与 node 侧同一 collator 逐项比对，而不是弱断言
  await evaluate(click("名称")); await sleep(80);
  const nameAsc = await evaluate(col("名称"));
  const expectedNames = ["无线鼠标", "机械键盘", "27寸显示器", "USB-C 扩展坞", "降噪耳机"]
    .slice().sort(new Intl.Collator("zh-Hans-CN", { numeric: true, sensitivity: "base" }).compare);
  ok("按名称升序与 node 侧 collator 结果一致",
     JSON.stringify(nameAsc) === JSON.stringify(expectedNames),
     "浏览器=" + JSON.stringify(nameAsc) + " node=" + JSON.stringify(expectedNames));

  // 排序指示器 + aria 状态 + 状态栏文字随点击变化
  const arrowIdx = await evaluate("[...document.querySelectorAll('#head-row button')].findIndex(b => /[▲▼]/.test(b.textContent))");
  ok("排序箭头出现在当前排序列（名称列 index=1）", arrowIdx === colIndex["名称"], "arrowIdx=" + arrowIdx);
  const aria = await evaluate("[...document.querySelectorAll('#head-row th')].map(th => th.getAttribute('aria-sort')).join(',')");
  ok("aria-sort 只有一个非 none", aria.split(",").filter(v => v !== "none").length === 1, aria);
  const statusTxt = await evaluate("document.getElementById('status').textContent");
  ok("状态栏反映当前排序列", statusTxt.includes("名称") && statusTxt.includes("升序") && statusTxt.includes("5"), statusTxt);

  // 真实异常检查：Runtime.enable 期间页面抛出的未捕获异常
  ok("整轮点击期间无未捕获异常", exceptions.length === 0, JSON.stringify(exceptions));

  // 鉴别力探针：证明上面的检查不是空转（故意抛一个异常，必须被捕获到）
  await evaluate("setTimeout(function () { throw new Error('discrimination-probe'); }, 0)");
  await sleep(300);
  ok("该异常检查确有鉴别力（探针异常被抓到）",
     exceptions.length === 1 && exceptions[0].includes("discrimination-probe"), JSON.stringify(exceptions));

  ws.close();
  cleanup();
  console.log("\n" + pass + " passed, " + fails.length + " failed");
  if (fails.length) fails.forEach(f => console.log("  - " + f));
  process.exit(fails.length ? 1 : 0);
})().catch(e => { console.log("ERROR " + e.message); process.exit(1); });
