# -*- coding: utf-8 -*-
"""报告生成：自包含 HTML（图表 base64 内嵌）+ Markdown 版本
输出: report.html, report.md
"""
import base64
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT, CH = ROOT / "data", ROOT / "output", ROOT / "output" / "charts"

res = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
meta, ov = res["meta"], res["overview"]
pred, bt, adv = res["prediction"], res["backtest"], res["advice"]
lr, ml = pred["lr"], pred["ml"]
btA, btB, btBH = bt["strategyA"], bt["strategyB"], bt["buy_hold"]
tsA, tsB = bt["trades_A"], bt["trades_B"]
ind_table = res["snapshot_indicators"]
now = datetime.now().strftime("%Y-%m-%d %H:%M")


def b64(name):
    return "data:image/png;base64," + base64.b64encode((CH / name).read_bytes()).decode()


def f2(v):
    return "—" if v is None else f"{v:,.2f}"


def sgn(v, digits=2, suffix="%"):
    if v is None:
        return "—"
    s = f"{v:+.{digits}f}{suffix}" if suffix else f"{v:+.{digits}f}"
    cls = "pos" if v > 0 else ("neg" if v < 0 else "")
    return f'<span class="{cls}">{s}</span>'


CSS = """
:root{--ink:#1c2333;--muted:#5b6472;--line:#e3e7ee;--accent:#1f5aa8;--soft:#f5f7fa;--up:#c0392b;--down:#0f7a4d}
*{box-sizing:border-box}
body{margin:0;background:var(--soft);color:var(--ink);font-family:"Microsoft YaHei","PingFang SC","Segoe UI",sans-serif;line-height:1.8}
.wrap{max-width:1020px;margin:0 auto;padding:28px 20px 60px}
.hero{background:linear-gradient(135deg,#14335c,#1f5aa8);color:#fff;border-radius:14px;padding:26px 32px;margin-bottom:26px}
.hero h1{margin:0 0 6px;font-size:26px}
.hero .sub{font-size:13.5px;opacity:.92}
.meta{display:flex;flex-wrap:wrap;gap:8px 26px;margin-top:14px;font-size:13px}
h2{font-size:20px;border-left:5px solid var(--accent);padding-left:12px;margin:36px 0 14px}
h3{font-size:16px;margin:22px 0 10px;color:#2a3550}
.cards{display:flex;flex-wrap:wrap;gap:12px;margin:14px 0}
.card{flex:1 1 150px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px 16px}
.card .k{font-size:12px;color:var(--muted)}
.card .v{font-size:21px;font-weight:700;margin-top:3px}
table{width:100%;border-collapse:collapse;background:#fff;font-size:13.5px;margin:10px 0}
th,td{border:1px solid var(--line);padding:7px 11px;text-align:left;vertical-align:top}
th{background:#eef2f8;font-weight:600;white-space:nowrap}
img.chart{width:100%;border:1px solid var(--line);border-radius:10px;margin:10px 0;display:block}
.note{background:#fff;border-left:4px solid var(--accent);padding:11px 16px;margin:12px 0;font-size:13.5px;border-radius:0 8px 8px 0}
.warn{background:#fff8ef;border-left:4px solid #e8890c;padding:11px 16px;margin:12px 0;font-size:13.5px;border-radius:0 8px 8px 0}
ul{margin:8px 0;padding-left:22px}
li{margin:5px 0}
.pos{color:var(--up);font-weight:600}
.neg{color:var(--down);font-weight:600}
footer{margin-top:44px;font-size:12.5px;color:var(--muted);border-top:1px solid var(--line);padding-top:14px}
code{background:#eef2f8;border-radius:4px;padding:1px 6px;font-size:12.5px}
"""

