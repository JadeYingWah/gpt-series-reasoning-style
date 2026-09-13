/*
 * selftest.js —— app.html 的离线自检脚本（Node 运行，无第三方依赖）
 * 用法： node selftest.js
 * 做法：读取 app.html 里的内联 <script>，用最小 DOM 桩跑起来，
 *       然后通过“真实点击事件处理函数”驱动按钮，检查输出与状态栏文字。
 *       剪贴板两条路径（navigator.clipboard / execCommand 回退）分别建独立实例验证。
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const HTML_PATH = path.join(__dirname, "app.html");
const html = fs.readFileSync(HTML_PATH, "utf8");

/* ---------------- 抽取内联脚本 ---------------- */
const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)];
if (scripts.length !== 1) {
  console.error("期望恰好 1 个内联 <script>，实际 " + scripts.length);
  process.exit(1);
}
const code = scripts[0][1];

/* ---------------- 最小 DOM 桩 ---------------- */
function makeEl(id) {
  const el = {
    id: id || "",
    value: "",
    className: "",
    disabled: false,
    dataset: {},
    style: {},
    _handlers: {},
    focus() { el._focused = true; },
    setSelectionRange(a, b) { el._sel = [a, b]; },
    addEventListener(t, fn) { (el._handlers[t] = el._handlers[t] || []).push(fn); },
    querySelector() { return el._badge; },
    appendChild(c) { return c; },
    removeChild(c) { return c; },
    setAttribute() {},
    select() { el._selected = true; }
  };
  // 真实 DOM 语义：设置 textContent 会清空 innerHTML，反之亦然
  let _text = "", _html = "";
  Object.defineProperty(el, "textContent", {
    get() { return _html ? _html.replace(/<[^>]*>/g, "") : _text; },
    set(v) { _text = String(v); _html = ""; },
    enumerable: true
  });
  Object.defineProperty(el, "innerHTML", {
    get() { return _html || _text; },
    set(v) { _html = String(v); _text = ""; },
    enumerable: true
  });
  el._badge = { textContent: "" };
  return el;
}

/* ---------------- 装载一个 app 实例 ---------------- */
function loadApp(opts) {
  opts = opts || {};
  const els = Object.create(null);
  const getEl = id => els[id] || (els[id] = makeEl(id));
  const uncaught = [];
  const clipboardCalls = [];

  const sandbox = {
    document: {
      getElementById: getEl,
      createElement: () => makeEl("tmp"),
      body: { appendChild() {}, removeChild() {} },
      execCommand() { clipboardCalls.push("exec"); return opts.execOk !== false; }
    },
    window: { addEventListener(t, fn) { uncaught.push([t, fn]); } },
    navigator: {
      clipboard: {
        writeText(t) {
          clipboardCalls.push("api:" + t.length);
          return opts.clipboardOk === false ? Promise.reject(new Error("NotAllowed")) : Promise.resolve();
        }
      }
    },
    performance: { now: () => Number(process.hrtime.bigint() / 1000n) / 1000 },
    setTimeout, clearTimeout, TextEncoder, console
  };

  try {
    vm.runInNewContext(code, sandbox, { filename: "app.html#script" });
  } catch (e) {
    throw new Error("脚本加载即抛异常：" + e.message);
  }

  const sleep = ms => new Promise(r => setTimeout(r, ms));
  return {
    els,
    getEl,
    clipboardCalls,
    uncaught,
    sleep,
    input: getEl("input"),
    output: getEl("output"),
    status() {
      const box = getEl("errbox");
      const msg = getEl("errmsg");
      return { kind: box.className, badge: box._badge.textContent, text: msg.innerHTML || msg.textContent };
    },
    setInput(v) {
      getEl("input").value = v;
      (getEl("input")._handlers.input || []).forEach(fn => fn({ type: "input" }));
    },
    click(id) {
      const hs = getEl(id)._handlers.click;
      if (!hs || !hs.length) { throw new Error("按钮 " + id + " 没有绑定 click"); }
      hs.forEach(fn => fn({ type: "click" }));
    },
    async settle(maxMs) {
      const t0 = Date.now();
      while (getEl("btnPretty").disabled) {
        if (Date.now() - t0 > (maxMs || 20000)) { throw new Error("处理超时未结束"); }
        await sleep(5);
      }
      await sleep(0);
    }
  };
}

