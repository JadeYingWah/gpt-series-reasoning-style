# -*- coding: utf-8 -*-
"""
05 报告生成：读取 data/ 下全部产物, 生成 report.html
规范: wb-finance-skill html-report-style —— 浅底深字研报风 / 首屏结论先行 / 红涨绿跌 /
      ECharts 骨架填数 / 表格服务端生成 / 内联 JS 交付前 node --check 自检。
"""
import csv
import json
import math
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

UP = "#c0392b"    # 涨-红 (A股口径)
DOWN = "#1e8449"  # 跌-绿


def load_json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def pct(x, digits=2, sign=True):
    s = f"{x*100:.{digits}f}%"
    if sign and x > 0:
        s = "+" + s
    return s


def num(x, digits=2):
    return f"{x:,.{digits}f}"


def main():
    meta = load_json("fetch_meta.json")
    ind = load_json("indicators_latest.json")
    fc = load_json("forecast.json")
    bt = load_json("backtest_results.json")

    # ---------- K线数据 (最近180根) ----------
    with open(os.path.join(DATA, "600519_indicators.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in r:
            if k != "date" and r[k] != "":
                r[k] = float(r[k])
    N = 180
    kl = rows[-N:]
    # MA30 未入指标CSV, 由全量收盘序列补算
    closes_all = [r["close"] for r in rows]
    ma30_all = [round(sum(closes_all[i - 29:i + 1]) / 30, 2) if i >= 29 else None
                for i in range(len(closes_all))]
    dates = [r["date"] for r in kl]
    ohlc = [[r["open"], r["close"], r["low"], r["high"]] for r in kl]
    vol_objs = [{"value": r["volume"],
                 "itemStyle": {"color": UP if r["close"] >= r["open"] else DOWN}} for r in kl]
    ma10 = [round(r["MA10"], 2) for r in kl]
    ma30 = ma30_all[-N:]
    ma60 = [round(r["MA60"], 2) for r in kl]
    dif = [round(r["DIF"], 3) for r in kl]
    dea = [round(r["DEA"], 3) for r in kl]
    hist_objs = [{"value": round(r["MACD"], 3),
                  "itemStyle": {"color": UP if r["MACD"] >= 0 else DOWN}} for r in kl]
    r6 = [round(r["RSI6"], 2) for r in kl]
    r12 = [round(r["RSI12"], 2) for r in kl]

    # ---------- 长期走势 ----------
    def fnum(r, key, digits=2):
        v = r.get(key)
        if v in ("", None):
            return None
        return round(float(v), digits)

    all_dates = [r["date"] for r in rows]
    all_close = [round(r["close"], 2) for r in rows]
    ma20_all = [fnum(r, "MA20") for r in rows]
    ma60_all = [fnum(r, "MA60") for r in rows]
    ma250_all = [fnum(r, "MA250") for r in rows]

    # ---------- 预测扇形: 最近60根 + 未来20个交易日 ----------
    H = 60
    h_dates = dates[-H:] if len(dates) >= H else dates
    h_close = all_close[-H:]
    fc_cats = h_dates + [f"T+{i}" for i in range(1, 21)]
    s0 = fc["s0"]
    q = fc["M2_gbm_quantiles"]
    pad = [None] * (len(h_dates) - 1)
    p5 = pad + [s0] + [round(q[str(h)]["P5"], 1) for h in (5, 10, 20)]
    p95 = pad + [s0] + [round(q[str(h)]["P95"], 1) for h in (5, 10, 20)]
    p25 = pad + [s0] + [round(q[str(h)]["P25"], 1) for h in (5, 10, 20)]
    p75 = pad + [s0] + [round(q[str(h)]["P75"], 1) for h in (5, 10, 20)]
    p50 = pad + [s0] + [round(q[str(h)]["P50"], 1) for h in (5, 10, 20)]
    p5band = [round(b - a, 1) if (a is not None and b is not None) else None
              for a, b in zip(p5, p95)]
    p75band = [round(b - a, 1) if (a is not None and b is not None) else None
               for a, b in zip(p25, p75)]
    fc_line = [None] * len(h_dates) + [round(q[str(h)]["P50"], 1) for h in (5, 10, 20)]
    m1 = fc["M1_linear60_point"]["20"]
    m3 = fc["M3_linear250_point"]["20"]

    # ---------- 回测净值 ----------
    with open(os.path.join(DATA, "600519_backtest_equity.csv"), encoding="utf-8") as f:
        eq = list(csv.DictReader(f))
    bt_dates = [r["date"] for r in eq]
    bt_s = [round(float(r["nav_strategy"]), 4) for r in eq]
    bt_bh = [round(float(r["nav_buyhold"]), 4) for r in eq]
    bt_la = [round(float(r["nav_lookahead"]), 4) for r in eq]
    def dd_series(nav):
        peak, out = -1e9, []
        for v in nav:
            peak = max(peak, v)
            out.append(round(v / peak - 1, 4))
        return out
    bt_dds = dd_series(bt_s)
    bt_ddbh = dd_series(bt_bh)

    m_ok, m_la, m_bh = bt["correct_next_open"], bt["lookahead_same_open"], bt["buy_and_hold"]

    # ---------- 关键指标快照表 ----------
    il = ind["indicators_latest"]
    ws = {c["name"]: c for c in ind["cross_check_vs_westock"]}
    def row(label, key, digits=2, note=""):
        v = il.get(key)
        w = ws.get(key)
        if w:
            badge = f'<span class="ok">✔ 一致(差{w["abs_diff"]})</span>'
            ref = num(w["westock"], digits)
        elif key.startswith("RSI"):
            badge = '<span class="diff">口径分歧*</span>'
            ref = {"RSI6": "21.90", "RSI12": "34.97", "RSI24": "43.80"}.get(key, "—")
        else:
            badge = '<span class="na">无独立锚点</span>'
            ref = "—"
        return f"<tr><td>{label}</td><td class='num'>{num(v, digits) if v is not None else '—'}</td><td class='num'>{ref}</td><td>{badge} {note}</td></tr>"

    close_now = ind["close"]
    tbl_ind = "".join([
        f"<tr><td>收盘价</td><td class='num'>{num(close_now)}</td><td class='num'>1,258.00</td>"
        f"<td><span class='ok'>✔ 一致(差0)</span></td></tr>",
        row("MA5", "MA5"), row("MA10", "MA10"), row("MA20", "MA20"),
        row("MA60", "MA60"), row("MA120", "MA120"), row("MA250", "MA250"),
        row("BOLL上轨", "BOLL_UPPER"), row("BOLL中轨", "BOLL_MID"), row("BOLL下轨", "BOLL_LOWER"),
        row("MACD DIF", "DIF", 3), row("MACD DEA", "DEA", 3), row("MACD柱", "MACD", 3),
        row("KDJ K", "KDJ_K"), row("KDJ D", "KDJ_D"), row("KDJ J", "KDJ_J"),
        row("RSI6 (Wilder)", "RSI6"), row("RSI12 (Wilder)", "RSI12"), row("RSI24 (Wilder)", "RSI24"),
        row("ADX14", "ADX14"), row("+DI14", "PDI"), row("-DI14", "MDI"),
        row("ATR14", "ATR14"), row("量比(对5日均量)", "VOL_RATIO", 3),
    ])

    # ---------- 回测指标表 ----------
    def bt_row(label, a, b, c, digits=2, fmt="pct"):
        def f(x):
            if x is None:
                return "—"
            if fmt == "pct":
                return pct(x, digits)
            if fmt == "num":
                return num(x, digits)
            return f"{x:.2f}"
        return f"<tr><td>{label}</td><td class='num'>{f(a)}</td><td class='num'>{f(b)}</td><td class='num'>{f(c)}</td></tr>"

    tbl_bt = "".join([
        bt_row("总收益", m_ok["total_return"], m_la["total_return"], m_bh["total_return"]),
        bt_row("年化收益 CAGR", m_ok["cagr"], m_la["cagr"], m_bh["cagr"]),
        bt_row("年化波动率", m_ok["annual_vol"], m_la["annual_vol"], m_bh["annual_vol"]),
        bt_row("夏普比率 (rf=0)", m_ok["sharpe_rf0"], m_la["sharpe_rf0"], m_bh["sharpe_rf0"], fmt="raw3"),
        bt_row("最大回撤", m_ok["max_drawdown"], m_la["max_drawdown"], m_bh["max_drawdown"]),
        bt_row("Calmar", m_ok["calmar"], m_la["calmar"], m_bh["calmar"], fmt="raw3"),
        bt_row("完整买卖回合数", m_ok["round_trips"], m_la["round_trips"], None, fmt="num"),
        bt_row("回合胜率", m_ok["win_rate"], m_la["win_rate"], None, fmt="pct"),
    ])

    # ---------- 预测分位表 ----------
    def fc_row(h):
        d = q[str(h)]
        return (f"<tr><td>T+{h}个交易日</td><td class='num'>{num(d['P5'],0)}</td>"
                f"<td class='num'>{num(d['P25'],0)}</td><td class='num'>{num(d['P50'],0)}</td>"
                f"<td class='num'>{num(d['P75'],0)}</td><td class='num'>{num(d['P95'],0)}</td>"
                f"<td class='num'>{pct(d['P_down'],1)}</td></tr>")
    tbl_fc = fc_row(5) + fc_row(10) + fc_row(20)

    # ---------- 数据溯源表 ----------
    cc = meta["cross_check_detail"]
    n_ok = sum(1 for x in cc if x["status"] == "一致")
    tbl_prov = (
        f"<tr><td>日K线 OHLCV(前复权/不复权)</td><td>腾讯行情接口 web.ifzq.gtimg.cn</td>"
        f"<td>{meta['date_start']} ~ {meta['date_end']}（{meta['rows_qfq']}根）</td>"
        f"<td>取数 {meta['fetch_time']}</td></tr>"
        f"<tr><td>K线交叉校验</td><td>westock-data（经 agentic_search）</td>"
        f"<td>最近10根逐字段核对</td><td>{n_ok}/10 完全一致（误差=0）</td></tr>"
        f"<tr><td>技术指标交叉校验</td><td>westock-data technical（经 agentic_search）</td>"
        f"<td>2026-09-16 截面15项</td><td>15/15 一致（≤0.0004）</td></tr>"
        f"<tr><td>基本面/资金流/机构预期</td><td>westock / neodata（经 agentic_search）</td>"
        f"<td>2026-09-16</td><td>二手平台数据，研报观点<span class='warn'>需核实原文</span></td></tr>"
        f"<tr><td>回测关键数字</td><td>本机两套独立实现对账</td>"
        f"<td>向量化 vs 逐bar账本</td><td>相对误差 1.6e-15，通过</td></tr>"
        f"<tr><td>预测带宽可信度</td><td>滚动起源检验（20个起源）</td>"
        f"<td>P5~P95 / P25~P75 覆盖率</td><td>90%（期望90%）/ 60%（期望50%）</td></tr>"
    )

    # ---------- TL;DR 关键数字 ----------
    close_now = ind["close"]
    ytd = None
    for i, d in enumerate(all_dates):
        if d >= "2025-12-31":
            ytd = close_now / all_close[i] - 1
            break
    hi52 = max(all_close[-244:])
    lo52 = min(all_close[-244:])
    dd_from_hi = close_now / hi52 - 1
    sigma_ann = fc["model_params"]["sigma_annualized_250d"]

    tldr = f"""
    <div class="cards">
      <div class="card"><div class="k">最新收盘 <span class="src">2026-09-16</span></div><div class="v">{num(close_now)} 元</div><div class="s">{pct(-0.0116)} 当日 · 52周 {num(lo52,0)}~{num(hi52,0)}</div></div>
      <div class="card"><div class="k">年初至今</div><div class="v down">{pct(ytd)}</div><div class="s">距52周高点 {pct(dd_from_hi)}</div></div>
      <div class="card"><div class="k">PE(TTM) / 股息率</div><div class="v">19.31× / 4.14%</div><div class="s">westock 2026-09-16</div></div>
      <div class="card"><div class="k">年化波动率(250d)</div><div class="v">{pct(sigma_ann,1)}</div><div class="s">GBM σ 估计</div></div>
      <div class="card"><div class="k">双均线回测(正确口径)</div><div class="v down">{pct(m_ok['total_return'])}</div><div class="s">买入持有 {pct(m_bh['total_return'])}</div></div>
      <div class="card"><div class="k">20日 P5~P95 区间</div><div class="v">{num(q["20"]['P5'],0)}~{num(q["20"]['P95'],0)}</div><div class="s">P(下跌) {pct(q["20"]['P_down'],1)}</div></div>
    </div>"""

    # ---------- 载荷 ----------
    payload = {
        "kline": {"dates": dates, "ohlc": ohlc, "vol": vol_objs, "ma10": ma10, "ma30": ma30,
                  "ma60": ma60, "dif": dif, "dea": dea, "hist": hist_objs, "r6": r6, "r12": r12},
        "trend": {"dates": all_dates, "close": all_close, "ma20": ma20_all,
                  "ma60": ma60_all, "ma250": ma250_all},
        "fan": {"cats": fc_cats, "close": h_close, "p5": p5, "p5band": p5band,
                "p25": p25, "p75band": p75band, "p95": p95, "p50": p50, "p50line": fc_line},
        "bt": {"dates": bt_dates, "s": bt_s, "bh": bt_bh, "la": bt_la,
               "dds": bt_dds, "ddbh": bt_ddbh},
    }
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    html = TEMPLATE
    for k, v in {
        "__PAYLOAD__": payload_json,
        "__TLDR__": tldr,
        "__TBL_IND__": tbl_ind,
        "__TBL_BT__": tbl_bt,
        "__TBL_FC__": tbl_fc,
        "__TBL_PROV__": tbl_prov,
        "__ASOF__": ind["as_of"],
        "__FETCH__": meta["fetch_time"],
        "__M1__": num(m1, 0), "__M3__": num(m3, 0),
        "__PDOWN__": pct(q["20"]["P_down"], 1),
        "__COV90__": str(fc["rolling_origin_check"]["coverage_P5_P95"]),
        "__COV50__": str(fc["rolling_origin_check"]["coverage_P25_P75"]),
        "__NORIGIN__": str(fc["rolling_origin_check"]["n_origins"]),
        "__LOOKAHEAD__": pct(bt["lookahead_inflation"]["total_return_diff"], 1),
        "__YTD__": pct(ytd),
    }.items():
        html = html.replace(k, v)

    out = os.path.join(BASE, "report.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] {out}  ({len(html)//1024} KB)")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>贵州茅台（600519.SH）量化分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
:root{--bg:#f7f8fa;--panel:#ffffff;--ink:#1f2937;--muted:#6b7280;--line:#e5e7eb;
      --red:#c0392b;--green:#1e8449;--blue:#1f4e79;--accent:#1f4e79;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--ink);font:15px/1.75 "Microsoft YaHei","PingFang SC",sans-serif;padding-bottom:60px;}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px;}
header{background:linear-gradient(135deg,#1f4e79 0%,#2d6da3 100%);color:#fff;padding:36px 0 30px;margin-bottom:24px;}
header h1{font-size:26px;font-weight:700;letter-spacing:.5px;}
header .sub{margin-top:8px;font-size:13px;opacity:.85;}
.badge{display:inline-block;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.35);
       border-radius:4px;padding:1px 10px;margin-right:8px;font-size:12px;}
h2{font-size:19px;color:var(--accent);border-left:4px solid var(--accent);padding-left:10px;margin:34px 0 14px;}
h3{font-size:16px;margin:18px 0 8px;}
p{margin:8px 0;}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:18px 20px;margin:14px 0;
       box-shadow:0 1px 3px rgba(0,0,0,.04);}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:16px 0;}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px 16px;}
.card .k{font-size:12px;color:var(--muted);}
.card .v{font-size:22px;font-weight:700;margin:4px 0;color:var(--ink);}
.card .v.down{color:var(--green);}
.card .v.up{color:var(--red);}
.card .s{font-size:11px;color:var(--muted);}
.card .src{font-weight:400;font-size:11px;}
table{width:100%;border-collapse:collapse;font-size:13px;margin:10px 0;background:#fff;}
th{background:#eef2f7;color:var(--ink);font-weight:600;text-align:left;}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);}
td.num{font-variant-numeric:tabular-nums;text-align:right;}
tr:hover td{background:#fafbfd;}
.ok{color:var(--green);font-size:12px;}
.warn{color:#b45309;font-size:12px;}
.diff{color:#b45309;font-size:12px;}
.na{color:var(--muted);font-size:12px;}
.up{color:var(--red);} .down{color:var(--green);}
.chart{width:100%;height:420px;}
.chart-tall{width:100%;height:560px;}
.note{background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:10px 14px;font-size:13px;color:#92400e;margin:10px 0;}
.risk{background:#fef2f2;border:1px solid #fecaca;border-radius:6px;padding:10px 14px;font-size:13px;color:#991b1b;margin:10px 0;}
ul{margin:6px 0 6px 22px;}
li{margin:4px 0;}
.src-tag{font-size:11px;color:var(--muted);background:#f3f4f6;border-radius:3px;padding:1px 6px;margin-left:6px;}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);font-size:12px;color:var(--muted);}
.disclaimer{background:#f3f4f6;border:1px solid var(--line);border-radius:6px;padding:12px 16px;font-size:12px;color:#4b5563;margin-top:14px;}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
@media(max-width:800px){.grid2{grid-template-columns:1fr;}}
.step{border-left:3px solid var(--accent);padding:2px 0 2px 14px;margin:12px 0;}
.step .t{font-weight:700;color:var(--accent);}
.tag{display:inline-block;font-size:11px;border-radius:3px;padding:1px 8px;margin-right:6px;}
.tag.sell{background:#fdecea;color:var(--red);border:1px solid #f5c6c2;}
.tag.buy{background:#e8f6ee;color:var(--green);border:1px solid #bfe5cd;}
.tag.wait{background:#fff7e6;color:#b45309;border:1px solid #fde8c2;}
</style>
</head>
<body>
<header><div class="wrap">
  <h1>贵州茅台（600519.SH）量化分析报告</h1>
  <div class="sub">
    <span class="badge">数据截至 __ASOF__ 收盘</span>
    <span class="badge">取数时间 __FETCH__</span>
    <span class="badge">数据源：腾讯行情接口 + 独立双源交叉校验</span>
    <span class="badge">分析标的由任务默认指定，未含用户个股偏好</span>
  </div>
</div></header>

<div class="wrap">

__TLDR__

<div class="panel">
<h3 style="margin-top:0">结论摘要（先看这里）</h3>
<ul>
  <li><b>位置：</b>股价 __YTD__（年初至今），收于全部均线（MA5/10/20/60/120/250）下方、贴近布林下轨，RSI6 处超卖区、KDJ J 值为负——<b>下跌趋势中的超卖状态，技术性反弹需求存在，但趋势尚未反转</b>（趋势维投票 1多/2空，ADX14 显示弱趋势）。</li>
  <li><b>回测警示：</b>经典 MA10/30 双均线策略 2020 年以来总收益 <b class="down">-18.4%</b>，跑输买入持有（+44.5%），31 个回合胜率仅 29%——<b>茅台近年宽幅震荡市对简单趋势跟随策略不友好</b>，不应直接实盘套用。</li>
  <li><b>前视偏差对照：</b>同一策略若误用"信号日开盘成交"（用了收盘后才知道的信号），收益虚增 <b class="up">__LOOKAHEAD__</b>——本报告回测已按"次日开盘成交+双边成本"的保守口径执行。</li>
  <li><b>预测口径：</b>GBM 蒙特卡洛显示未来 20 个交易日 P5~P95 区间宽达 ±10%，P(下跌) __PDOWN__；60日线性外推（__M1__ 元）与250日外推（__M3__ 元）方向相反——<b>短期方向本质不可精确预测，区间与应对比点估计重要</b>。带宽经 __NORIGIN__ 个滚动起源检验，P5~P95 覆盖率 __COV90__%（期望90%）。</li>
  <li><b>基本盘（第三方数据）：</b>PE(TTM) 19.31×、股息率 4.14% 处历史偏低区，但 2026H1 归母净利同比 -1.95%（2015年来首次半年报下滑）、主力资金近20日净流出21.6亿——<b>估值底与业绩/资金拐点未共振</b>。</li>
</ul>
</div>

<h2>一、数据获取与多源交叉校验</h2>
<div class="panel">
<p>本报告全部行情数据由脚本从<b>腾讯公开行情接口</b>拉取（2020-01-02 ~ __ASOF__，前复权 1,627 根日线），并执行了三层自动校验：</p>
<table>
<tr><th>数据项</th><th>来源</th><th>范围/样本</th><th>校验结果</th></tr>
__TBL_PROV__
</table>
<p class="note">⚠ 口径披露：RSI 使用标准 Wilder/通达信口径（公式：SMA(max(ΔC,0),N,1)/SMA(|ΔC|,N,1)×100）。已探测 8 种平滑变体均无法对齐 westock 的 RSI 值（差 3.9~13.3 且随周期增大），判定为对方私有口径；双方定性结论一致（RSI6 均在 30 以下超卖区），不影响信号方向。详见 <code>data/indicators_latest.json</code>。</p>
</div>

<h2>二、技术指标与三维信号投票</h2>
<div class="panel">
<p>按"趋势维（EMA/ADX）→ 均值回归维（BOLL/RSI）→ 量价维（OBV/量比）"三维框架汇总，信号优先级：趋势方向 &gt; 关键位置 &gt; 短期信号。<span class="src-tag">截面：__ASOF__ 收盘 1,258.00 元</span></p>
<div class="grid2">
<div>
<table>
<tr><th>指标</th><th>本报告</th><th>独立源参考</th><th>校验</th></tr>
__TBL_IND__
</table>
</div>
<div>
<h3>三维投票结果</h3>
<table>
<tr><th>维度</th><th>信号</th></tr>
<tr><td>趋势维</td><td><b>偏空（1多/2空）</b>：收盘&lt;MA20、收盘&lt;MA60、MA20&lt;MA60；ADX14≈15 弱趋势，-DI&gt;+DI</td></tr>
<tr><td>均值回归维</td><td><b>超卖</b>：RSI6≈18(&lt;30)、KDJ J≈-3.9(&lt;0)、%B≈0.02（贴近下轨）——存在技术性反弹需求，但"超卖可钝化，不等于必反弹"</td></tr>
<tr><td>量价维</td><td><b>中性偏弱</b>：量比 1.19（无明显放量承接），OBV 20日斜率向下（资金参与度回落）</td></tr>
</table>
<p class="risk">信号解读纪律：单一指标信号 ≠ 必然成立；周期错配时优先长周期；极限值往往预示反弹而非趋势加速，需多系统交叉确认。</p>
</div>
</div>
<div id="kline" class="chart-tall"></div>
<p style="font-size:12px;color:var(--muted)">图1：日K线+MA10/30/60+成交量+MACD(12,26,9)+RSI6/12（最近180个交易日，可缩放）。红涨绿跌。</p>
</div>

<h2>三、趋势预测模型（概率情景推演）</h2>
<div class="panel">
<p><b>方法与定位：</b>四个模型并行——M1 60日对数线性回归外推、M2 GBM蒙特卡洛（250日 μ/σ 估计，10,000路径，固定种子 20260916）、M3 250日长周期回归外推、M4 零漂移随机游走对照。<b>输出为概率区间而非点预测</b>；M1（看多至 __M1__）与 M3（看平至 __M3__）方向相反，正说明短期方向对起点窗口高度敏感。</p>
<table>
<tr><th>到期点</th><th>P5</th><th>P25</th><th>P50</th><th>P75</th><th>P95</th><th>P(低于现价)</th></tr>
__TBL_FC__
</table>
<p style="font-size:13px;color:var(--muted)">基准价 1,258 元；μ/σ 由最近250交易日对数收益估计（年化 σ≈22.2%）。M4 随机游走对照的 P50 与 M2 几乎重合而区间略窄，说明漂移项贡献有限——<b>当前预测的不确定性主要来自波动而非方向</b>。</p>
<div id="fan" class="chart"></div>
<p style="font-size:12px;color:var(--muted)">图2：未来20个交易日 GBM 分位扇形（深带 P25~P75，浅带 P5~P95，中虚线 P50）。横轴 T+n 为交易日序。</p>
<p class="note">✔ 模型自检（滚动起源检验）：以 2024-01 以来每月末为起源、用当时可见数据重新估计参数并预测20日，共 __NORIGIN__ 个起源：真实值落入 P5~P95 带 __COV90__%（期望90%）、落入 P25~P75 带 __COV50__%（期望50%）——<b>区间标定诚实，无系统性过窄</b>。这检验的是"带宽可信度"，不构成对未来方向的保证。</p>
</div>

<h2>四、回测验证（含前视偏差负对照）</h2>
<div class="panel">
<p><b>策略：</b>MA10/MA30 双均线金叉买/死叉卖，全仓进出，只做多。<b>成本口径（保守）：</b>佣金 0.025% 双边 + 印花税 0.05% 卖出 + 滑点 0.1% 双边。<b>执行纪律：</b>信号次日开盘成交（无前视）。</p>
<table>
<tr><th>指标</th><th>① 正确版（次日开盘）</th><th>② 负对照（前视偏差）</th><th>③ 买入持有</th></tr>
__TBL_BT__
</table>
<div class="risk">
<b>负对照说明（为什么有第②列）：</b>若误用"信号当日开盘成交"，等于用当日收盘才能算出的信号指导当日开盘交易——同一策略总收益从 -18.4% 变 +31.2%，<b>虚增 __LOOKAHEAD__</b>。把要防的错误故意做一次、看指标是否"变红"，是验证回测管线本身是否可信的必要环节。
</div>
<p><b>诚实结论：</b>①双均线策略在此标的此区间<b>跑输买入持有约 63 个百分点</b>，主因 2021-2024 宽幅下跌+震荡中反复金叉死叉被磨损（胜率 29%，最大回撤 -59.0%）；②策略波动率（21.4%）低于买入持有（30.5%），说明"趋势跟随降波动"在这只票上成立、但代价是收益被成本与假信号吞噬；③<span style="color:#1e8449">关键数字经两套独立实现（向量化 × 逐bar账本）对账，相对误差 1.6e-15</span>。</p>
<div id="btchart" style="width:100%;height:520px;"></div>
<p style="font-size:12px;color:var(--muted)">图3：回测净值对比（对数刻度）与回撤（下副图）。绿色=买入持有，蓝色=正确口径双均线，灰色虚线=前视偏差负对照。</p>
</div>

<h2>五、交易策略建议（研究参考）</h2>
<div class="panel">
<p><b>前提显式：</b>以下建议基于——①标的：贵州茅台（600519.SH）；②环境假设：白酒行业磨底、大盘中性；③适配对象：可承受 ±10% 波动、期限 3-6 个月、分仓操作的中长线投资者。<b>不适合短线交易者与无法承受继续下跌的仓位。</b></p>

<div class="step"><div class="t">① 当前交易位置</div>
<p><span class="tag sell">下跌反抽观察区</span> 收盘价位于全部均线下方、贴近布林下轨，RSI6/KDJ 超卖但趋势未反转；量比 1.19 无放量承接，OBV 下行。对照 trade-plan 位置表属"下跌反抽"——<b>反抽可参与度低，右侧确认前不重仓</b>。</p></div>

<div class="step"><div class="t">② 入场逻辑与触发条件（宁可等确认）</div>
<p><span class="tag wait">等待右侧确认</span>满足<b>全部三条</b>再考虑首仓：a) 收盘站回 MA20 且 MA10 走平上拐；b) MACD 绿柱连续 3 日收窄或金叉；c) 反弹日量比 ≥1.5（放量承接）。单日超卖反抽（如 J 值修复）不作为入场依据。</p></div>

<div class="step"><div class="t">③ 分仓路径</div>
<p>首仓（试错仓）≤20%；站回 MA60 且缩量回踩不破再加 20-30%（确认仓）；有效突破布林中轨 1,294 且主力资金转净流入再评估加仓。任何单一步骤亏损触及止损线即终止升级，<b>不摊平、不补仓</b>。</p></div>

<div class="step"><div class="t">④ 止盈止损（写完即纪律）</div>
<p>止损：收盘跌破前低 <b>1,151 元</b>（6月低点）或买入价 -8%（取先到者），无条件执行；时间止损：入场后 15 个交易日未创反弹新高降半仓。止盈：第一目标布林中轨/前平台 1,294~1,320 区间减 1/3；第二目标 1,348~1,360（8月平台）再减 1/3；剩余仓位跟踪 MA30 移动止盈。</p></div>

<div class="step"><div class="t">⑤ 失效条件（触发即放弃计划）</div>
<p>a) 三季报营收/净利增速显著低于预期（旺季动销证伪）；b) 飞天批价跌破 1,650 元（提价逻辑受损）；c) 主力资金连续 10 日净流出扩大；d) 大盘/白酒板块系统性走弱（板块指数跌破 9 月低点）。</p></div>

<div class="step"><div class="t">⑥ 环境确认（当前不支持激进）</div>
<p>主力资金近20日净流出 21.6 亿、机构基金持仓环比 -0.69pct、行业处深度调整磨底期——<b>当前环境不支持左侧重仓</b>；估值（PE 19.31×/股息率 4.14%）提供长期安全垫但非短期催化。<b>环境不支持时降仓或放弃，是计划的一部分而非胆怯。</b></p></div>

<p class="risk"><b>反向声音（本报告的自我反驳）：</b>如果你准备依据"超卖+低估值"抄底，请先回答——机构评级 97% 买入/增持与基金实际减仓 0.69pct 的背离说明什么？答案可能是：卖方观点滞后于基本面拐点（2026H1 净利首降），低估值反映的是"增长逻辑变化"而非错杀。<b>估值底 ≠ 价格底。</b></p>
</div>

<h2>六、已验证 / 未验证声明</h2>
<div class="panel">
<h3>✅ 已验证（附复现方式）</h3>
<ul>
  <li><b>行情数据真实性</b>：与独立第二源（westock，经 agentic_search 2026-09-16 返回）逐字段核对最近10根K线，10/10 零误差。复现：<code>python 01_fetch_data.py</code></li>
  <li><b>技术指标正确性</b>：MA/BOLL/MACD/KDJ 共15项与独立源同口径对跑，15/15 一致（≤0.0004）。复现：<code>python 02_indicators.py</code></li>
  <li><b>回测关键数字</b>：两套独立实现（向量化/逐bar账本）期末净值相对误差 1.6e-15。复现：<code>python 04_backtest.py</code></li>
  <li><b>前视偏差防线</b>：故意构造前视版本，收益虚增 __LOOKAHEAD__，证明执行时点处理正确且敏感。复现：同上。</li>
  <li><b>预测带宽标定</b>：20 个滚动起源回验，P5~P95 覆盖率 __COV90__%（期望90%）。复现：<code>python 03_forecast.py</code></li>
</ul>
<h3>❌ 未验证（明确列出，不装全验）</h3>
<ul>
  <li><b>RSI 与 westock 数值差异</b>——原因：对方为私有平滑口径，8种标准变体均无法对齐；已并列披露双方数值，定性结论一致。</li>
  <li><b>未来 20 日价格路径</b>——原因：本质不可验证；本报告只交付概率区间及其标定检验，不交付方向判断。</li>
  <li><b>基本面/资金流/机构目标价（PE 19.31、股息率 4.14%、目标价 1,658.08、主力净流出 21.6 亿等）</b>——原因：来自第三方数据平台（westock/neodata，经 agentic_search 2026-09-16），属二手来源，研报观点<span class="warn">需核实原文</span>；未与交易所/公司公告一手来源逐项核对。</li>
  <li><b>滑点 0.1% 的现实性</b>——原因：未接真实交易环境；茅台流动性好，实际滑点大概率更低，但未实证。</li>
  <li><b>前复权历史价格对 2020 年前持仓成本的适用性</b>——原因：除权因子链未与交易所公告核对到每一次分红除息。</li>
  <li><b>极端行情下的模型适用性</b>——原因：GBM 低估肥尾；滚动起源检验未覆盖类似 2015/2018 级别的极端时段。</li>
</ul>
<p style="font-size:13px;color:var(--muted)">复现路径：本目录 <code>01_fetch_data.py → 02_indicators.py → 03_forecast.py → 04_backtest.py → 05_build_report.py</code>；全部中间产物在 <code>data/</code> 目录（CSV/JSON），报告数字均可追溯。</p>
</div>

<footer>
<div class="disclaimer">
<b>免责声明</b>：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。市场有风险，投资需谨慎。任何投资决策应结合个人风险承受能力、资金状况和投资目标独立判断，必要时咨询持牌专业机构。过往表现不预示未来收益。
</div>
<p style="margin-top:8px">报告生成：本机量化管线（Python，固定随机种子，全部可复现） · 数据时点 __ASOF__ 收盘 · 分析标的 600519.SH 为任务默认指定</p>
</footer>

</div>

<script>
var P = __PAYLOAD__;

/* 图1: K线+MA+量+MACD+RSI */
(function(){
  var k = P.kline;
  var up = '#c0392b', dn = '#1e8449';
  echarts.init(document.getElementById('kline')).setOption({
    animation: false,
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    grid: [
      { left: 60, right: 20, top: 30, height: '42%' },
      { left: 60, right: 20, top: '58%', height: '12%' },
      { left: 60, right: 20, top: '76%', height: '11%' },
      { left: 60, right: 20, top: '92%', height: '6%' }
    ],
    xAxis: [
      { type: 'category', data: k.dates, gridIndex: 0, boundaryGap: true },
      { type: 'category', data: k.dates, gridIndex: 1, axisLabel: { show: false } },
      { type: 'category', data: k.dates, gridIndex: 2, axisLabel: { show: false } },
      { type: 'category', data: k.dates, gridIndex: 3, axisLabel: { show: false } }
    ],
    yAxis: [
      { scale: true, gridIndex: 0 },
      { scale: true, gridIndex: 1, axisLabel: { show: false }, splitLine: { show: false } },
      { scale: true, gridIndex: 2, axisLabel: { show: false }, splitLine: { show: false } },
      { scale: true, gridIndex: 3, min: 0, max: 100, axisLabel: { show: false }, splitLine: { show: false } }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1, 2, 3], start: 40, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1, 2, 3], start: 40, end: 100, bottom: 2 }
    ],
    legend: { data: ['MA10', 'MA30', 'MA60'], top: 2 },
    series: [
      { name: '日K', type: 'candlestick', data: k.ohlc, xAxisIndex: 0, yAxisIndex: 0,
        itemStyle: { color: up, color0: dn, borderColor: up, borderColor0: dn } },
      { name: 'MA10', type: 'line', data: k.ma10, xAxisIndex: 0, yAxisIndex: 0,
        symbol: 'none', lineStyle: { width: 1, color: '#e67e22' } },
      { name: 'MA30', type: 'line', data: k.ma30, xAxisIndex: 0, yAxisIndex: 0,
        symbol: 'none', lineStyle: { width: 1, color: '#2980b9' } },
      { name: 'MA60', type: 'line', data: k.ma60, xAxisIndex: 0, yAxisIndex: 0,
        symbol: 'none', lineStyle: { width: 1, color: '#8e44ad' } },
      { name: '成交量', type: 'bar', data: k.vol, xAxisIndex: 1, yAxisIndex: 1 },
      { name: 'DIF', type: 'line', data: k.dif, xAxisIndex: 2, yAxisIndex: 2,
        symbol: 'none', lineStyle: { width: 1, color: '#e67e22' } },
      { name: 'DEA', type: 'line', data: k.dea, xAxisIndex: 2, yAxisIndex: 2,
        symbol: 'none', lineStyle: { width: 1, color: '#2980b9' } },
      { name: 'MACD柱', type: 'bar', data: k.hist, xAxisIndex: 2, yAxisIndex: 2 },
      { name: 'RSI6', type: 'line', data: k.r6, xAxisIndex: 3, yAxisIndex: 3,
        symbol: 'none', lineStyle: { width: 1, color: '#c0392b' } },
      { name: 'RSI12', type: 'line', data: k.r12, xAxisIndex: 3, yAxisIndex: 3,
        symbol: 'none', lineStyle: { width: 1, color: '#2980b9' } }
    ]
  });
})();

/* 图2: 预测扇形 */
(function(){
  var f = P.fan;
  echarts.init(document.getElementById('fan')).setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['近60日收盘', 'P50中位路径'], top: 0 },
    grid: { left: 60, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: f.cats, boundaryGap: false },
    yAxis: { scale: true, name: '元' },
    series: [
      { name: 'P5下界', type: 'line', data: f.p5, stack: 'b95', symbol: 'none',
        lineStyle: { opacity: 0 }, silent: true },
      { name: 'P95带', type: 'line', data: f.p5band, stack: 'b95', symbol: 'none',
        lineStyle: { opacity: 0 }, areaStyle: { color: 'rgba(31,78,121,0.10)' }, silent: true },
      { name: 'P25下界', type: 'line', data: f.p25, stack: 'b75', symbol: 'none',
        lineStyle: { opacity: 0 }, silent: true },
      { name: 'P75带', type: 'line', data: f.p75band, stack: 'b75', symbol: 'none',
        lineStyle: { opacity: 0 }, areaStyle: { color: 'rgba(31,78,121,0.22)' }, silent: true },
      { name: '近60日收盘', type: 'line', data: f.close, symbol: 'none',
        lineStyle: { width: 2, color: '#1f2937' } },
      { name: 'P50中位路径', type: 'line', data: f.p50line, symbol: 'none',
        lineStyle: { width: 2, type: 'dashed', color: '#1f4e79' } }
    ]
  });
})();

