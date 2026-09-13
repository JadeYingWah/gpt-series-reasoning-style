/*
 * browsertest.js —— 用真实 Chrome（headless + CDP）验证 app.html
 * 零依赖：Node 22 内置 WebSocket / fetch
 * 用法： node browsertest.js
 * 产出：控制台结果 + screenshot.png（真实渲染截图）
 */
"use strict";

const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PAGE_URL = "file:///" + path.join(__dirname, "app.html").replace(/\\/g, "/");
const PORT = 9333;
const PROFILE = fs.mkdtempSync(path.join(os.tmpdir(), "base02-chrome-"));

let pass = 0, fail = 0;
const failures = [];
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  PASS  " + name); }
  else { fail++; failures.push(name + (extra ? " :: " + extra : "")); console.log("  FAIL  " + name + (extra ? " :: " + extra : "")); }
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* ---------------- CDP 极简客户端 ---------------- */
class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.events = []; }
  static async connect(url) {
    const ws = new WebSocket(url);
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("ws 连接失败")); });
    const c = new CDP(ws);
    ws.onmessage = ev => {
      const m = JSON.parse(ev.data);
      if (m.id && c.pending.has(m.id)) {
        const { res, rej } = c.pending.get(m.id); c.pending.delete(m.id);
        m.error ? rej(new Error(m.method + " " + JSON.stringify(m.error))) : res(m.result);
      } else if (m.method) { c.events.push(m); }
    };
    return c;
  }
  send(method, params) {
    const id = ++this.id;
    return new Promise((res, rej) => {
      this.pending.set(id, { res, rej });
      this.ws.send(JSON.stringify({ id, method, params: params || {} }));
      setTimeout(() => { if (this.pending.has(id)) { this.pending.delete(id); rej(new Error(method + " 超时")); } }, 180000);
    });
  }
  async eval(expr, awaitPromise) {
    const r = await this.send("Runtime.evaluate", {
      expression: expr, returnByValue: true, awaitPromise: !!awaitPromise, userGesture: true
    });
    if (r.exceptionDetails) {
      throw new Error("页面内异常：" + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text));
    }
    return r.result.value;
  }
}

/* ---------------- 页面内测试脚本 ---------------- */
const PAGE_HARNESS = `
window.__t = {
  el: function (id) { return document.getElementById(id); },
  status: function () {
    var b = document.getElementById("errbox");
    return { kind: b.className, badge: b.querySelector(".badge").textContent,
             text: document.getElementById("errmsg").innerText };
  },
  wait: function () {
    return new Promise(function (res) {
      var t0 = Date.now();
      (function poll() {
        if (!document.getElementById("btnPretty").disabled) { return res(true); }
        if (Date.now() - t0 > 120000) { return res(false); }
        setTimeout(poll, 5);
      })();
    });
  },
  run: function (kind, text) {
    var ta = document.getElementById("input");
    ta.value = text;
    ta.dispatchEvent(new Event("input", { bubbles: true }));
    var t0 = performance.now();
    document.getElementById(kind === "minify" ? "btnMinify" : "btnPretty").click();
    return window.__t.wait().then(function () {
      return { ms: performance.now() - t0, out: document.getElementById("output").value,
               st: window.__t.status() };
    });
  },
  click: function (id) { document.getElementById(id).click(); }
};
"ready";
`;