/* ---------------- 断言 ---------------- */
let pass = 0, fail = 0;
const failures = [];
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  PASS  " + name); }
  else { fail++; failures.push(name + (extra ? " :: " + extra : "")); console.log("  FAIL  " + name + (extra ? " :: " + extra : "")); }
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* ---------------- 用例 ---------------- */
(async function main() {
  console.log("== 0. 静态检查：无外部依赖 ==");
  const ext = [
    [/<script[^>]+\bsrc\s*=/i, "script src"],
    [/<link[^>]+\bhref\s*=/i, "link href"],
    [/@import/i, "@import"],
    [/https?:\/\//i, "http(s) URL"],
    [/\bfetch\s*\(/, "fetch("],
    [/XMLHttpRequest/, "XMLHttpRequest"],
    [/importScripts/, "importScripts"],
    [/\bnew WebSocket/, "WebSocket"],
    [/<img\b/i, "<img>"]
  ];
  ext.forEach(([re, label]) => ok("静态：未出现 " + label, !re.test(html), re.test(html) ? "命中 " + re : ""));
  ok("静态：只有一个内联 script", scripts.length === 1);
  ok("静态：声明 charset=utf-8", /<meta charset="utf-8">/i.test(html));
  ok("静态：单文件、无 <base>/<iframe>", !/<base\b|<iframe\b/i.test(html));

  const app = loadApp();

  console.log("\n== 1. 美化（2 空格缩进）/ 压缩 ==");
  const obj = { b: 1, a: [1, 2, { c: "中文" }], d: null, e: true };
  const raw = JSON.stringify(obj);
  app.setInput(raw);
  app.click("btnPretty"); await app.settle();
  ok("美化输出 == JSON.stringify(x,null,2)", app.output.value === JSON.stringify(obj, null, 2), app.output.value.slice(0, 60));
  ok("美化输出含 2 空格缩进", /\n  "b"/.test(app.output.value));
  ok("美化后状态为 ok", app.status().kind === "ok", app.status().kind);
  app.click("btnMinify"); await app.settle();
  ok("压缩输出 == JSON.stringify(x)", app.output.value === raw);
  ok("压缩输出无换行/无缩进", app.output.value.indexOf("\n") === -1 && app.output.value.indexOf("  ") === -1);
  ok("压缩比被计算", /%$/.test(app.getEl("s-ratio").textContent), app.getEl("s-ratio").textContent);
  ok("耗时被记录", /ms$/.test(app.getEl("s-time").textContent), app.getEl("s-time").textContent);
  ok("元信息统计了字符数", /字符/.test(app.getEl("inMeta").textContent) && /字符/.test(app.getEl("outMeta").textContent));

  console.log("\n== 2. 非法 JSON 的位置信息 ==");
  app.setInput('{"a":1,}');
  app.click("btnPretty"); await app.settle();
  let st = app.status();
  ok("非法 JSON -> error 状态", st.kind === "error", st.kind);
  ok("错误文本含“第 N 行”", /第\s*\d+\s*行/.test(st.text), st.text.slice(0, 120));
  ok("错误文本含“第 N 列”", /第\s*\d+\s*列/.test(st.text));
  ok("错误文本含字符偏移", /字符偏移/.test(st.text));
  ok("错误文本含上下文片段", /上下文/.test(st.text));
  ok("非法 JSON 时不产出结果", app.output.value === "");
  ok("非法 JSON 后按钮恢复可用", !app.getEl("btnPretty").disabled);
  ok("非法 JSON 时选中出错字符", Array.isArray(app.input._sel) && app.input._sel[0] === 7, JSON.stringify(app.input._sel));

  // 位置精度：手工数出 `{"aaaa":1,}` 中多余的 `}` 位于偏移 10
  const t10 = '{"aaaa":1,}';
  app.setInput(t10);
  app.click("btnMinify"); await app.settle();
  {
    const m = /字符偏移[^0-9]*(\d+)/.exec(app.status().text.replace(/<[^>]*>/g, ""));
    ok("字符偏移与人工计数一致（应为 10）", m && Number(m[1]) === 10, "实测=" + (m && m[1]));
  }
  ok("注册了全局兜底错误处理", app.uncaught.length === 2, "handler 数=" + app.uncaught.length);

  // 多行：错误在第 3 行（"b" 后缺冒号）
  app.setInput('{\n  "a": 1,\n  "b" 2\n}');
  app.click("btnPretty"); await app.settle();
  ok("多行非法 JSON 定位到第 3 行", /第\s*3\s*行/.test(app.status().text), app.status().text.replace(/\n/g, " | ").slice(0, 160));

  // 第 2 行错误
  app.setInput('{\n  "a": 1\n  "b": 2\n}');
  app.click("btnPretty"); await app.settle();
  ok("缺逗号定位到第 3 行", /第\s*3\s*行/.test(app.status().text), app.status().text.replace(/\n/g, " | ").slice(0, 160));

  console.log("\n== 2b. 边界输入不得抛未捕获异常 ==");
  const cases = [
    ["空字符串", ""],
    ["仅空白", "   \n\t  "],
    ["仅换行", "\n\n\n"],
    ["未闭合字符串", '{"a":"abc}'],
    ["未闭合对象", '{"a":'],
    ["缺冒号", '{"a" 1}'],
    ["缺逗号", '{"a":1 "b":2}'],
    ["尾随内容", '{"a":1} xyz'],
    ["尾随逗号", "[1,2,]"],
    ["非法数字", '{"a":01}'],
    ["裸 token", "undefined"],
    ["单引号", "{'a':1}"],
    ["NaN", '{"a":NaN}'],
    ["Infinity", '{"a":Infinity}'],
    ["注释", '{"a":1 /*c*/}'],
    ["未转义控制字符", '{"a":"x\u0001y"}'],
    ["仅左括号", "["],
    ["仅右括号", "]"],
    ["孤立逗号", ","],
    ["孤立冒号", ":"],
    ["BOM + 合法", "\uFEFF{\"a\":1}"],
    ["合法纯量 true", "true"],
    ["合法纯量 数字", "42"],
    ["合法纯量 字符串", '"hi"'],
    ["合法 null", "null"],
    ["超深嵌套 3000 层", "[".repeat(3000) + "]".repeat(3000)],
    ["未闭合超深数组", "[".repeat(500) + "1"],
    ["超长单行字符串 200KB", '{"s":"' + "x".repeat(200000) + '"}'],
    ["大量重复键", "{" + Array.from({ length: 5000 }, (_, i) => '"k' + i + '":' + i).join(",") + "}"],
    ["代理对/emoji", '{"e":"😀🎉"}'],
    ["\\u0000 转义", '{"z":"\\u0000"}']
  ];
  for (const [name, text] of cases) {
    const inst = loadApp();
    let threw = null;
    try { inst.setInput(text); inst.click("btnPretty"); await inst.settle(); }
    catch (e) { threw = e; }
    const s = inst.status();
    const good = !threw && (s.kind === "error" || s.kind === "ok" || s.kind === "warn") && s.text.length > 0;
    ok("边界：" + name, good, threw ? String(threw.message) : "状态=" + s.kind);
    // 有值时再走一次压缩，确保两条路径都不炸
    if (!threw && s.kind !== "error") {
      try { inst.click("btnMinify"); await inst.settle(); } catch (e) { ok("边界：" + name + " 压缩路径", false, String(e.message)); continue; }
      ok("边界：" + name + " 压缩路径", true);
    }
  }
  // 未闭合超深数组必须给出行列
  {
    const inst = loadApp();
    inst.setInput("[".repeat(500) + "1");
    inst.click("btnMinify"); await inst.settle();
    ok("未闭合超深数组给出位置", inst.status().kind === "error" && /行/.test(inst.status().text), inst.status().text.slice(0, 120));
  }

  console.log("\n== 3. 大输入（>100KB）不卡死 ==");
  for (const kb of [100, 512, 1024, 2048]) {
    const arr = [];
    for (let i = 0; i < kb * 8; i++) { arr.push({ i: i, name: "item-" + i, ok: i % 2 === 0, v: i * 1.5 }); }
    const bigRaw = JSON.stringify(arr);
    const bytes = Buffer.byteLength(bigRaw, "utf8");
    const inst = loadApp();
    inst.setInput(bigRaw);
    const t0 = Date.now();
    let threw = null;
    try { inst.click("btnPretty"); await inst.settle(120000); } catch (e) { threw = e; }
    const ms = Date.now() - t0;
    ok("大输入 " + Math.round(bytes / 1024) + "KB 美化不抛异常", !threw, threw && threw.message);
    ok("大输入 " + Math.round(bytes / 1024) + "KB 美化输出正确", inst.output.value === JSON.stringify(arr, null, 2), "outLen=" + inst.output.value.length);
    console.log("        " + Math.round(bytes / 1024) + "KB 美化往返 ≈ " + ms + " ms");
  }
  {
    const arr = []; for (let i = 0; i < 20000; i++) { arr.push({ i, t: "中文文本-" + i }); }
    const prettyText = JSON.stringify(arr, null, 2);
    const inst = loadApp();
    inst.setInput(prettyText);
    let threw = null;
    try { inst.click("btnMinify"); await inst.settle(120000); } catch (e) { threw = e; }
    ok("20k 元素美化文本压缩不抛异常", !threw, threw && threw.message);
    ok("压缩大输入结果正确", inst.output.value === JSON.stringify(arr), "outLen=" + inst.output.value.length);
  }
  {
    // 5MB 以上：应给出“正在处理”提示但仍正常返回
    const arr = []; for (let i = 0; i < 60000; i++) { arr.push({ i, s: "填充填充填充填充填充填充填充填充" + i }); }
    const bigRaw = JSON.stringify(arr);
    const bytes = Buffer.byteLength(bigRaw, "utf8");
    const inst = loadApp();
    inst.setInput(bigRaw);
    let threw = null;
    try { inst.click("btnPretty"); await inst.settle(180000); } catch (e) { threw = e; }
    ok("超大输入 " + (bytes / 1048576).toFixed(1) + "MB 不抛异常", !threw, threw && threw.message);
    ok("超大输入有成功反馈", inst.status().kind === "ok", inst.status().kind + " :: " + inst.status().text.slice(0, 100));
    ok("超大输入结果正确", inst.output.value === JSON.stringify(arr, null, 2));
  }

  console.log("\n== 4. 复制（三条路径） ==");
  {
    const inst = loadApp();
    inst.click("btnClear"); await inst.settle();
    inst.click("btnCopy"); await sleep(30);
    ok("结果为空时复制 -> 警告而非崩溃", inst.status().kind === "warn", inst.status().kind);
    inst.setInput('{"a":1}'); inst.click("btnPretty"); await inst.settle();
    inst.click("btnCopy"); await sleep(50);
    ok("clipboard API 可用时 -> 成功状态", inst.status().kind === "ok", inst.status().text.slice(0, 80));
    ok("成功文案含字符数", /已复制\s*\d+\s*个字符/.test(inst.status().text), inst.status().text.slice(0, 80));
    ok("复制按钮有反馈文字变化", inst.getEl("btnCopy").textContent !== "复制结果", inst.getEl("btnCopy").textContent);
  }
  {
    const inst = loadApp({ clipboardOk: false });
    inst.setInput('{"a":1}'); inst.click("btnPretty"); await inst.settle();
    inst.click("btnCopy"); await sleep(80);
    ok("API 被拒 + execCommand 成功 -> ok", inst.status().kind === "ok", inst.status().text.slice(0, 80));
    ok("确实回退调用了 execCommand", inst.clipboardCalls.indexOf("exec") >= 0, JSON.stringify(inst.clipboardCalls));
  }
  {
    const inst = loadApp({ clipboardOk: false, execOk: false });
    inst.setInput('{"a":1}'); inst.click("btnPretty"); await inst.settle();
    inst.click("btnCopy"); await sleep(80);
    ok("两条复制路径都失败 -> warn 并全选", inst.status().kind === "warn" && /Ctrl\+C/.test(inst.status().text), inst.status().text.slice(0, 80));
    ok("失败时结果被全选", Array.isArray(inst.output._sel), JSON.stringify(inst.output._sel));
  }

  console.log("\n== 5. 其它交互状态 ==");
  {
    const inst = loadApp();
    inst.click("btnSample"); await inst.settle();
    ok("载入示例有反馈", inst.status().kind === "info" && inst.input.value.length > 0);
    ok("示例是合法 JSON", (() => { try { JSON.parse(inst.input.value); return true; } catch (e) { return false; } })());
    inst.click("btnPretty"); await inst.settle();
    const prettySample = inst.output.value;
    inst.click("btnSwap"); await sleep(10);
    ok("结果→输入 生效", inst.input.value === prettySample && inst.output.value === "");
    ok("交换后有反馈", inst.status().kind === "info", inst.status().kind);
    inst.click("btnClear"); await sleep(10);
    ok("清空生效", inst.input.value === "" && inst.output.value === "");
    ok("清空后统计归零", inst.getEl("s-out").textContent === "0");
    inst.setInput('{"a":1}'); await sleep(10);
    ok("输入事件给出反馈", inst.status().kind === "info" && /已输入\s*7\s*字符/.test(inst.status().text), inst.status().text);
    inst.click("btnEsc"); await sleep(10);
    ok("转义为字符串可用", inst.output.value === JSON.stringify(JSON.stringify({ a: 1 })), inst.output.value);
    inst.click("btnClear"); await sleep(10);
    inst.click("btnEsc"); await sleep(10);
    ok("空输入转义 -> 警告不崩溃", inst.status().kind === "warn", inst.status().kind);
    inst.click("btnSwap"); await sleep(10);
    ok("空结果交换 -> 警告不崩溃", inst.status().kind === "warn", inst.status().kind);
  }

  console.log("\n== 6. 重复操作稳定性（同一实例连跑 50 次） ==");
  {
    const inst = loadApp();
    let threw = null;
    try {
      for (let i = 0; i < 50; i++) {
        const v = (i % 3 === 0) ? '{"a":' + i + '}' : '{"a":' + i + ',}';
        inst.setInput(v);
        inst.click("btnPretty"); await inst.settle();
        if (i % 3 === 0 && inst.status().kind !== "ok") { throw new Error("第 " + i + " 轮应成功"); }
        if (i % 3 !== 0 && inst.status().kind !== "error") { throw new Error("第 " + i + " 轮应报错"); }
        if (inst.getEl("btnPretty").disabled) { throw new Error("第 " + i + " 轮后按钮未恢复"); }
      }
    } catch (e) { threw = e; }
    ok("连续 50 次成功/失败交替无异常、按钮状态正确", !threw, threw && threw.message);
  }

  console.log("\n================ 结果 ================");
  console.log("PASS = " + pass + " , FAIL = " + fail);
  if (failures.length) {
    console.log("失败项：");
    failures.forEach(f => console.log("  - " + f));
    process.exit(1);
  }
  process.exit(0);
})().catch(e => {
  console.error("自检脚本自身异常：" + (e && e.stack || e));
  process.exit(2);
});
