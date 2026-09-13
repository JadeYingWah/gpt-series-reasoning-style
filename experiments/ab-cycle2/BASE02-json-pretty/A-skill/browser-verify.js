/**
 * BASE02 / A 臂 —— 真实浏览器实操验收（Chrome + CDP，Node 22 内置 WebSocket/fetch，无第三方依赖）
 * 运行： node browser-verify.js
 * 产物： browser-report.txt / browser-report.json / browser-shot-*.png
 */
"use strict";
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");
const net = require("net");

const DIR = __dirname;
const REPORT = path.join(DIR, "browser-report.txt");
const REPORT_JSON = path.join(DIR, "browser-report.json");
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const FILE_URL = "file:///" + path.join(DIR, "app.html").replace(/\\/g, "/");
const PROFILE = path.join(os.tmpdir(), "cdp-base02-profile");
let PORT = 0; // 运行时动态选取空闲端口，避免与其他 Agent 的调试端口撞车

const lines = [], records = [];
let pass = 0, fail = 0;
const log = s => lines.push(s);
const check = (cond, name, detail) => {
  if (cond) { pass++; records.push({ name, status: "PASS", detail: detail || "" }); log("  [PASS] " + name + (detail ? "  -> " + detail : "")); }
  else { fail++; records.push({ name, status: "FAIL", detail: detail || "" }); log("  [FAIL] " + name + (detail ? "  -> " + detail : "")); }
};
const section = t => { log(""); log("=== " + t + " ==="); };
const sleep = ms => new Promise(r => setTimeout(r, ms));

/** 动态选取一个空闲端口：先 bind 成功再释放，避免与其他 Agent 的 CDP 端口冲突 */
function pickFreePort(start) {
  return new Promise((resolve, reject) => {
    let p = start;
    const tryOne = () => {
      if (p > start + 400) return reject(new Error("找不到空闲端口"));
      const srv = net.createServer();
      srv.once("error", () => { p++; tryOne(); });
      srv.listen(p, "127.0.0.1", () => {
        const got = srv.address().port;
        srv.close(() => resolve(got));
      });
    };
    tryOne();
  });
}

let child = null, cdp = null, netRequests = [], exceptions = [], consoleErrors = [];

