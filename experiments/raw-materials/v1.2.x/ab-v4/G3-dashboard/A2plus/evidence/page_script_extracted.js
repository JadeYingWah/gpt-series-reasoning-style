
"use strict";
/* 12 个月销售数据（万元，演示用虚构数值） */
var MONTHS = [
  { m:"1月",  v:128 }, { m:"2月",  v:96 },  { m:"3月",  v:145 },
  { m:"4月",  v:132 }, { m:"5月",  v:158 }, { m:"6月",  v:176 },
  { m:"7月",  v:143 }, { m:"8月",  v:151 }, { m:"9月",  v:189 },
  { m:"10月", v:205 }, { m:"11月", v:234 }, { m:"12月", v:218 }
];
var SCOPES = {
  all: { label:"全年",     idx:[0,1,2,3,4,5,6,7,8,9,10,11] },
  q1:  { label:"第一季度", idx:[0,1,2] },
  q2:  { label:"第二季度", idx:[3,4,5] },
  q3:  { label:"第三季度", idx:[6,7,8] },
  q4:  { label:"第四季度", idx:[9,10,11] }
};

function computeMetrics(rows){
  var total = 0, peak = rows[0], i;
  for (i = 0; i < rows.length; i++){
    total += rows[i].v;
    if (rows[i].v > peak.v){ peak = rows[i]; }
  }
  return { count: rows.length, total: total, avg: total / rows.length,
           peakMonth: peak.m, peakValue: peak.v };
}
function fmtInt(n){ return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ","); }
function fmtAvg(n){ return (Math.round(n * 10) / 10).toFixed(1); }

function setCard(id, main, unit){
  var node = document.getElementById(id);
  node.textContent = "";
  node.appendChild(document.createTextNode(main));
  var s = document.createElement("small");
  s.textContent = unit;
  node.appendChild(s);
}

function buildChart(rows, scopeLabel){
  var W = 640, H = 320, L = 52, R = 16, T = 30, B = 42;
  var pw = W - L - R, ph = H - T - B;
  var vmax = 0, pv = 0, i;
  for (i = 0; i < rows.length; i++){
    if (rows[i].v > vmax){ vmax = rows[i].v; pv = rows[i].v; }
  }
  var ymax = Math.ceil(vmax / 50) * 50;
  var band = pw / rows.length;
  var barW = Math.min(Math.round(band * 0.55), 72);

  var NS = "http://www.w3.org/2000/svg";
  var svg = document.createElementNS(NS, "svg");
  svg.setAttribute("width", W);
  svg.setAttribute("height", H);
  svg.setAttribute("viewBox", "0 0 " + W + " " + H);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", scopeLabel + "月度销售额柱状图");

  function txt(x, y, s, anchor, cls){
    var t = document.createElementNS(NS, "text");
    t.setAttribute("x", x); t.setAttribute("y", y);
    t.setAttribute("text-anchor", anchor || "middle");
    t.setAttribute("class", cls);
    t.textContent = s;
    return t;
  }
  function gridLine(y){
    var l = document.createElementNS(NS, "line");
    l.setAttribute("x1", L); l.setAttribute("y1", y);
    l.setAttribute("x2", L + pw); l.setAttribute("y2", y);
    l.setAttribute("class", "grid");
    return l;
  }
  var steps = 5;
  for (i = 0; i <= steps; i++){
    var yv = ymax / steps * i;
    var y = T + ph - (ph * yv / ymax);
    svg.appendChild(gridLine(y));
    svg.appendChild(txt(L - 8, y + 4, String(yv), "end", "tick"));
  }
  for (i = 0; i < rows.length; i++){
    var r = rows[i];
    var bh = ph * r.v / ymax;
    var x = L + band * i + (band - barW) / 2;
    var y2 = T + ph - bh;
    var rect = document.createElementNS(NS, "rect");
    rect.setAttribute("x", x); rect.setAttribute("y", y2);
    rect.setAttribute("width", barW); rect.setAttribute("height", bh);
    rect.setAttribute("rx", 3);
    rect.setAttribute("class", r.v === pv ? "bar bar-peak" : "bar");
    rect.setAttribute("data-v", r.v);
    svg.appendChild(rect);
    svg.appendChild(txt(x + barW / 2, y2 - 6, String(r.v), "middle", "val"));
    svg.appendChild(txt(L + band * i + band / 2, T + ph + 18, r.m, "middle", "mlabel"));
  }
  var chart = document.getElementById("chart");
  chart.textContent = "";
  chart.appendChild(svg);
}

function render(scopeKey){
  var sc = SCOPES[scopeKey];
  var rows = sc.idx.map(function(i){ return MONTHS[i]; });
  var mt = computeMetrics(rows);
  setCard("kpi-total", fmtInt(mt.total), " 万元");
  setCard("kpi-avg", fmtAvg(mt.avg), " 万元/月");
  setCard("kpi-peak", mt.peakMonth, mt.peakValue + " 万元");
  document.getElementById("chart-title").textContent = "月度销售额趋势（" + sc.label + "）";
  buildChart(rows, sc.label);
  var btns = document.querySelectorAll(".filters button");
  for (var i = 0; i < btns.length; i++){
    var on = btns[i].getAttribute("data-scope") === scopeKey;
    if (on){ btns[i].classList.add("active"); } else { btns[i].classList.remove("active"); }
    btns[i].setAttribute("aria-pressed", on ? "true" : "false");
  }
}
function setScope(k){ if (SCOPES[k]){ render(k); } }

(function init(){
  var btns = document.querySelectorAll(".filters button");
  for (var i = 0; i < btns.length; i++){
    (function(b){
      b.addEventListener("click", function(){ setScope(b.getAttribute("data-scope")); });
    })(btns[i]);
  }
  var initial = "all";
  try {
    var sp = new URLSearchParams(location.search);
    var s = sp.get("scope");
    if (s && SCOPES[s]){ initial = s; }
  } catch (e) { /* 不支持 URLSearchParams 时回退全年视图 */ }
  render(initial);
})();
