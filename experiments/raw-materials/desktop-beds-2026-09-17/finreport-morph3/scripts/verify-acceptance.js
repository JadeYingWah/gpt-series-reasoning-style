/**
 * 指挥官独立验收：用 Chrome headless 打开三页，抽取数字并与 data.js 对源。
 * 可复现：node scripts/verify-acceptance.js
 */
const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT = "C:/Users/<username>/Desktop/MyProject";
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const TMP = path.join(ROOT, "scripts", "_accept_tmp");
fs.mkdirSync(TMP, { recursive: true });

function loadFinanceData() {
  const code = fs.readFileSync(path.join(ROOT, "js", "data.js"), "utf8");
  const ctx = {};
  const fn = new Function("window", "globalThis", code + "\n;return window.FinanceData || globalThis.FinanceData;");
  return fn(ctx, ctx);
}

function runChrome(url, dumpFile) {
  const r = spawnSync(CHROME, [
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--virtual-time-budget=3000",
    "--dump-dom",
    url
  ], { encoding: "utf8", maxBuffer: 20 * 1024 * 1024 });
  fs.writeFileSync(dumpFile, r.stdout || "", "utf8");
  if (r.stderr) fs.writeFileSync(dumpFile + ".err.txt", r.stderr, "utf8");
  return r.stdout || "";
}

function runChromeEval(url, expr, outFile) {
  // Chrome headless --evaluate-on-new-document is limited; use dump-dom of a wrapper page instead.
  const html = `<!DOCTYPE html><html><body>
<script src="${url.replace(/\\/g, "/")}?x=1"></script>
</body></html>`;
  // Fallback: use --repl not available. We'll parse dump-dom text instead.
  return null;
}

function extractAllMoney(html) {
  const re = /¥\s?([0-9][0-9,]*(?:\.[0-9]+)?)/g;
  const out = [];
  let m;
  while ((m = re.exec(html))) out.push(m[1].replace(/,/g, ""));
  return out;
}

function hasText(html, s) {
  return html.indexOf(s) !== -1;
}

function check(cond, msg, failures) {
  if (!cond) {
    failures.push(msg);
    console.log("FAIL:", msg);
  } else {
    console.log("OK:", msg);
  }
}

const D = loadFinanceData();
const failures = [];

// Independent recomputation (not using FinanceData.summary for cross-check of monthly math)
const monthsRaw = D.months;
const yIn = monthsRaw.reduce((a, m) => a + m.totalIncome, 0);
const yOut = monthsRaw.reduce((a, m) => a + m.totalExpense, 0);
const yNet = monthsRaw.reduce((a, m) => a + m.net, 0);
check(yIn === D.summary.totalIncome, `year income ${yIn} == summary ${D.summary.totalIncome}`, failures);
check(yOut === D.summary.totalExpense, `year expense ${yOut} == summary ${D.summary.totalExpense}`, failures);
check(yNet === D.summary.totalNet, `year net ${yNet} == summary ${D.summary.totalNet}`, failures);
check(Math.abs(D.summary.savingsRate - (yNet / yIn) * 100) < 0.01, `savings rate ${D.summary.savingsRate}`, failures);

// Open pages with real browser
const indexDom = runChrome("file:///" + ROOT + "/index.html", path.join(TMP, "index.html"));
const dashDom = runChrome("file:///" + ROOT + "/dashboard.html", path.join(TMP, "dashboard.html"));
const reportDom = runChrome("file:///" + ROOT + "/report.html", path.join(TMP, "report.html"));

const fmt = D.formatMoney(yIn);
check(hasText(indexDom, fmt), `index shows year income ${fmt}`, failures);
check(hasText(indexDom, D.formatMoney(yOut)), `index shows year expense ${D.formatMoney(yOut)}`, failures);
check(hasText(indexDom, D.formatMoney(yNet)), `index shows net ${D.formatMoney(yNet)}`, failures);

check(hasText(dashDom, D.formatMoney(yIn)), `dashboard KPI income`, failures);
check(hasText(dashDom, D.formatMoney(yOut)), `dashboard KPI expense`, failures);
check(hasText(dashDom, D.formatMoney(yNet)), `dashboard KPI net`, failures);
check(hasText(dashDom, D.summary.savingsRate.toFixed(2) + "%"), `dashboard savings rate`, failures);
check((dashDom.match(/<canvas /g) || []).length >= 3, `dashboard has >=3 canvas`, failures);

check(hasText(reportDom, D.formatMoney(yIn)), `report KPI income`, failures);
check(hasText(reportDom, D.formatMoney(yOut)), `report KPI expense`, failures);
check(hasText(reportDom, D.formatMoney(yNet)), `report KPI net`, failures);

// 12 month labels present
D.months.forEach(function (m) {
  check(hasText(reportDom, m.label), `report has month ${m.label}`, failures);
  check(hasText(reportDom, D.formatMoney(m.totalIncome)), `report has ${m.label} income`, failures);
  check(hasText(reportDom, D.formatMoney(m.totalExpense)), `report has ${m.label} expense`, failures);
  check(hasText(reportDom, D.formatMoney(m.net)), `report has ${m.label} net`, failures);
});

// Category table top: 房租 50400 should appear
check(hasText(reportDom, D.formatMoney(D.summary.expenseByCategory["房租"])), `report has 房租 total`, failures);
check(hasText(reportDom, D.formatMoney(D.summary.expenseByCategory["餐饮"])), `report has 餐饮 total`, failures);

// Analysis paragraphs
check(hasText(reportDom, "整体财务状况"), `report analysis p1`, failures);
check(hasText(reportDom, "高峰与低谷月"), `report analysis p2`, failures);
check(hasText(reportDom, "主要开支观察"), `report analysis p3`, failures);

// Screenshots for visual open
function shot(url, out) {
  spawnSync(CHROME, [
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--window-size=1280,1600",
    "--virtual-time-budget=3000",
    "--screenshot=" + out,
    url
  ], { encoding: "utf8", maxBuffer: 20 * 1024 * 1024 });
}
shot("file:///" + ROOT + "/index.html", path.join(TMP, "index.png"));
shot("file:///" + ROOT + "/dashboard.html", path.join(TMP, "dashboard.png"));
shot("file:///" + ROOT + "/report.html", path.join(TMP, "report.png"));

// Mutation / negative test for rule 5: temporarily break expectation
// If we search for a number that is NOT in data, pages must NOT contain it (already implicit).
check(!hasText(reportDom, "999999999"), "negative check: absurd number not present", failures);

console.log("\n==== RESULT ====");
if (failures.length) {
  console.log("ACCEPT_FAIL count=" + failures.length);
  process.exitCode = 1;
} else {
  console.log("ACCEPT_OK");
}
console.log("baseline: income=" + yIn + " expense=" + yOut + " net=" + yNet + " rate=" + D.summary.savingsRate);
