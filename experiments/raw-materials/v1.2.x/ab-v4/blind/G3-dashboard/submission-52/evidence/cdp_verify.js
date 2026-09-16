// CDP 交互验证：真实点击筛选按钮，比对指标卡/图表/active 样式与 Python 预期，采集控制台错误并截图。
// 运行：node cdp_verify.js（本脚本位于交付目录 evidence/ 下）
"use strict";
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9223;
const URL_ = "file:///<实验根目录>/ab-v4/G3-dashboard/A2/index.html";
const OUT = __dirname;

// 预期值来源：evidence/verify_data.py 独立复算（显示格式按页面 fmt 规则）
const EXPECT = {
  all: { total: "2,036 万", avg: "169.7 万", peak: "12月", peakHint: "268 万元", months: ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"], values: [128,96,142,135,158,173,149,165,187,204,231,268] },
  q1:  { total: "366 万",  avg: "122 万",   peak: "3月",  peakHint: "142 万元", months: ["1月","2月","3月"], values: [128,96,142] },
  q2:  { total: "466 万",  avg: "155.3 万", peak: "6月",  peakHint: "173 万元", months: ["4月","5月","6月"], values: [135,158,173] },
  q3:  { total: "501 万",  avg: "167 万",   peak: "9月",  peakHint: "187 万元", months: ["7月","8月","9月"], values: [149,165,187] },
  q4:  { total: "703 万",  avg: "234.3 万", peak: "12月", peakHint: "268 万元", months: ["10月","11月","12月"], values: [204,231,268] },
};
const ORDER = ["all", "q1", "q2", "q3", "q4"];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const results = { states: {}, errors: [], exceptions: [] };
  const chrome = spawn(CHROME, [
    `--remote-debugging-port=${PORT}`, "--headless=new", "--disable-gpu",
    "--no-first-run", `--user-data-dir=${path.join(OUT, ".chrome-tmp")}`, "about:blank",
  ], { stdio: "ignore" });

  try {
    let target;
    for (let i = 0; i < 50; i++) {
      await sleep(200);
      try {
        const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
        target = list.find((t) => t.type === "page");
        if (target) break;
      } catch {}
    }
    if (!target) throw new Error("CDP target 未就绪");
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

    let mid = 0;
    const pending = new Map();
    const events = [];
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
      else if (msg.method) events.push(msg);
    };
    const send = (method, params = {}) => new Promise((res) => {
      const id = ++mid;
      pending.set(id, res);
      ws.send(JSON.stringify({ id, method, params }));
    });

    await send("Page.enable");
    await send("Runtime.enable");
    // 双通道错误收集：页面内 onerror + CDP 事件
    await send("Page.addScriptToEvaluateOnNewDocument", { source: `
      window.__pageErrors = [];
      window.onerror = function(msg, src, line, col) { window.__pageErrors.push(String(msg)); };
      window.addEventListener("unhandledrejection", function(e) { window.__pageErrors.push(String(e.reason)); });` });

    ws.send(JSON.stringify({ id: ++mid, method: "Page.navigate", params: { url: URL_ } }));
    await sleep(1500);

    const readState = async (key) => {
      const r = await send("Runtime.evaluate", { returnByValue: true, expression: `(() => {
        const q = (s) => document.querySelector(s);
        const activeBtn = q("#filters button.active");
        const cs = activeBtn ? getComputedStyle(activeBtn) : null;
        const texts = Array.from(q("#chart").querySelectorAll("svg text")).map((t) => t.textContent);
        return {
          total: q("#kpi-total").textContent,
          avg: q("#kpi-avg").textContent,
          peak: q("#kpi-peak").textContent,
          peakHint: q("#kpi-peak-hint").textContent,
          title: q("#chart-title").textContent,
          activeBtn: activeBtn ? activeBtn.getAttribute("data-range") : null,
          activeBg: cs ? cs.backgroundColor : null,
          svgCount: document.querySelectorAll("#chart svg").length,
          chartTexts: texts,
          pageErrors: window.__pageErrors,
        };
      })()` });
      if (r.result && r.result.exceptionDetails) throw new Error("evaluate 异常: " + JSON.stringify(r.result.exceptionDetails));
      results.states[key] = r.result.result.value;
    };

    const shot = async (name) => {
      const r = await send("Page.captureScreenshot", { format: "png" });
      fs.writeFileSync(path.join(OUT, `screenshot-${name}.png`), Buffer.from(r.result.data, "base64"));
    };

    for (let i = 0; i < ORDER.length; i++) {
      const key = ORDER[i];
      // 真实 DOM 点击（headless 下 isTrusted=false 但本页无 AudioContext/节流依赖，逻辑可测）
      await send("Runtime.evaluate", { expression: `document.querySelector('#filters button[data-range="${key}"]').click()` });
      await sleep(300);
      await readState(key);
      if (key === "all" || key === "q1") await shot(key);
    }

    for (const e of events) {
      if (e.method === "Runtime.consoleAPICalled" && e.params.type === "error") {
        results.errors.push(e.params.args.map((a) => a.value ?? a.description ?? "").join(" "));
      }
      if (e.method === "Runtime.exceptionThrown") {
        results.exceptions.push(e.params.exceptionDetails.text + " " + (e.params.exceptionDetails.exception?.description || ""));
      }
    }

    // 比对
    const problems = [];
    for (const key of ORDER) {
      const s = results.states[key], x = EXPECT[key];
      const eq = (a, b, what) => { if (a !== b) problems.push(`${key}.${what}: got "${a}" expect "${b}"`); };
      eq(s.total, x.total, "total");
      eq(s.avg, x.avg, "avg");
      eq(s.peak, x.peak, "peak");
      eq(s.peakHint, x.peakHint, "peakHint");
      eq(s.activeBtn, key, "activeBtn");
      eq(s.activeBg, "rgb(37, 99, 235)", "activeBg(#2563eb)");
      if (s.svgCount !== 1) problems.push(`${key}.svgCount: ${s.svgCount}`);
      // 图表 text 序列 = Y 轴刻度 ×k + (数值,月份) 交替对 ×n → 取末尾 2n 个
      const tail = s.chartTexts.slice(-2 * x.values.length);
      const vals = tail.filter((_, i) => i % 2 === 0).map(Number);
      const mons = tail.filter((_, i) => i % 2 === 1);
      if (s.chartTexts[0] !== "0") problems.push(`${key}.yAxisFirstTick: ${s.chartTexts[0]}`);
      if (JSON.stringify(vals) !== JSON.stringify(x.values)) problems.push(`${key}.chartValues: ${JSON.stringify(vals)}`);
      if (JSON.stringify(mons) !== JSON.stringify(x.months)) problems.push(`${key}.chartMonths: ${JSON.stringify(mons)}`);
      if ((s.pageErrors || []).length) problems.push(`${key}.pageErrors: ${JSON.stringify(s.pageErrors)}`);
    }
    if (results.errors.length) problems.push("console.error: " + JSON.stringify(results.errors));
    if (results.exceptions.length) problems.push("exceptions: " + JSON.stringify(results.exceptions));

    const summary = {
      pass: problems.length === 0,
      problems,
      checked: `${ORDER.length} 个筛选状态 × (3 指标卡 + peakHint + active按钮 + active背景色 + SVG图表数值/月份序列 + 页面错误)`,
      consoleErrors: results.errors,
      exceptions: results.exceptions,
    };
    fs.writeFileSync(path.join(OUT, "cdp_result.json"), JSON.stringify(summary, null, 1));
    console.log(JSON.stringify(summary, null, 1));
    ws.close();
  } finally {
    chrome.kill();
    await sleep(500);
    fs.rmSync(path.join(OUT, ".chrome-tmp"), { recursive: true, force: true });
  }
}

main().catch((e) => { console.error("VERIFY_SCRIPT_FAIL:", e.message); process.exit(1); });