(async function main() {
  console.log("Chrome: " + CHROME);
  console.log("页面:   " + PAGE_URL);
  const chrome = spawn(CHROME, [
    "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
    "--remote-debugging-port=" + PORT, "--user-data-dir=" + PROFILE,
    "--window-size=1280,900", PAGE_URL
  ], { stdio: "ignore" });

  const cleanup = () => { try { chrome.kill(); } catch (e) {} };
  process.on("exit", cleanup);

  let wsUrl = null;
  for (let i = 0; i < 60 && !wsUrl; i++) {
    await sleep(500);
    try {
      const list = await (await fetch("http://127.0.0.1:" + PORT + "/json/list")).json();
      // 必须精确挑到我们加载的那个页面，避免连到别的 tab / 别的 Chrome 实例
      const page = list.find(t => t.type === "page" && t.webSocketDebuggerUrl && /app\.html/i.test(t.url || ""));
      if (page) { wsUrl = page.webSocketDebuggerUrl; }
    } catch (e) { /* 还没起来 */ }
  }
  if (!wsUrl) { console.error("无法连接到 Chrome CDP（未找到 app.html 页面目标）"); cleanup(); process.exit(1); }

  const cdp = await CDP.connect(wsUrl);
  await cdp.send("Runtime.enable");
  await cdp.send("Page.enable");
  // 等页面 DOM 就绪
  for (let i = 0; i < 100; i++) {
    const ready = await cdp.eval("document.readyState === 'complete' && !!document.getElementById('input')");
    if (ready) { break; }
    await sleep(100);
  }
  await cdp.eval(PAGE_HARNESS);

  console.log("\n== B1. 真实浏览器中的美化 / 压缩 ==");
  const obj = { z: 1, a: [1, 2, { c: "中文", d: null }], n: -1500, ok: true };
  const raw = JSON.stringify(obj);
  let r = await cdp.eval("window.__t.run('pretty', " + JSON.stringify(raw) + ")", true);
  ok("真实浏览器：美化输出 == JSON.stringify(x,null,2)", r.out === JSON.stringify(obj, null, 2), r.out.slice(0, 80));
  ok("真实浏览器：美化状态为成功", r.st.kind === "ok", r.st.kind);
  ok("真实浏览器：状态徽章为“成功”", r.st.badge === "成功", r.st.badge);
  r = await cdp.eval("window.__t.run('minify', " + JSON.stringify(JSON.stringify(obj, null, 2)) + ")", true);
  ok("真实浏览器：压缩输出 == JSON.stringify(x)", r.out === raw, r.out.slice(0, 80));

  console.log("\n== B2. 真实浏览器中的错误定位 ==");
  r = await cdp.eval("window.__t.run('pretty', '{\\n  \"a\": 1,\\n  \"b\" 2\\n}')", true);
  ok("真实浏览器：定位到第 3 行", /第\s*3\s*行/.test(r.st.text), r.st.text.replace(/\n/g, " | ").slice(0, 140));
  ok("真实浏览器：给出列号与偏移", /第\s*\d+\s*列/.test(r.st.text) && /字符偏移/.test(r.st.text));
  ok("真实浏览器：错误时结果区为空", r.out === "");
  ok("真实浏览器：错误徽章为“错误”", r.st.badge === "错误", r.st.badge);

  console.log("\n== B3. 真实浏览器中的大输入（≥100KB） ==");
  // 大字符串全部在页面内生成/比对，只回传数字，避免 CDP 传 MB 级 JSON 文本
  await cdp.eval(`
    window.__t.runBig = function (kind, n) {
      var gen = JSON.stringify(Array.from({length:n}, function(_,i){return {i:i,name:'item-'+i,ok:i%2===0,v:i*1.5};}));
      var expect = kind === 'minify' ? JSON.stringify(JSON.parse(gen)) : JSON.stringify(JSON.parse(gen), null, 2);
      var inChars = gen.length, inBytes = new TextEncoder().encode(gen).length;
      var ta = document.getElementById('input');
      ta.value = gen;
      ta.dispatchEvent(new Event('input', {bubbles:true}));
      var t0 = performance.now();
      document.getElementById(kind === 'minify' ? 'btnMinify' : 'btnPretty').click();
      function poll(){
        if (document.getElementById('btnPretty').disabled) { return new Promise(function(r){ setTimeout(r,1); }).then(poll); }
      }
      return Promise.resolve().then(poll).then(function(){
        var ms = performance.now() - t0;
        var out = document.getElementById('output').value;
        return { ms: ms, inBytes: inBytes, inChars: inChars, outChars: out.length,
                 exact: out === expect, kind: document.getElementById('errbox').className,
                 st: document.getElementById('errmsg').innerText.slice(0, 120) };
      });
    }; 'ok';
  `);
  for (const [n, label] of [[5000, "约 250KB"], [40000, "约 2MB"], [100000, "约 5MB"]]) {
    const t0 = Date.now();
    const res = await cdp.eval("window.__t.runBig('pretty', " + n + ")", true);
    const wall = Date.now() - t0;
    const mb = (res.inBytes / 1048576).toFixed(2);
    ok("真实浏览器：" + label + "（" + mb + "MB 输入）美化成功且无异常", res.kind === "ok", res.kind + " " + res.st);
    ok("真实浏览器：" + mb + "MB 输入美化结果与 JSON.stringify(x,null,2) 逐字节一致", res.exact === true,
       "outChars=" + res.outChars);
    console.log("        输入 " + mb + "MB → 页面内耗时 " + res.ms.toFixed(0) + " ms，端到端(含 CDP) ≈ " + wall + " ms");
  }
  {
    const res = await cdp.eval("window.__t.runBig('minify', 100000)", true);
    ok("真实浏览器：5MB 美化文本压缩成功且一致", res.kind === "ok" && res.exact === true, res.kind + " outChars=" + res.outChars);
    console.log("        压缩 5MB → 页面内耗时 " + res.ms.toFixed(0) + " ms");
  }

  console.log("\n== B4. 真实浏览器中的复制按钮 ==");
  r = await cdp.eval("window.__t.run('pretty', '{\"a\":1}')", true);
  await cdp.eval("window.__t.click('btnCopy'); 'x'");
  await sleep(400);
  let cst = await cdp.eval("window.__t.status()");
  ok("真实浏览器：复制后给出明确反馈（成功或提示全选）",
     cst.kind === "ok" || (cst.kind === "warn" && /Ctrl\+C/.test(cst.text)), cst.kind + " :: " + cst.text.slice(0, 90));
  console.log("        剪贴板实际结果：" + cst.kind + " / " + cst.text.slice(0, 60));
  await cdp.eval("window.__t.click('btnClear'); 'x'");
  await sleep(100);
  await cdp.eval("window.__t.click('btnCopy'); 'x'");
  await sleep(200);
  const cst2 = await cdp.eval("window.__t.status()");
  ok("真实浏览器：空结果复制 -> 警告不崩溃", cst2.kind === "warn", cst2.kind);

  console.log("\n== B5. 页面级异常检查（console error / 未捕获异常） ==");
  const bad = cdp.events.filter(e =>
    e.method === "Runtime.exceptionThrown" ||
    (e.method === "Runtime.consoleAPICalled" && e.params.type === "error"));
  ok("全程无未捕获异常 / console.error", bad.length === 0,
     bad.map(e => JSON.stringify(e.params).slice(0, 160)).join(" | "));

  console.log("\n== B6. 真实渲染截图 ==");
  await cdp.eval("window.__t.run('pretty', JSON.stringify({name:'截图样例',list:[1,2,3],ok:true}, null, 0))", true);
  await sleep(200);
  const shot = await cdp.send("Page.captureScreenshot", { format: "png" });
  const png = path.join(__dirname, "screenshot.png");
  fs.writeFileSync(png, Buffer.from(shot.data, "base64"));
  const st = fs.statSync(png);
  ok("已生成真实渲染截图 screenshot.png（非空 PNG）", st.size > 5000, st.size + " bytes");
  console.log("        " + png + " (" + st.size + " bytes)");

  console.log("\n================ 真实浏览器结果 ================");
  console.log("PASS = " + pass + " , FAIL = " + fail);
  cleanup();
  if (failures.length) {
    console.log("失败项：");
    failures.forEach(f => console.log("  - " + f));
    process.exit(1);
  }
  process.exit(0);
})().catch(async e => {
  console.error("浏览器自检异常：" + (e && e.stack || e));
  try { fs.rmSync(PROFILE, { recursive: true, force: true }); } catch (x) {}
  process.exit(2);
});
