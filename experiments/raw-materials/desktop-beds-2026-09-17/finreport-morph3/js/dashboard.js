/**
 * 仪表盘 — 全部数字与图形来自 window.FinanceData（js/data.js）
 * 纯原生 Canvas 手绘，无外部依赖。
 */
(function () {
  "use strict";

  var D = window.FinanceData;
  if (!D) {
    console.error("FinanceData 未加载：请确认已引入 js/data.js");
    return;
  }

  var COLORS = {
    income: "#0f766e",
    expense: "#c2410c",
    net: "#0369a1",
    grid: "#d9e0dc",
    axis: "#5c6b64",
    ink: "#1c2420",
    muted: "#5c6b64",
    pie: [
      "#0f766e", "#c2410c", "#0369a1", "#b45309",
      "#7c3aed", "#be123c", "#0e7490", "#4d7c0f",
      "#a16207", "#64748b"
    ]
  };

  function money(n) {
    return "¥" + D.formatMoney(n);
  }

  /* ---------- KPI ---------- */
  function renderKpis() {
    document.getElementById("kpi-income").textContent = money(D.summary.totalIncome);
    document.getElementById("kpi-expense").textContent = money(D.summary.totalExpense);
    document.getElementById("kpi-net").textContent = money(D.summary.totalNet);
    document.getElementById("kpi-rate").textContent = D.summary.savingsRate.toFixed(2) + "%";
  }

  /* ---------- Canvas 工具 ---------- */
  function setupCanvas(canvas) {
    var dpr = window.devicePixelRatio || 1;
    var cssW = canvas.clientWidth || canvas.width;
    var cssH = parseInt(canvas.getAttribute("height"), 10) || canvas.height;
    canvas.width = Math.round(cssW * dpr);
    canvas.height = Math.round(cssH * dpr);
    canvas.style.height = cssH + "px";
    var ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);
    return { ctx: ctx, w: cssW, h: cssH };
  }

  function drawGrid(ctx, x0, y0, w, h, rows) {
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 1;
    for (var i = 0; i <= rows; i++) {
      var y = y0 + (h * i) / rows;
      ctx.beginPath();
      ctx.moveTo(x0, y);
      ctx.lineTo(x0 + w, y);
      ctx.stroke();
    }
  }

  function drawYTicks(ctx, x0, y0, h, maxVal, formatter) {
    ctx.fillStyle = COLORS.muted;
    ctx.font = "11px sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    var steps = 4;
    for (var i = 0; i <= steps; i++) {
      var val = maxVal * (1 - i / steps);
      var y = y0 + (h * i) / steps;
      ctx.fillText(formatter(val), x0 - 8, y);
    }
  }

  function niceMax(v) {
    if (v <= 0) return 100;
    var mag = Math.pow(10, Math.floor(Math.log(v) / Math.LN10));
    var norm = v / mag;
    var nice;
    if (norm <= 1) nice = 1;
    else if (norm <= 2) nice = 2;
    else if (norm <= 2.5) nice = 2.5;
    else if (norm <= 5) nice = 5;
    else nice = 10;
    return nice * mag;
  }

  function shortMoney(n) {
    if (Math.abs(n) >= 10000) {
      return (Math.round((n / 10000) * 100) / 100) + "万";
    }
    return String(Math.round(n));
  }

  /* ---------- 柱状图：月度收支对比 ---------- */
  function drawBarChart() {
    var canvas = document.getElementById("chart-bar");
    if (!canvas) return;
    var s = setupCanvas(canvas);
    var ctx = s.ctx, W = s.w, H = s.h;

    var padL = 56, padR = 16, padT = 16, padB = 36;
    var plotW = W - padL - padR;
    var plotH = H - padT - padB;

    var months = D.months;
    var maxVal = 0;
    months.forEach(function (m) {
      if (m.totalIncome > maxVal) maxVal = m.totalIncome;
      if (m.totalExpense > maxVal) maxVal = m.totalExpense;
    });
    var yMax = niceMax(maxVal * 1.05);

    drawGrid(ctx, padL, padT, plotW, plotH, 4);
    drawYTicks(ctx, padL, padT, plotH, yMax, shortMoney);

    var groupW = plotW / months.length;
    var barW = Math.max(6, groupW * 0.32);
    var gap = Math.max(2, groupW * 0.06);

    months.forEach(function (m, i) {
      var cx = padL + groupW * i + groupW / 2;
      var hInc = (m.totalIncome / yMax) * plotH;
      var hExp = (m.totalExpense / yMax) * plotH;
      var xInc = cx - barW - gap / 2;
      var xExp = cx + gap / 2;

      ctx.fillStyle = COLORS.income;
      ctx.fillRect(xInc, padT + plotH - hInc, barW, hInc);
      ctx.fillStyle = COLORS.expense;
      ctx.fillRect(xExp, padT + plotH - hExp, barW, hExp);

      ctx.fillStyle = COLORS.muted;
      ctx.font = "11px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillText(m.shortLabel, cx, padT + plotH + 8);
    });

    // 基线
    ctx.strokeStyle = COLORS.axis;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padL, padT + plotH);
    ctx.lineTo(padL + plotW, padT + plotH);
    ctx.stroke();
  }

  /* ---------- 折线图：月度净结余 ---------- */
  function drawNetChart() {
    var canvas = document.getElementById("chart-net");
    if (!canvas) return;
    var s = setupCanvas(canvas);
    var ctx = s.ctx, W = s.w, H = s.h;

    var padL = 56, padR = 16, padT = 16, padB = 36;
    var plotW = W - padL - padR;
    var plotH = H - padT - padB;

    var months = D.months;
    var minVal = Infinity, maxVal = -Infinity;
    months.forEach(function (m) {
      if (m.net < minVal) minVal = m.net;
      if (m.net > maxVal) maxVal = m.net;
    });
    // 留出上下边距
    var span = maxVal - minVal || 1;
    var yMin = minVal - span * 0.15;
    var yMax = maxVal + span * 0.15;

    // 网格 + Y 轴
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 1;
    ctx.fillStyle = COLORS.muted;
    ctx.font = "11px sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    var steps = 4;
    for (var i = 0; i <= steps; i++) {
      var val = yMax - ((yMax - yMin) * i) / steps;
      var y = padT + (plotH * i) / steps;
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(padL + plotW, y);
      ctx.stroke();
      ctx.fillText(shortMoney(val), padL - 8, y);
    }

    function px(i) {
      return padL + (plotW * (i + 0.5)) / months.length;
    }
    function py(v) {
      return padT + plotH - ((v - yMin) / (yMax - yMin)) * plotH;
    }

    // 面积填充
    ctx.beginPath();
    ctx.moveTo(px(0), py(months[0].net));
    for (var j = 1; j < months.length; j++) {
      ctx.lineTo(px(j), py(months[j].net));
    }
    ctx.lineTo(px(months.length - 1), padT + plotH);
    ctx.lineTo(px(0), padT + plotH);
    ctx.closePath();
    ctx.fillStyle = "rgba(3, 105, 161, 0.12)";
    ctx.fill();

    // 折线
    ctx.beginPath();
    ctx.moveTo(px(0), py(months[0].net));
    for (var k = 1; k < months.length; k++) {
      ctx.lineTo(px(k), py(months[k].net));
    }
    ctx.strokeStyle = COLORS.net;
    ctx.lineWidth = 2;
    ctx.stroke();

    // 数据点
    months.forEach(function (m, idx) {
      ctx.beginPath();
      ctx.arc(px(idx), py(m.net), 3.5, 0, Math.PI * 2);
      ctx.fillStyle = COLORS.net;
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.fillStyle = COLORS.muted;
      ctx.font = "11px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillText(m.shortLabel, px(idx), padT + plotH + 8);
    });

    // 基线
    ctx.strokeStyle = COLORS.axis;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padL, padT + plotH);
    ctx.lineTo(padL + plotW, padT + plotH);
    ctx.stroke();
  }

  /* ---------- 环形图：全年支出构成 ---------- */
  function drawPieChart() {
    var canvas = document.getElementById("chart-pie");
    if (!canvas) return;
    var s = setupCanvas(canvas);
    var ctx = s.ctx, W = s.w, H = s.h;

    var cats = D.expenseCategories;
    var byCat = D.summary.expenseByCategory;
    var total = D.summary.totalExpense;
    if (!total) return;

    // 按金额降序，便于阅读
    var items = cats.map(function (c, i) {
      return { name: c, value: byCat[c] || 0, color: COLORS.pie[i % COLORS.pie.length] };
    }).filter(function (it) {
      return it.value > 0;
    }).sort(function (a, b) {
      return b.value - a.value;
    });

    var cx = Math.min(W * 0.28, 220);
    var cy = H / 2;
    var outerR = Math.min(cx - 30, cy - 30, 130);
    var innerR = outerR * 0.58;

    var start = -Math.PI / 2;
    items.forEach(function (it) {
      var slice = (it.value / total) * Math.PI * 2;
      var end = start + slice;

      ctx.beginPath();
      ctx.arc(cx, cy, outerR, start, end);
      ctx.arc(cx, cy, innerR, end, start, true);
      ctx.closePath();
      ctx.fillStyle = it.color;
      ctx.fill();

      start = end;
    });

    // 中心文字
    ctx.fillStyle = COLORS.ink;
    ctx.font = "600 14px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("全年支出", cx, cy - 12);
    ctx.font = "700 15px sans-serif";
    ctx.fillText(money(total), cx, cy + 12);

    // 右侧图例列表
    var listX = cx + outerR + 48;
    if (listX > W - 140) listX = Math.max(cx + outerR + 20, W * 0.55);
    var rowH = Math.min(26, (H - 30) / Math.max(items.length, 1));
    var listY0 = (H - rowH * items.length) / 2 + rowH / 2;

    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    items.forEach(function (it, i) {
      var y = listY0 + i * rowH;
      ctx.fillStyle = it.color;
      ctx.fillRect(listX, y - 6, 12, 12);
      ctx.fillStyle = COLORS.ink;
      ctx.font = "12px sans-serif";
      var pct = ((it.value / total) * 100).toFixed(1);
      ctx.fillText(it.name + "  " + money(it.value) + "（" + pct + "%）", listX + 18, y);
    });

    // HTML 图例（无障碍/小屏备用）
    var legend = document.getElementById("pie-legend");
    if (legend) {
      legend.innerHTML = items.map(function (it) {
        var pct = ((it.value / total) * 100).toFixed(1);
        return '<span><i style="background:' + it.color + '"></i>' +
          it.name + " " + pct + "%</span>";
      }).join("");
    }
  }

  /* ---------- 初始化 ---------- */
  function renderAll() {
    renderKpis();
    drawBarChart();
    drawNetChart();
    drawPieChart();
  }

  renderAll();

  var resizeTimer = null;
  window.addEventListener("resize", function () {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(renderAll, 150);
  });
})();