async function main() {
  section("0. 启动 Chrome 并连接 CDP");
  PORT = await pickFreePort(21000 + (process.pid % 5000));
  log("  选用空闲调试端口: " + PORT + "（动态选取，避免与其他 Agent 撞车）");
  fs.rmSync(PROFILE, { recursive: true, force: true });
  child = spawn(CHROME, [
    "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
    "--disable-extensions", "--disable-background-networking", "--mute-audio",
    "--remote-debugging-port=" + PORT, "--user-data-dir=" + PROFILE,
    "--allow-file-access-from-files", "--window-size=1280,900", "about:blank"
  ], { stdio: "ignore" });

  const version = await waitFor(async () => {
    const r = await fetch("http://127.0.0.1:" + PORT + "/json/version");
    return r.ok ? r.json() : null;
  }, 25000);
  check(!!version && !!version.webSocketDebuggerUrl, "Chrome 已启动，DevTools 端口就绪",
    version && version.Browser);

  const targets = await (await fetch("http://127.0.0.1:" + PORT + "/json/list")).json();
  const stray = targets.filter(t => t.type === "page" && t.url !== "about:blank");
  // 关键护栏：如果这个浏览器实例上已经开着别家页面，说明连错了实例，必须立刻停手
  check(stray.length === 0, "连到的是本脚本新建的干净实例（无他人的页面目标）",
    stray.length ? "发现非空白目标: " + JSON.stringify(stray.map(t => t.url)) : "仅有 about:blank");
  if (stray.length) throw new Error("检测到端口上已有其他会话的页面，已中止以免干扰他人：" + JSON.stringify(stray.map(t => t.url)));
  const page = targets.find(t => t.type === "page");
  check(!!page, "找到 page 目标", page && page.url);

  cdp = await connect(page.webSocketDebuggerUrl);
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Network.enable");
  await cdp.send("Log.enable");
  await cdp.send("Emulation.setDeviceMetricsOverride",
    { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });

  cdp.on(msg => {
    if (msg.method === "Network.requestWillBeSent") netRequests.push(msg.params.request.url);
    if (msg.method === "Runtime.exceptionThrown") exceptions.push(JSON.stringify(msg.params.exceptionDetails));
    if (msg.method === "Log.entryAdded" && msg.params.entry.level === "error") consoleErrors.push(msg.params.entry.text);
    if (msg.method === "Runtime.consoleAPICalled" && msg.params.type === "error") {
      consoleErrors.push((msg.params.args || []).map(a => a.value).join(" "));
    }
  });

  section("1. 以 file:// 离线打开 app.html");
  await cdp.send("Page.navigate", { url: FILE_URL });
  await waitFor(() => ev("!!(window.__JSONToolUI && window.JSONTool)"), 15000);
  check(true, "页面加载完成，__JSONToolUI / JSONTool 就绪");
  const ready = await ev("({title:document.title, btnPretty:!!document.getElementById('btn-pretty'), btnMinify:!!document.getElementById('btn-minify'), btnCopy:!!document.getElementById('btn-copy'), hasClipboard:!!(navigator.clipboard&&navigator.clipboard.writeText), secure:window.isSecureContext})");
  check(ready.btnPretty && ready.btnMinify && ready.btnCopy, "三个核心按钮均存在于 DOM", JSON.stringify(ready));
  log("  环境: navigator.clipboard=" + ready.hasClipboard + " isSecureContext=" + ready.secure);

  section("2. 交互 1：粘贴 JSON → 一键美化（2 空格）");
  const src = '{"b":2,"a":[1,{"c":true}]}';
  await ev("__JSONToolUI.setInput(" + JSON.stringify(src) + ")");
  const r1 = await clickAndWait("btn-pretty");
  const s1 = await ev("({out:__JSONToolUI.getOutput(), fb:__JSONToolUI.getFeedback(), err:__JSONToolUI.getError()})");
  const expectPretty = '{\n  "b": 2,\n  "a": [\n    1,\n    {\n      "c": true\n    }\n  ]\n}';
  check(s1.out === expectPretty, "美化输出严格 2 空格缩进且键序保持原序",
    JSON.stringify(s1.out));
  check(/feedback ok/.test(s1.fb.cls) && /已美化/.test(s1.fb.text), "状态条给出成功反馈", s1.fb.text);
  check(s1.err.hidden === true, "错误面板保持隐藏");
  check(r1.ms < 2000, "美化点击→反馈耗时 " + r1.ms + " ms（有即时反馈）");
  await shot("browser-shot-1-pretty.png");

  section("3. 交互 2：一键压缩");
  const r2 = await clickAndWait("btn-minify");
  const s2 = await ev("({out:__JSONToolUI.getOutput(), fb:__JSONToolUI.getFeedback()})");
  check(s2.out === '{"b":2,"a":[1,{"c":true}]}', "压缩输出无多余空白", JSON.stringify(s2.out));
  check(/feedback ok/.test(s2.fb.cls) && /已压缩/.test(s2.fb.text), "压缩成功反馈", s2.fb.text);
  check(r2.ms < 2000, "压缩点击→反馈耗时 " + r2.ms + " ms");

  section("4. 交互 3：非法 JSON 显示具体错误位置");
  await ev("__JSONToolUI.setInput(" + JSON.stringify('{"a":1,}') + ")");
  await clickAndWait("btn-pretty");
  const s3 = await ev("({fb:__JSONToolUI.getFeedback(), err:__JSONToolUI.getError(), excerpt:document.getElementById('error-excerpt').textContent, out:__JSONToolUI.getOutput(), outMetric:document.getElementById('out-metric').textContent})");
  check(s3.err.hidden === false, "错误面板已显示", JSON.stringify(s3.err.msg));
  check(s3.out === "" && /解析失败/.test(s3.outMetric),
    "解析失败时清空结果区，不残留上一次的成功结果（回归断言）",
    "结果=" + JSON.stringify(s3.out) + " 计数显示=" + s3.outMetric);
  check(/第 1 行，第 8 列/.test(s3.err.loc), "定位文案含「第 1 行，第 8 列」", s3.err.loc);
  check(/尾随逗号/.test(s3.err.msg), "错误信息说明了原因", s3.err.msg);
  check(/\^/.test(s3.excerpt), "错误摘录带插入符定位", JSON.stringify(s3.excerpt));
  check(/feedback err/.test(s3.fb.cls), "状态条切换为错误态", s3.fb.cls);
  await shot("browser-shot-2-error.png");

  // 多行非法输入的行号
  await ev("__JSONToolUI.setInput(" + JSON.stringify('{\n  "a": 1,\n  "b": ,\n  "c": 3\n}') + ")");
  await clickAndWait("btn-pretty");
  const s3b = await ev("__JSONToolUI.getError()");
  check(/第 3 行，第 8 列/.test(s3b.loc), "多行输入定位到第 3 行第 8 列", s3b.loc);

  section("5. 交互 4：一键复制结果");
  // 尝试授予剪贴板读写权限，以便「真正读回」核验复制内容
  let granted = "未尝试";
  try {
    await cdp.send("Browser.grantPermissions",
      { origin: "file://", permissions: ["clipboardReadWrite", "clipboardSanitizedWrite"] });
    granted = "已授予";
  } catch (e) { granted = "授予失败: " + String(e.message).slice(0, 120); }
  log("  Browser.grantPermissions -> " + granted);
  await ev("__JSONToolUI.setInput(" + JSON.stringify(src) + ")");
  await clickAndWait("btn-pretty");
  const expectedCopy = await ev("__JSONToolUI.getOutput()");
  await ev("document.getElementById('btn-copy').click()");
  await sleep(600);
  const s4 = await ev("__JSONToolUI.getFeedback()");
  const copyState = await ev("__JSONToolUI.state.lastCopy || null");
  log("  lastCopy = " + JSON.stringify(copyState));
  // 读回剪贴板（若浏览器允许）。注意 Windows 剪贴板会把 \n 归一化为 \r\n，
  // 因此比对前必须做行尾归一化，否则长度会「多出」换行符个数。
  try { await cdp.send("Page.bringToFront"); } catch (e) {}
  await sleep(200);
  const back = await ev("(async()=>{try{ if(!navigator.clipboard||!navigator.clipboard.readText) return {ok:false,why:'no-api'};"
    + " const raw=await navigator.clipboard.readText();"
    + " const t=raw.replace(/\\r\\n/g,'\\n');"
    + " return {ok:true, rawLen:raw.length, crlf:(raw.match(/\\r\\n/g)||[]).length, normLen:t.length,"
    + " equal: t === " + JSON.stringify(expectedCopy) + ", head:t.slice(0,20)};"
    + "}catch(e){return {ok:false,why:String(e&&e.message||e)}}})()");
  log("  剪贴板读回 = " + JSON.stringify(back));
  check(/feedback ok/.test(s4.cls) && /已复制/.test(s4.text), "复制按钮给出成功反馈", s4.text);
  if (copyState && copyState.ok && back.ok) {
    check(back.equal === true,
      "剪贴板内容与结果逐字符一致（真实读回，仅做 \\r\\n→\\n 行尾归一化）",
      "归一化后长度=" + back.normLen + " 期望=" + expectedCopy.length);
    check(back.normLen === expectedCopy.length && back.head === expectedCopy.slice(0, 20),
      "读回内容长度与前 20 字符吻合", JSON.stringify(back.head) + " ｜ " + back.normLen);
    check(back.rawLen === expectedCopy.length + back.crlf,
      "原始长度 = 结果长度 + CRLF 归一化增量（差异可完整解释，非内容丢失）",
      back.rawLen + " = " + expectedCopy.length + " + " + back.crlf);
  } else {
    records.push({ name: "剪贴板内容一致性", status: "UNVERIFIED", detail: "浏览器未授予剪贴板读取权限，无法读回比对: " + JSON.stringify(back && back.why) });
    log("  [UNVERIFIED] 剪贴板内容一致性（读回被拒，见上）");
  }

  section("6. 交互 5：清空 / 载入示例 / 快捷键");
  await ev("document.getElementById('btn-clear').click()");
  const cl = await ev("({inp:document.getElementById('input').value, out:__JSONToolUI.getOutput(), fb:__JSONToolUI.getFeedback()})");
  check(cl.inp === "" && cl.out === "", "清空按钮同时清空输入与结果", cl.fb.text);
  check(/feedback info/.test(cl.fb.cls), "清空后状态条为中性提示", cl.fb.cls);

  await ev("document.getElementById('btn-sample').click()");
  const sm = await ev("({len:document.getElementById('input').value.length, metric:document.getElementById('in-metric').textContent, fb:__JSONToolUI.getFeedback()})");
  check(sm.len > 0 && /字符/.test(sm.metric), "载入示例：输入框与字符计数同步更新",
    "长度=" + sm.len + " 计数=" + sm.metric);

  // 快捷键是异步链路（rAF + setTimeout）：在**同一次求值内**派发并读状态，避免读取时机竞态
  const ksBusy = await ev("(function(){document.getElementById('input').focus();document.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',ctrlKey:true,bubbles:true}));return __JSONToolUI.getFeedback();})()");
  const ksWait = await clickFeedbackDone(8000);
  const ks = await ev("({out:__JSONToolUI.getOutput().length, fb:__JSONToolUI.getFeedback()})");
  check(/正在美化/.test(ksBusy.text), "Ctrl+Enter 触发处理（按键后立即进入处理态）", ksBusy.text);
  check(ks.out > 0 && /feedback ok/.test(ks.fb.cls), "Ctrl+Enter 快捷键完成美化",
    "结果长度=" + ks.out + " ｜ 等待 " + ksWait.ms + " ms ｜ " + ks.fb.text);

  // 注意：必须先确保输入非空，否则会走到「输入为空」告警分支（这本身是正确的边界行为）
  await ev("__JSONToolUI.setInput(" + JSON.stringify(src) + ")");
  const kmBusy = await ev("(function(){document.getElementById('input').focus();document.dispatchEvent(new KeyboardEvent('keydown',{key:'M',ctrlKey:true,shiftKey:true,bubbles:true}));return __JSONToolUI.getFeedback();})()");
  const kmW = await clickFeedbackDone(8000);
  const km = await ev("({out:__JSONToolUI.getOutput(), fb:__JSONToolUI.getFeedback()})");
  check(/正在压缩/.test(kmBusy.text), "Ctrl+Shift+M 触发处理（立即进入处理态）", kmBusy.text);
  check(km.out === '{"b":2,"a":[1,{"c":true}]}' && /feedback ok/.test(km.fb.cls),
    "Ctrl+Shift+M 快捷键完成压缩", JSON.stringify(km.out) + " ｜ " + kmW.ms + " ms ｜ " + km.fb.text);

  section("7. 大输入（>100KB）不卡死");
  const bigLen = await ev("(function(){const a=[];for(let i=0;i<3000;i++)a.push({id:i,name:'项目'+i,tags:['a','b','c'],ok:i%2===0,score:i*1.5});window.__BIG=JSON.stringify({total:3000,items:a});return window.__BIG.length;})()");
  const bigBytes = await ev("new TextEncoder().encode(window.__BIG).length");
  check(bigBytes > 100 * 1024, "构造输入 " + bigBytes + " 字节（>" + (100 * 1024) + "）", bigLen + " 字符");
  await ev("__JSONToolUI.setInput(window.__BIG)");
  const t0 = Date.now();
  // 同一次求值内先点击再读状态：process() 在调度 CPU 工作前会同步写入「处理中」，
  // 因此这里拿到 busy 就证明点击没有被长任务阻塞。
  const busySeen = await ev("(function(){document.getElementById('btn-minify').click();return __JSONToolUI.getFeedback().cls;})()");
  const r7 = await clickFeedbackDone(15000);
  const wall = Date.now() - t0;
  const s7 = await ev("({fb:__JSONToolUI.getFeedback(), outLen:__JSONToolUI.getOutput().length, equal: JSON.stringify(JSON.parse(__JSONToolUI.getOutput()))===JSON.stringify(JSON.parse(window.__BIG))})");
  check(/feedback busy/.test(busySeen), "点击后同步读到「处理中」状态（UI 未被长任务阻塞）", "点击瞬间状态=" + busySeen);
  check(/feedback ok/.test(s7.fb.cls), "大输入压缩成功", s7.fb.text);
  check(s7.equal === true, "压缩结果与原始数据语义一致（页内 JSON.parse 比对）");
  check(wall < 5000, "点击→完成总耗时 " + wall + " ms（<5s）");
  const r7b = await clickAndWait("btn-pretty", 15000);
  const s7b = await ev("({fb:__JSONToolUI.getFeedback(), len:__JSONToolUI.getOutput().length})");
  check(/feedback ok/.test(s7b.fb.cls) && s7b.len > bigLen, "大输入美化成功且输出变大（换行+缩进）",
    s7b.fb.text);
  await shot("browser-shot-3-big.png");

  section("8. 空输入边界");
  await ev("__JSONToolUI.setInput('')");
  await clickAndWait("btn-pretty");
  const s8 = await ev("__JSONToolUI.getFeedback()");
  check(/feedback warn/.test(s8.cls) && /输入为空/.test(s8.text), "空输入：中性警告而非异常", s8.text);

  section("9. 无未捕获异常 / 无网络请求");
  await sleep(400);
  check(exceptions.length === 0, "Runtime.exceptionThrown 为空（无未捕获异常）",
    exceptions.join(" | ") || "0 条");
  check(consoleErrors.length === 0, "console error 为空", consoleErrors.join(" | ") || "0 条");
  const external = netRequests.filter(u => !u.startsWith("file:///") && !u.startsWith("data:") && !u.startsWith("devtools:"));
  check(external.length === 0, "无外部网络请求（离线可用）",
    "全部请求: " + JSON.stringify([...new Set(netRequests)]));
}

