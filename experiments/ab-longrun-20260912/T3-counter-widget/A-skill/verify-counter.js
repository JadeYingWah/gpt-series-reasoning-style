/**
 * Offline verification for counter.html logic.
 * Mocks a minimal DOM + localStorage, loads the page script, runs acceptance checks.
 * Exit 0 = all checks passed; non-zero = failures printed.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const HTML_PATH = path.join(__dirname, "counter.html");
const html = fs.readFileSync(HTML_PATH, "utf8");

// Extract inline <script> content (the last script block).
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/i);
if (!scriptMatch) {
  console.error("FAIL: no inline <script> found in counter.html");
  process.exit(1);
}
const pageScript = scriptMatch[1];

// --- minimal DOM mock ---
function createEl(id, tag) {
  const listeners = {};
  const el = {
    id,
    tagName: (tag || "div").toUpperCase(),
    textContent: "",
    value: "",
    disabled: false,
    title: "",
    className: "",
    _classes: new Set(),
    classList: {
      add(c) { el._classes.add(c); el.className = [...el._classes].join(" "); },
      remove(c) { el._classes.delete(c); el.className = [...el._classes].join(" "); },
      toggle(c, force) {
        const on = force === undefined ? !el._classes.has(c) : !!force;
        if (on) el._classes.add(c); else el._classes.delete(c);
        el.className = [...el._classes].join(" ");
        return on;
      },
      contains(c) { return el._classes.has(c); }
    },
    addEventListener(type, fn) {
      (listeners[type] = listeners[type] || []).push(fn);
    },
    click() {
      // Simulate disabled button: browser does not fire click on disabled.
      if (el.disabled) return;
      (listeners.click || []).forEach(fn => fn({ type: "click", target: el }));
    },
    dispatch(type) {
      (listeners[type] || []).forEach(fn => fn({ type, target: el }));
    }
  };
  return el;
}

const store = new Map();
const localStorageMock = {
  getItem(k) { return store.has(k) ? store.get(k) : null; },
  setItem(k, v) { store.set(k, String(v)); },
  removeItem(k) { store.delete(k); },
  clear() { store.clear(); }
};

const elements = {
  value: createEl("value", "div"),
  status: createEl("status", "div"),
  step: createEl("step", "input"),
  "step-error": createEl("step-error", "div"),
  "btn-plus": createEl("btn-plus", "button"),
  "btn-minus": createEl("btn-minus", "button"),
  "btn-reset": createEl("btn-reset", "button")
};

const documentMock = {
  getElementById(id) {
    if (!elements[id]) throw new Error("unknown element: " + id);
    return elements[id];
  }
};

// Minimal window + setTimeout
const windowMock = {};
const sandbox = {
  window: windowMock,
  document: documentMock,
  localStorage: localStorageMock,
  setTimeout: (fn) => { /* skip animation timers in tests */ },
  clearTimeout: () => {},
  console
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

let failed = 0;
let passed = 0;
function check(name, cond, detail) {
  if (cond) {
    passed++;
    console.log("PASS  " + name);
  } else {
    failed++;
    console.log("FAIL  " + name + (detail ? " — " + detail : ""));
  }
}

// Run page script
try {
  vm.runInContext(pageScript, sandbox, { filename: "counter-inline.js" });
} catch (e) {
  console.error("FAIL: page script threw:", e);
  process.exit(1);
}

const api = windowMock.__counterTest;
check("script bootstraps without throw", true);
check("exposes __counterTest helpers", !!api && typeof api.parseStep === "function");

// --- acceptance checks ---
const btnPlus = elements["btn-plus"];
const btnMinus = elements["btn-minus"];
const btnReset = elements["btn-reset"];
const elValue = elements.value;
const elStatus = elements.status;
const elStep = elements.step;
const elStepError = elements["step-error"];

// 1. Initial display is 0
check("initial value displays 0", elValue.textContent === "0", "got " + elValue.textContent);

// 2. +1 with default step
btnPlus.click();
check("+1 → 1", elValue.textContent === "1", "got " + elValue.textContent);

// 3. −1
btnMinus.click();
check("−1 → 0", elValue.textContent === "0", "got " + elValue.textContent);

// 4. Reset from non-zero
btnPlus.click();
btnPlus.click();
btnPlus.click();
check("three +1 → 3", elValue.textContent === "3");
btnReset.click();
check("reset → 0", elValue.textContent === "0");

// 5. Step input applies
elStep.value = "5";
elStep.dispatch("input");
check("step set to 5 accepted", elStepError.textContent === "" && !elStep.classList.contains("invalid"));
btnPlus.click();
check("step 5 + → 5", elValue.textContent === "5", "got " + elValue.textContent);
btnMinus.click();
check("step 5 − → 0", elValue.textContent === "0");

// 6. Step validation: reject non-positive-integer
elStep.value = "0";
elStep.dispatch("input");
check("step 0 rejected", elStepError.textContent.length > 0 && elStep.classList.contains("invalid"));
check("step 0 keeps previous behavior (step still 5)", api.getState().step === 5, "step=" + api.getState().step);

elStep.value = "-3";
elStep.dispatch("input");
check("step -3 rejected", elStepError.textContent.length > 0);

elStep.value = "2.5";
elStep.dispatch("input");
check("step 2.5 rejected", elStepError.textContent.length > 0);

elStep.value = "abc";
elStep.dispatch("input");
check("step abc rejected", elStepError.textContent.length > 0);

elStep.value = "3";
elStep.dispatch("input");
check("step 3 accepted", elStepError.textContent === "" && api.getState().step === 3);

