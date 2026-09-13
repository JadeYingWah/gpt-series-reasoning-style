/*
 * prof.js —— 真实 Chrome 里对 app.html 做大输入耗时拆解（零依赖）
 * 用法： node prof.js
 * 目的：区分「JSON 解析/序列化」「DOM 赋值」各自的耗时，判断是否真会卡死
 */
"use strict";

const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PAGE_URL = "file:///" + path.join(__dirname, "app.html").replace(/\\/g, "/");
const PORT = 9334;
const PROFILE = fs.mkdtempSync(path.join(os.tmpdir(), "base02-prof-"));
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async function main() {
  const chrome = spawn(CHROME, [
    "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
    "--remote-debugging-port=" + PORT, "--user-data-dir=" + PROFILE,
    "--window-size=1280,900", PAGE_URL
  ], { stdio: "ignore" });
  process.on("exit", () => { try { chrome.kill(); } catch (e) {} });

  let wsUrl = null;
  for (let i = 0; i < 60 && !wsUrl; i++) {
    await sleep(500);
    try {
      const list = await (await fetch("http://127.0.0.1:" + PORT + "/json/list")).json();
      const p = list.find(t => t.type === "page" && t.webSocketDebuggerUrl);
      if (p) { wsUrl = p.webSocketDebuggerUrl; }
    } catch (e) {}
  }
  if (!wsUrl) { console.error("CDP 连接失败"); process.exit(1); }

  const ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("ws fail")); });
  let id = 0; const pend = new Map();
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.rej(new Error(JSON.stringify(m.error))) : p.res(m.result); }
  };
  const send = (method, params) => new Promise((res, rej) => { const i = ++id; pend.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params: params || {} })); setTimeout(() => { if (pend.has(i)) { pend.delete(i); rej(new Error(method + " 超时")); } }, 300000); });
  const ev = async (expr, awaitP) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: !!awaitP });
    if (r.exceptionDetails) { throw new Error("页面异常：" + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text)); }
    return r.result.value;
  };
  await send("Runtime.enable");
  await sleep(300);

  // 页面内：按阶段计时，只回传数字，不回传大字符串
  await ev(`
    window.__prof = function (n) {
      var gen = JSON.stringify(Array.from({length:n}, function(_,i){return {i:i,name:'item-'+i,ok:i%2===0,v:i*1.5};}));
      var inBytes = new TextEncoder().encode(gen).length;
      var t = {};
      var t0 = performance.now();
      var parsed = JSON.parse(gen);
      t.parse = performance.now() - t0;
      t0 = performance.now();
      var pretty = JSON.stringify(parsed, null, 2);
      t.stringifyPretty = performance.now() - t0;
      t0 = performance.now();
      var mini = JSON.stringify(parsed);
      t.stringifyMini = performance.now() - t0;
      var ta = document.getElementById('input');
      t0 = performance.now();
      ta.value = gen;
      t.inputAssign = performance.now() - t0;
      var out = document.getElementById('output');
      t0 = performance.now();
      out.value = pretty;
      t.outputAssign = performance.now() - t0;
      t0 = performance.now();
      document.getElementById('btnSample'); // 空操作占位
      t.inMeta = performance.now() - t0;
      t.inChars = gen.length; t.inBytes = inBytes; t.prettyChars = pretty.length;
      return t;
    }; 'ok';
  `);
  // utf8Bytes 的成本（输入事件里会跑）
  const t = await ev("window.__prof(1)", true);
  console.log("预热完成");

  for (const n of [2000, 20000, 60000, 200000, 400000]) {
    const r = await ev("window.__prof(" + n + ")", true);
    console.log(
      "n=" + String(n).padStart(6) +
      " 输入 " + (r.inBytes / 1048576).toFixed(2) + "MB" +
      " | parse " + r.parse.toFixed(1) +
      " | stringify(indent2) " + r.stringifyPretty.toFixed(1) +
      " | stringify(min) " + r.stringifyMini.toFixed(1) +
      " | textarea输入赋值 " + r.inputAssign.toFixed(1) +
      " | textarea输出赋值 " + r.outputAssign.toFixed(1) + " ms"
    );
  }

  // 端到端（点按钮 -> 结果就绪）在 browsertest.js 的 B3 里测，这里只做耗时拆解

  console.log("\n（profile 完成）");
  try { chrome.kill(); } catch (e) {}
  try { fs.rmSync(PROFILE, { recursive: true, force: true }); } catch (e) {}
  process.exit(0);
})().catch(e => { console.error("prof 异常：" + (e && e.stack || e)); process.exit(2); });