async function clickAndWait(btnId, timeout = 8000) {
  const t0 = Date.now();
  await ev("document.getElementById(" + JSON.stringify(btnId) + ").click()");
  const cls = await waitFor(async () => {
    const c = await ev("__JSONToolUI.getFeedback().cls");
    return /feedback (ok|err|warn)\b/.test(c) ? c : null;
  }, timeout, 40);
  return { ms: Date.now() - t0, cls };
}
async function clickFeedbackDone(timeout) {
  const t0 = Date.now();
  await waitFor(async () => {
    const c = await ev("__JSONToolUI.getFeedback().cls");
    return /feedback (ok|err|warn)\b/.test(c) ? c : null;
  }, timeout, 40);
  return { ms: Date.now() - t0 };
}

async function shot(name) {
  const r = await cdp.send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(path.join(DIR, name), Buffer.from(r.data, "base64"));
  log("  截图已保存: " + name);
}

async function ev(expr) {
  const r = await cdp.send("Runtime.evaluate", {
    expression: expr, returnByValue: true, awaitPromise: true, userGesture: true
  });
  if (r.exceptionDetails) {
    throw new Error("页面内求值异常: " + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || JSON.stringify(r.exceptionDetails)));
  }
  return r.result.value;
}

async function waitFor(fn, timeout = 15000, interval = 200) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    try { const v = await fn(); if (v) return v; } catch (e) { /* retry */ }
    await sleep(interval);
  }
  throw new Error("waitFor 超时");
}