/* 图3: 回测净值与回撤 */
(function(){
  var b = P.bt;
  echarts.init(document.getElementById('btchart')).setOption({
    animation: false,
    tooltip: { trigger: 'axis' },
    legend: { data: ['双均线(正确口径)', '买入持有', '双均线(前视偏差负对照)', '回撤-双均线', '回撤-买入持有'], top: 0 },
    grid: [
      { left: 60, right: 20, top: 36, height: '55%' },
      { left: 60, right: 20, top: '74%', height: '18%' }
    ],
    xAxis: [
      { type: 'category', data: b.dates, gridIndex: 0, boundaryGap: false },
      { type: 'category', data: b.dates, gridIndex: 1, axisLabel: { show: false } }
    ],
    yAxis: [
      { type: 'log', gridIndex: 0, name: '净值(对数)' },
      { type: 'value', gridIndex: 1, axisLabel: { formatter: function(v){ return (v*100).toFixed(0) + '%'; } } }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: 0, end: 100, bottom: 2 }
    ],
    series: [
      { name: '双均线(正确口径)', type: 'line', data: b.s, xAxisIndex: 0, yAxisIndex: 0,
        symbol: 'none', lineStyle: { width: 1.5, color: '#1f4e79' } },
      { name: '买入持有', type: 'line', data: b.bh, xAxisIndex: 0, yAxisIndex: 0,
        symbol: 'none', lineStyle: { width: 1.5, color: '#1e8449' } },
      { name: '双均线(前视偏差负对照)', type: 'line', data: b.la, xAxisIndex: 0, yAxisIndex: 0,
        symbol: 'none', lineStyle: { width: 1, type: 'dashed', color: '#9ca3af' } },
      { name: '回撤-双均线', type: 'line', data: b.dds, xAxisIndex: 1, yAxisIndex: 1,
        symbol: 'none', lineStyle: { width: 1, color: '#1f4e79' },
        areaStyle: { color: 'rgba(31,78,121,0.15)' } },
      { name: '回撤-买入持有', type: 'line', data: b.ddbh, xAxisIndex: 1, yAxisIndex: 1,
        symbol: 'none', lineStyle: { width: 1, color: '#1e8449' },
        areaStyle: { color: 'rgba(30,132,73,0.12)' } }
    ]
  });
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