H = []
H.append(f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{meta['name']}({meta['code']}) 股票分析报告</title><style>{CSS}</style></head><body><div class="wrap">
<div class="hero">
<h1>{meta['name']}（{meta['code']}）股票分析报告</h1>
<div class="sub">A股 · {meta['fq']} · {meta['klt']} ｜ 本报告由自动化流水线生成，仅供研究演示，不构成投资建议</div>
<div class="meta">
<span>数据区间：{ov['first_date']} ~ {ov['last_date']}（{meta['rows']} 个交易日）</span>
<span>数据源：{meta['source']}</span>
<span>生成时间：{now}</span>
</div></div>""")

# ---- 摘要 ----
H.append("<h2>一、摘要</h2><ul>")
for s_ in res["summary"]:
    H.append(f"<li>{s_}</li>")
H.append("</ul>")

# ---- 行情概览 ----
H.append(f"""<h2>二、行情数据概览</h2>
<div class="cards">
<div class="card"><div class="k">最新收盘（{ov['last_date']}）</div><div class="v">¥{ov['last_close']}</div></div>
<div class="card"><div class="k">区间累计涨跌</div><div class="v {('pos' if ov['period_return_pct']>0 else 'neg')}">{ov['period_return_pct']:+.2f}%</div></div>
<div class="card"><div class="k">20日年化波动率</div><div class="v">{ov['ann_vol_20d_pct']}%</div></div>
<div class="card"><div class="k">区间最高</div><div class="v">{ov['max_high']}<span style="font-size:12px;color:#5b6472">（{ov['max_high_date']}）</span></div></div>
<div class="card"><div class="k">区间最低</div><div class="v">{ov['min_low']}<span style="font-size:12px;color:#5b6472">（{ov['min_low_date']}）</span></div></div>
</div>
<table><tr><th>日均成交量</th><td>{ov['avg_volume']:,} 手</td><th>日均成交额</th><td>{'—' if ov['avg_amount_yi'] is None else str(ov['avg_amount_yi'])+' 亿元'}</td></tr>
<tr><th>平均换手率</th><td>{'—' if ov['avg_turnover_pct'] is None else str(ov['avg_turnover_pct'])+'%'}</td><th>起点收盘价</th><td>{ov['first_close']} 元（{ov['first_date']}）</td></tr></table>
<div class="note">数据获取：通过公开行情接口抓取 {meta['rows']} 个交易日的 {meta['fq']}日线（OHLC、成交量、成交额），逐行校验 OHLC 逻辑关系与日期单调性后落盘为 <code>data/{meta['code']}_daily.csv</code>，全流程可复现。</div>""")

# ---- K线与技术指标 ----
H.append("<h2>三、K线图与技术指标</h2>")
H.append(f'<img class="chart" src="{b64("chart_kline.png")}" alt="K线图">')
H.append(f'<img class="chart" src="{b64("chart_indicators.png")}" alt="技术指标">')
H.append("<h3>指标最新读数</h3><table><tr><th>指标</th><th>数值</th><th>解读</th></tr>")
for row in ind_table:
    H.append(f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>")
H.append("</table>")

# ---- 趋势预测 ----
H.append(f"""<h2>四、趋势预测模型</h2>
<div class="note"><b>方法说明</b>：模型A为对数价格线性回归（近{lr['window_days']}日），仅用于刻画既有趋势并外推{lr['horizon_days']}个交易日，附带 ±1.96σ 残差带——它<b>不是</b>价格预测。模型B为岭回归（12个价量特征，标准化后 λ=1），预测未来5日收益率，采用 <b>walk-forward 滚动验证</b>：每日仅用该日之前已实现的样本训练，杜绝未来函数。</div>
<img class="chart" src="{b64('chart_prediction.png')}" alt="趋势预测">
<table>
<tr><th>项目</th><th>模型A（线性外推）</th><th>模型B（岭回归 5日收益）</th></tr>
<tr><td>核心参数</td><td>窗口{lr['window_days']}日，年化趋势斜率 {sgn(lr['slope_ann_pct'])}</td><td>12特征：滞后收益(1/2/3/5/10日)、均线偏离、RSI、MACD柱、量比、ATR</td></tr>
<tr><td>验证方式</td><td>残差带宽度（描述性）</td><td>walk-forward {ml['eval_days']} 日滚动样本外验证</td></tr>
<tr><td>方向准确率</td><td>—</td><td>{ml['acc_pct']}%（基线①全看多 {ml['baseline_up_pct']}%；基线②动量延续 {ml['baseline_persist_pct']}%）</td></tr>
<tr><td>误差/相关性</td><td>σ={lr['sigma']}</td><td>MAE {ml['mae_pct']}%{'｜相关系数 '+str(ml['corr']) if ml['corr'] is not None else ''}</td></tr>
<tr><td>当前输出</td><td>20日外推终点 {lr['forecast_end']} 元（区间 {lr['band_end'][0]}~{lr['band_end'][1]}）</td><td>未来5日 {sgn(ml['live_pred_5d_pct'])}（方向：{ml['live_dir']}）</td></tr>
</table>
<div class="warn"><b>诚实结论</b>：模型B方向准确率 {ml['acc_pct']}% 相对最强基线（{max(ml['baseline_up_pct'], ml['baseline_persist_pct'])}%）{'高 ' + str(round(ml['acc_pct'] - max(ml['baseline_up_pct'], ml['baseline_persist_pct']), 2)) + ' 个百分点，统计意义上属于弱边际，不构成可靠交易信号' if ml['beats_baseline'] else '并无优势，即该特征集在样本外<b>不具备</b>稳定预测能力'}。短期股价方向本质接近随机游走，请勿将预测输出当作买卖依据。</div>""")

# ---- 回测 ----
H.append(f"""<h2>五、回测验证</h2>
<div class="note"><b>回测规则</b>：{bt['assumptions']['signal']}；成本假设：{bt['assumptions']['commission']}，印花税 {bt['assumptions']['stamp_tax']}（卖出），滑点 {bt['assumptions']['slippage']}；{bt['assumptions']['lot']}，{bt['assumptions']['position']}。价格口径：{bt['assumptions']['price_basis']}。回测区间 {bt['period']['start']} ~ {bt['period']['end']}（{bt['period']['days']} 个交易日）。</div>
<img class="chart" src="{b64('chart_backtest.png')}" alt="回测净值">
<table>
<tr><th>指标</th><th>策略A：MA5/20双均线</th><th>策略B：双均线+MA60过滤</th><th>买入持有（基准）</th></tr>
<tr><td>期末净值</td><td>¥{btA['final_equity']:,.0f}</td><td>¥{btB['final_equity']:,.0f}</td><td>¥{btBH['final_equity']:,.0f}</td></tr>
<tr><td>总收益率</td><td>{sgn(btA['total_return_pct'])}</td><td>{sgn(btB['total_return_pct'])}</td><td>{sgn(btBH['total_return_pct'])}</td></tr>
<tr><td>年化收益</td><td>{sgn(btA['cagr_pct'])}</td><td>{sgn(btB['cagr_pct'])}</td><td>{sgn(btBH['cagr_pct'])}</td></tr>
<tr><td>年化波动</td><td>{btA['ann_vol_pct']}%</td><td>{btB['ann_vol_pct']}%</td><td>{btBH['ann_vol_pct']}%</td></tr>
<tr><td>夏普比率(rf=0)</td><td>{f2(btA['sharpe'])}</td><td>{f2(btB['sharpe'])}</td><td>{f2(btBH['sharpe'])}</td></tr>
<tr><td>最大回撤</td><td><span class="neg">{btA['max_drawdown_pct']:.2f}%</span></td><td><span class="neg">{btB['max_drawdown_pct']:.2f}%</span></td><td><span class="neg">{btBH['max_drawdown_pct']:.2f}%</span></td></tr>
<tr><td>平仓交易次数</td><td>{tsA['n_closed']}（在持 {tsA['n_open']}）</td><td>{tsB['n_closed']}（在持 {tsB['n_open']}）</td><td>1</td></tr>
<tr><td>胜率</td><td>{f2(tsA['win_rate_pct'])}%</td><td>{f2(tsB['win_rate_pct'])}%</td><td>—</td></tr>
<tr><td>盈亏比(PF)</td><td>{f2(tsA['profit_factor'])}</td><td>{f2(tsB['profit_factor'])}</td><td>—</td></tr>
<tr><td>平均持仓天数</td><td>{f2(tsA['avg_hold_days'])}</td><td>{f2(tsB['avg_hold_days'])}</td><td>{bt['period']['days']}</td></tr>
<tr><td>持仓时间占比</td><td>{btA['exposure_pct']}%</td><td>{btB['exposure_pct']}%</td><td>100%</td></tr>
</table>
<div class="note">逐笔记录见 <code>data/backtest_trades_A.csv</code> 与 <code>data/backtest_trades_B.csv</code>，净值序列见 <code>data/backtest_equity.csv</code>，可独立复核。若策略收益不及买入持有，说明该简单信号在本标的/本区间不具备超额收益，属于正常且常见的结果——回测的意义在于证伪而非找圣杯。</div>""")

# ---- 策略建议 ----
lv = adv["levels"]
H.append(f"""<h2>六、交易策略建议</h2>
<div class="note"><b>当前判断</b>：{adv['trend_state']}（{ov['last_date']} 收盘 {ov['last_close']} 元）。</div>
<ul>""")
for b in adv["bullets"]:
    H.append(f"<li>{b}</li>")
H.append("</ul>")
H.append(f"""<h3>关键价位</h3>
<table><tr><th>项目</th><th>价位（元）</th><th>说明</th></tr>
<tr><td>支撑参考</td><td>{lv['支撑']}</td><td>近60日最低价</td></tr>
<tr><td>压力参考</td><td>{lv['压力']}</td><td>近60日最高价</td></tr>
<tr><td>移动止损参考</td><td>{lv['止损参考']}</td><td>收盘价 − 2×ATR({lv['ATR(14)']})</td></tr></table>
<h3>仓位与纪律</h3><ul>""")
for b in adv["discipline"]:
    H.append(f"<li>{b}</li>")
H.append("</ul>")

# ---- 局限与声明 ----
H.append(f"""<h2>七、方法局限与风险声明</h2>
<div class="warn">
<ul>
<li><b>预测局限</b>：模型A/B 仅使用历史价量信息，未纳入基本面、资金面与事件驱动；线性/岭回归结构简单，存在欠拟合与过拟合的双重风险；walk-forward 准确率接近基线时，预测输出不构成信号。</li>
<li><b>回测局限</b>：以次日开盘价成交是理想化假设，涨停无法买入/跌停无法卖出、流动性冲击未建模；成本参数（佣金/印花税/滑点）为固定近似，敏感性未知；样本仅覆盖单一标的一段时间，<b>结论不能外推到其他标的或未来行情</b>。</li>
<li><b>数据局限</b>：{meta['fq']}价格已将分红折入历史序列；数据来自公开接口，若接口口径变化可能引入误差（以交易所披露为准）。</li>
<li><b>免责声明</b>：本报告全部内容由程序基于公开历史数据自动生成，仅供学习与研究演示，<b>不构成任何投资建议或买卖推荐</b>。股市有风险，入市需谨慎；据此操作，风险自担。</li>
</ul></div>
<footer>
复现方式（依序执行）：<code>scripts/fetch_data.py</code> → <code>scripts/run_analysis.py</code> → <code>scripts/make_charts.py</code> → <code>scripts/make_report.py</code><br>
产出清单：数据 <code>data/*.csv</code>（原始/指标/预测/回测共7个）｜图表 <code>output/charts/*.png</code>（4张）｜结果汇总 <code>output/results.json</code>｜本报告 <code>report.html</code> / <code>report.md</code>
</footer></div></body></html>""")

html = "\n".join(H)
(ROOT / "report.html").write_text(html, encoding="utf-8")

# ================= Markdown 版本 =================
M = []
M.append(f"# {meta['name']}（{meta['code']}）股票分析报告\n")
M.append(f"> A股 · {meta['fq']} · {meta['klt']} ｜ 数据区间 {ov['first_date']} ~ {ov['last_date']}（{meta['rows']} 个交易日） ｜ 数据源：{meta['source']} ｜ 生成时间：{now}\n")
M.append("> 本报告由自动化流水线生成，仅供研究演示，不构成投资建议。\n")
M.append("## 一、摘要\n")
for s_ in res["summary"]:
    M.append(f"- {s_}")
M.append("\n## 二、行情数据概览\n")
M.append(f"| 项目 | 数值 |\n|---|---|\n| 最新收盘 | ¥{ov['last_close']}（{ov['last_date']}） |\n| 区间累计涨跌 | {ov['period_return_pct']:+.2f}% |\n| 20日年化波动率 | {ov['ann_vol_20d_pct']}% |\n| 区间最高/最低 | {ov['max_high']}（{ov['max_high_date']}）/ {ov['min_low']}（{ov['min_low_date']}） |\n| 日均成交量 | {ov['avg_volume']:,} 手 |")
M.append("\n![K线图](output/charts/chart_kline.png)\n")
M.append("## 三、K线图与技术指标\n\n![技术指标](output/charts/chart_indicators.png)\n")
M.append("| 指标 | 数值 | 解读 |\n|---|---|---|")
for row in ind_table:
    M.append(f"| {row[0]} | {row[1]} | {row[2]} |")
M.append(f"\n## 四、趋势预测模型\n\n![趋势预测](output/charts/chart_prediction.png)\n")
M.append(f"- **模型A（对数线性外推{lr['horizon_days']}日）**：年化趋势斜率 {lr['slope_ann_pct']:+.2f}%，外推终点 {lr['forecast_end']} 元（±1.96σ 区间 {lr['band_end'][0]}~{lr['band_end'][1]}），仅刻画趋势非预测。")
M.append(f"- **模型B（岭回归 5日收益，walk-forward {ml['eval_days']} 日）**：方向准确率 **{ml['acc_pct']}%**（基线：全看多 {ml['baseline_up_pct']}%、动量延续 {ml['baseline_persist_pct']}%）；MAE {ml['mae_pct']}%{'，相关系数 ' + str(ml['corr']) if ml['corr'] is not None else ''}；当前5日预测 {ml['live_pred_5d_pct']:+.2f}%（{ml['live_dir']}）。")
M.append(f"- **诚实结论**：{('准确率仅略高于基线，属弱边际，不构成可靠信号。' if ml['beats_baseline'] else '样本外不优于基线，该特征集不具备稳定预测能力。')}短期方向接近随机游走。\n")
M.append("## 五、回测验证\n\n![回测](output/charts/chart_backtest.png)\n")
M.append(f"回测区间 {bt['period']['start']} ~ {bt['period']['end']}；假设：{bt['assumptions']['signal']}，{bt['assumptions']['commission']}，印花税{bt['assumptions']['stamp_tax']}（卖出），滑点{bt['assumptions']['slippage']}，整手，无止损，初始 {bt['assumptions']['initial_capital']/10000:.0f} 万元。\n")
M.append("| 指标 | 策略A 双均线 | 策略B +MA60过滤 | 买入持有 |\n|---|---|---|---|")
M.append(f"| 总收益 | {btA['total_return_pct']:+.2f}% | {btB['total_return_pct']:+.2f}% | {btBH['total_return_pct']:+.2f}% |")
M.append(f"| 年化收益 | {f2(btA['cagr_pct'])}% | {f2(btB['cagr_pct'])}% | {f2(btBH['cagr_pct'])}% |")
M.append(f"| 夏普(rf=0) | {f2(btA['sharpe'])} | {f2(btB['sharpe'])} | {f2(btBH['sharpe'])} |")
M.append(f"| 最大回撤 | {btA['max_drawdown_pct']:.2f}% | {btB['max_drawdown_pct']:.2f}% | {btBH['max_drawdown_pct']:.2f}% |")
M.append(f"| 平仓次数/胜率 | {tsA['n_closed']} / {f2(tsA['win_rate_pct'])}% | {tsB['n_closed']} / {f2(tsB['win_rate_pct'])}% | 1 / — |")
M.append(f"| 持仓占比 | {btA['exposure_pct']}% | {btB['exposure_pct']}% | 100% |")
M.append("\n逐笔记录：`data/backtest_trades_A.csv`、`data/backtest_trades_B.csv`；净值：`data/backtest_equity.csv`。\n")
M.append("## 六、交易策略建议\n")
M.append(f"**当前判断**：{adv['trend_state']}。\n")
for b in adv["bullets"]:
    M.append(f"- {b}")
M.append(f"\n关键价位：支撑 {lv['支撑']}（近60日低点）｜压力 {lv['压力']}（近60日高点）｜移动止损参考 {lv['止损参考']}（收盘−2×ATR）。\n")
for b in adv["discipline"]:
    M.append(f"- {b}")
M.append("\n## 七、方法局限与风险声明\n")
M.append("""> 预测仅基于历史价量，未含基本面/资金面；回测为理想化执行（未建模涨跌停、流动性），成本假设固定；单一标的单一区间，结论不可外推。
> **本报告由程序自动生成，仅供学习研究，不构成任何投资建议。股市有风险，入市需谨慎。**
>
> 复现：`scripts/fetch_data.py` → `run_analysis.py` → `make_charts.py` → `make_report.py`；中间产物见 `data/`、`output/`。""")

(ROOT / "report.md").write_text("\n".join(M), encoding="utf-8")
print(f"OK: report.html ({len(html):,} bytes) + report.md")