function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    const pending = new Map();
    const handlers = [];
    let id = 0;
    ws.onmessage = ev => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) {
        const p = pending.get(msg.id); pending.delete(msg.id);
        msg.error ? p.rej(new Error(JSON.stringify(msg.error))) : p.res(msg.result);
      } else handlers.forEach(h => h(msg));
    };
    ws.onerror = e => reject(new Error("WebSocket 错误: " + (e && e.message)));
    ws.onopen = () => resolve({
      send(method, params) {
        const mid = ++id;
        return new Promise((res, rej) => {
          pending.set(mid, { res, rej });
          ws.send(JSON.stringify({ id: mid, method, params: params || {} }));
        });
      },
      on(fn) { handlers.push(fn); },
      close() { try { ws.close(); } catch (e) {} }
    });
    setTimeout(() => reject(new Error("WebSocket 连接超时")), 15000);
  });
}

(async () => {
  let fatal = null;
  try { await main(); }
  catch (e) { fatal = e; }
  finally {
    if (fatal) { log(""); log("!!! 致命错误: " + (fatal && fatal.stack || fatal)); fail++; records.push({ name: "脚本执行", status: "FAIL", detail: String(fatal) }); }
    try { if (cdp) { await cdp.send("Browser.close"); cdp.close(); } } catch (e) {}
    try { if (child && !child.killed) child.kill(); } catch (e) {}
    await sleep(500);
    try { fs.rmSync(PROFILE, { recursive: true, force: true }); } catch (e) {}

    section("汇总");
    log("  通过: " + pass);
    log("  失败: " + fail);
    log("  结论: " + (fail === 0 ? "浏览器实操全部通过" : "存在失败项"));
    log("");
    log("  复算: cd BASE02-json-pretty/A-skill && node browser-verify.js");
    log("  被测页面: " + FILE_URL);
    log("  使用调试端口: " + PORT + "（动态选取）");
    fs.writeFileSync(REPORT, lines.join("\n") + "\n", "utf8");
    fs.writeFileSync(REPORT_JSON, JSON.stringify({ pass, fail, port: PORT, netRequests: [...new Set(netRequests)], exceptions, consoleErrors, records }, null, 2), "utf8");
    process.exitCode = fail === 0 ? 0 : 1;
    console.log(lines.join("\n"));
  }
})();
