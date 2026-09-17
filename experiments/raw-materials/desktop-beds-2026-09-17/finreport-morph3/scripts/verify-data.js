const fs = require("fs");
const path = "C:/Users/<username>/Desktop/MyProject/js/data.js";
const code = fs.readFileSync(path, "utf8");
const ctx = {};
// Execute as if in a browser-ish global
const fn = new Function("window", "globalThis", code + "\n;return window.FinanceData || globalThis.FinanceData;");
const FinanceData = fn(ctx, ctx);
const d = FinanceData;
console.log("months", d.months.length);
console.log("totalIncome", d.summary.totalIncome);
console.log("totalExpense", d.summary.totalExpense);
console.log("totalNet", d.summary.totalNet);
console.log("savingsRate", d.summary.savingsRate);
console.log("avgIncome", d.summary.avgIncome);
console.log("avgExpense", d.summary.avgExpense);
d.months.forEach(function (m) {
  console.log(m.label, "in", m.totalIncome, "out", m.totalExpense, "net", m.net);
  const si = Object.values(m.income).reduce(function (a, b) { return a + b; }, 0);
  const se = Object.values(m.expense).reduce(function (a, b) { return a + b; }, 0);
  if (si !== m.totalIncome || se !== m.totalExpense) {
    console.error("MISMATCH", m.label, si, m.totalIncome, se, m.totalExpense);
    process.exitCode = 1;
  }
});
// year totals from monthly
const yIn = d.months.reduce(function (a, m) { return a + m.totalIncome; }, 0);
const yOut = d.months.reduce(function (a, m) { return a + m.totalExpense; }, 0);
if (yIn !== d.summary.totalIncome || yOut !== d.summary.totalExpense) {
  console.error("YEAR MISMATCH", yIn, yOut, d.summary.totalIncome, d.summary.totalExpense);
  process.exitCode = 1;
}
console.log("expense category totals", d.summary.expenseByCategory);
console.log("income category totals", d.summary.incomeByCategory);
console.log(process.exitCode ? "FAIL" : "OK");
