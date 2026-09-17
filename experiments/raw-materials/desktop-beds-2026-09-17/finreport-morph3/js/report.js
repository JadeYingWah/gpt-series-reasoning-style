/**
 * 月度报告 — 全部数字与分析段落来自 window.FinanceData（js/data.js）
 */
(function () {
  "use strict";

  var D = window.FinanceData;
  if (!D) {
    console.error("FinanceData 未加载：请确认已引入 js/data.js");
    return;
  }

  function money(n) {
    return "¥" + D.formatMoney(n);
  }

  function pct(n) {
    return (Math.round(n * 100) / 100).toFixed(2) + "%";
  }

  /* ---------- KPI ---------- */
  function renderKpis() {
    document.getElementById("kpi-income").textContent = money(D.summary.totalIncome);
    document.getElementById("kpi-expense").textContent = money(D.summary.totalExpense);
    document.getElementById("kpi-net").textContent = money(D.summary.totalNet);
    document.getElementById("kpi-rate").textContent = pct(D.summary.savingsRate);
  }

  /* ---------- 12 个月汇总表 ---------- */
  function renderMonthsTable() {
    var tbody = document.querySelector("#table-months tbody");
    var tfoot = document.querySelector("#table-months tfoot");
    if (!tbody || !tfoot) return;

    var rowsHtml = D.months.map(function (m) {
      var netClass = m.net >= 0 ? "num-pos" : "num-neg";
      return (
        "<tr>" +
        "<td>" + m.label + "</td>" +
        "<td>" + money(m.totalIncome) + "</td>" +
        "<td>" + money(m.totalExpense) + "</td>" +
        '<td class="' + netClass + '">' + money(m.net) + "</td>" +
        "</tr>"
      );
    }).join("");
    tbody.innerHTML = rowsHtml;

    var netClass = D.summary.totalNet >= 0 ? "num-pos" : "num-neg";
    tfoot.innerHTML =
      "<tr>" +
      "<td>合计</td>" +
      "<td>" + money(D.summary.totalIncome) + "</td>" +
      "<td>" + money(D.summary.totalExpense) + "</td>" +
      '<td class="' + netClass + '">' + money(D.summary.totalNet) + "</td>" +
      "</tr>";
  }

  /* ---------- 支出分类合计表 ---------- */
  function renderCategoryTable() {
    var tbody = document.querySelector("#table-cats tbody");
    var tfoot = document.querySelector("#table-cats tfoot");
    if (!tbody || !tfoot) return;

    var total = D.summary.totalExpense;
    var items = D.expenseCategories.map(function (c) {
      return { name: c, value: D.summary.expenseByCategory[c] || 0 };
    }).sort(function (a, b) {
      return b.value - a.value;
    });

    tbody.innerHTML = items.map(function (it) {
      var share = total ? (it.value / total) * 100 : 0;
      return (
        "<tr>" +
        "<td>" + it.name + "</td>" +
        "<td>" + money(it.value) + "</td>" +
        "<td>" + pct(share) + "</td>" +
        "</tr>"
      );
    }).join("");

    tfoot.innerHTML =
      "<tr>" +
      "<td>合计</td>" +
      "<td>" + money(total) + "</td>" +
      "<td>" + pct(100) + "</td>" +
      "</tr>";
  }

  /* ---------- 文字分析（≥3 段，全部由数据推导） ---------- */
  function buildAnalysis() {
    var s = D.summary;
    var months = D.months;

    // 1. 整体财务状况
    var p1 =
      "<strong>整体财务状况：</strong>" +
      s.year + " 年全年总收入 <strong>" + money(s.totalIncome) + "</strong>，" +
      "总支出 <strong>" + money(s.totalExpense) + "</strong>，" +
      "净结余 <strong>" + money(s.totalNet) + "</strong>，" +
      "储蓄率 <strong>" + pct(s.savingsRate) + "</strong>。" +
      "月均收入 " + money(s.avgIncome) + "，月均支出 " + money(s.avgExpense) + "，" +
      "月均结余 " + money(s.avgNet) + "。" +
      (s.totalNet > 0
        ? "全年为正结余，收支结构整体可持续。"
        : "全年为负结余，支出超过收入，需要收紧开支。");

    // 2. 高峰/低谷月
    var maxInc = months[0], minInc = months[0];
    var maxExp = months[0], minExp = months[0];
    var maxNet = months[0], minNet = months[0];
    months.forEach(function (m) {
      if (m.totalIncome > maxInc.totalIncome) maxInc = m;
      if (m.totalIncome < minInc.totalIncome) minInc = m;
      if (m.totalExpense > maxExp.totalExpense) maxExp = m;
      if (m.totalExpense < minExp.totalExpense) minExp = m;
      if (m.net > maxNet.net) maxNet = m;
      if (m.net < minNet.net) minNet = m;
    });
    var p2 =
      "<strong>高峰与低谷月：</strong>" +
      "收入最高的月份是 <strong>" + maxInc.label + "</strong>（" + money(maxInc.totalIncome) + "），" +
      "最低是 " + minInc.label + "（" + money(minInc.totalIncome) + "）。" +
      "支出峰值出现在 <strong>" + maxExp.label + "</strong>（" + money(maxExp.totalExpense) + "），" +
      "谷值在 " + minExp.label + "（" + money(minExp.totalExpense) + "）。" +
      "结余最好的月份为 " + maxNet.label + "（" + money(maxNet.net) + "），" +
      "最吃紧的是 " + minNet.label + "（" + money(minNet.net) + "）。" +
      "收入峰谷差 " + money(maxInc.totalIncome - minInc.totalIncome) + "，" +
      "支出峰谷差 " + money(maxExp.totalExpense - minExp.totalExpense) + "。";

    // 3. 主要开支观察
    var cats = D.expenseCategories.map(function (c) {
      return { name: c, value: s.expenseByCategory[c] || 0 };
    }).filter(function (x) {
      return x.value > 0;
    }).sort(function (a, b) {
      return b.value - a.value;
    });
    var top1 = cats[0];
    var top3 = cats.slice(0, 3);
    var top3Sum = top3.reduce(function (acc, x) { return acc + x.value; }, 0);
    var top3Share = s.totalExpense ? (top3Sum / s.totalExpense) * 100 : 0;
    var p3 =
      "<strong>主要开支观察：</strong>" +
      "支出最大的类别是 <strong>" + top1.name + "</strong>，" +
      "全年 " + money(top1.value) + "，占总支出 " +
      pct(s.totalExpense ? (top1.value / s.totalExpense) * 100 : 0) + "。" +
      "前三类别（" + top3.map(function (x) { return x.name; }).join("、") + "）" +
      "合计 " + money(top3Sum) + "，占总支出 " + pct(top3Share) + "，" +
      "开支集中度较高" + (top3Share >= 60 ? "，优化这三项即可显著改善结余。" : "，但仍有分散空间。");

    // 4. 收入结构（附加第 4 段，仍由数据推导）
    var incCats = D.incomeCategories.map(function (c) {
      return { name: c, value: s.incomeByCategory[c] || 0 };
    }).filter(function (x) {
      return x.value > 0;
    }).sort(function (a, b) {
      return b.value - a.value;
    });
    var mainInc = incCats[0];
    var sideIncSum = incCats.slice(1).reduce(function (acc, x) { return acc + x.value; }, 0);
    var p4 =
      "<strong>收入结构：</strong>" +
      "最主要收入来源为 <strong>" + mainInc.name + "</strong>，" +
      "全年 " + money(mainInc.value) + "，占总收入 " +
      pct(s.totalIncome ? (mainInc.value / s.totalIncome) * 100 : 0) + "。" +
      "其余来源合计 " + money(sideIncSum) + "，占 " +
      pct(s.totalIncome ? (sideIncSum / s.totalIncome) * 100 : 0) + "。" +
      "月均收入 " + money(s.avgIncome) + "，月均支出 " + money(s.avgExpense) + "，" +
      "平均每月可留存 " + money(s.avgNet) + "（储蓄率 " + pct(s.savingsRate) + "）。";

    return [p1, p2, p3, p4];
  }

  function renderAnalysis() {
    var el = document.getElementById("analysis-body");
    if (!el) return;
    el.innerHTML = buildAnalysis()
      .map(function (p) { return "<p>" + p + "</p>"; })
      .join("");
  }

  /* ---------- 初始化 ---------- */
  renderKpis();
  renderMonthsTable();
  renderCategoryTable();
  renderAnalysis();
})();