// 7. Upper bound 99
btnReset.click();
elStep.value = "1";
elStep.dispatch("input");
// Fast-forward: set value near bound via many clicks is slow; use step tricks
// Jump to 98 with step, then 1, then check disabled.
// Current step=1, value=0. Use step 50 twice → 100 clamped? Better: step 99 once → 99.
elStep.value = "99";
elStep.dispatch("input");
btnPlus.click();
check("step 99 from 0 → 99", elValue.textContent === "99", "got " + elValue.textContent);
check("+ disabled at 99", btnPlus.disabled === true);
check("status warns at max", /上限/.test(elStatus.textContent), "status=" + elStatus.textContent);
check("value has at-max class", elValue.classList.contains("at-max"));
btnPlus.click(); // should be no-op because disabled
check("disabled + does not change value", elValue.textContent === "99");

// From 99, step 1, minus should work
elStep.value = "1";
elStep.dispatch("input");
check("+ re-enabled when step allows room? value=99 step=1 → still at max", btnPlus.disabled === true);
btnMinus.click();
check("− from 99 → 98", elValue.textContent === "98", "got " + elValue.textContent);
check("+ enabled at 98", btnPlus.disabled === false);

// 8. Lower bound -99
btnReset.click();
elStep.value = "99";
elStep.dispatch("input");
btnMinus.click();
check("step 99 − from 0 → −99", elValue.textContent === "-99", "got " + elValue.textContent);
check("− disabled at −99", btnMinus.disabled === true);
check("status warns at min", /下限/.test(elStatus.textContent));
check("value has at-min class", elValue.classList.contains("at-min"));
btnMinus.click();
check("disabled − does not change value", elValue.textContent === "-99");

// 9. Step larger than remaining room disables button (not partial apply)
btnReset.click();
elStep.value = "50";
elStep.dispatch("input");
btnPlus.click(); // 50
btnPlus.click(); // 100 → would exceed; should disable not fire
check("step 50 → 50", elValue.textContent === "50");
// canAdd: 50+50=100 > 99 → disabled
check("step 50 at 50: + disabled (no partial jump)", btnPlus.disabled === true);
btnPlus.click();
check("no partial apply when disabled", elValue.textContent === "50");

// 10. localStorage persistence
const key = api.STORAGE_KEY;
check("storage key is counter-widget.v1", key === "counter-widget.v1", "key=" + key);
const savedRaw = localStorageMock.getItem(key);
check("localStorage has payload", !!savedRaw, "raw=" + savedRaw);
const saved = JSON.parse(savedRaw);
check("saved value matches UI", saved.value === 50, JSON.stringify(saved));
check("saved step matches UI", saved.step === 50);

// 11. Reload simulation: new context with same storage
const store2 = new Map(store); // copy persisted state
const sandbox2 = {
  window: {},
  document: documentMock,
  localStorage: {
    getItem: k => store2.has(k) ? store2.get(k) : null,
    setItem: (k, v) => store2.set(k, String(v)),
    removeItem: k => store2.delete(k),
    clear: () => store2.clear()
  },
  setTimeout: () => {},
  clearTimeout: () => {},
  console
};
vm.createContext(sandbox2);
// Reset DOM text so we observe re-render
elValue.textContent = "";
btnPlus.disabled = false;
btnMinus.disabled = false;
try {
  vm.runInContext(pageScript, sandbox2, { filename: "counter-inline-reload.js" });
  check("reload restores value 50", elValue.textContent === "50", "got " + elValue.textContent);
  check("reload restores step 50", elStep.value === "50");
  check("reload keeps + disabled at 50+50>99", btnPlus.disabled === true);
} catch (e) {
  check("reload restores value 50", false, String(e));
}

// 12. Corrupt storage falls back to 0/1
store2.set(key, "{not json");
const sandbox3 = {
  window: {},
  document: documentMock,
  localStorage: {
    getItem: k => store2.get(k) ?? null,
    setItem: (k, v) => store2.set(k, String(v)),
    removeItem: k => store2.delete(k),
    clear: () => store2.clear()
  },
  setTimeout: () => {},
  clearTimeout: () => {},
  console
};
elValue.textContent = "";
elStep.value = "";
vm.createContext(sandbox3);
vm.runInContext(pageScript, sandbox3, { filename: "counter-inline-corrupt.js" });
check("corrupt storage → value 0", elValue.textContent === "0", "got " + elValue.textContent);
check("corrupt storage → step 1", elStep.value === "1");

// 13. parseStep unit checks
check("parseStep('1') ok", api.parseStep("1").ok === true && api.parseStep("1").step === 1);
check("parseStep('  7 ') ok", api.parseStep("  7 ").ok === true && api.parseStep("  7 ").step === 7);
check("parseStep('') fail", api.parseStep("").ok === false);
check("parseStep('0') fail", api.parseStep("0").ok === false);
check("parseStep('-1') fail", api.parseStep("-1").ok === false);
check("parseStep('100') fail", api.parseStep("100").ok === false);
check("parseStep('99') ok", api.parseStep("99").ok === true);

// 14. No CDN / framework markers
const banned = ["http://", "https://", "cdn.", "jquery", "react", "vue", "bootstrap"];
const lower = html.toLowerCase();
// Allow none — page must not load external assets
const hasExternal = /<(script|link)[^>]+src=["']https?:/i.test(html) || /<link[^>]+href=["']https?:/i.test(html);
check("no external script/link resources", !hasExternal);

console.log("\n===== " + passed + " passed, " + failed + " failed =====");
process.exit(failed > 0 ? 1 : 0);
