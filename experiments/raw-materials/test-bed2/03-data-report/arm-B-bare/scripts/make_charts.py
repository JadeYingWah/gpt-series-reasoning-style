# -*- coding: utf-8 -*-
"""可视化：K线+均线+BOLL+成交量 / MACD+RSI+KDJ / 趋势外推 / 回测净值
输出: output/charts/chart_kline.png, chart_indicators.png, chart_prediction.png, chart_backtest.png
配色遵循A股惯例：涨=红，跌=绿
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / "data", ROOT / "output"
CH = OUT / "charts"
CH.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

UP, DOWN = "#d9463e", "#159a6c"
C_MA = {"ma5": "#e8a013", "ma10": "#1d6fd1", "ma20": "#8e44ad", "ma60": "#555f6d"}

meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
res = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
df = pd.read_csv(DATA / "600519_enriched.csv", parse_dates=["date"])
fc = pd.read_csv(DATA / "forecast_lr.csv", parse_dates=["date"])
eq = pd.read_csv(DATA / "backtest_equity.csv", parse_dates=["date"])


def date_ticks(ax, dates, every=21):
    idx = list(range(0, len(dates), every))
    if idx[-1] != len(dates) - 1:
        idx.append(len(dates) - 1)
    ax.set_xticks(idx)
    ax.set_xticklabels([pd.Timestamp(dates[i]).strftime("%y-%m-%d") for i in idx],
                       rotation=45, ha="right", fontsize=8)


# ---------- 1. K线 + 均线 + BOLL + 成交量 ----------
N = 250
w = df.iloc[-N:].reset_index(drop=True)
x = np.arange(N)
colors = [UP if c >= o else DOWN for o, c in zip(w["open"], w["close"])]

fig = plt.figure(figsize=(12.6, 8.2))
gs = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.08)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1], sharex=ax1)

ax1.vlines(x, w["low"], w["high"], color=colors, lw=0.8, alpha=0.9)
body = (w["close"] - w["open"]).abs().clip(lower=w["close"] * 1e-4)
ax1.bar(x, body, bottom=np.minimum(w["open"], w["close"]), width=0.66,
        color=colors, edgecolor=colors, lw=0.4)
ax1.fill_between(x, w["boll_up"], w["boll_low"], color="#7aa6d9", alpha=0.10, label="BOLL(20,2)")
for m, c in C_MA.items():
    ax1.plot(x, w[m], lw=1.2, color=c, label=m.upper())
ax1.legend(loc="upper left", fontsize=9, ncol=5, framealpha=0.6)
ax1.set_title(f"{meta['name']}({meta['code']}) 日K线 · {meta['fq']} · 近{N}个交易日", fontsize=13, pad=10)
ax1.set_ylabel("价格（元）")
ax1.grid(alpha=0.25, lw=0.5)
plt.setp(ax1.get_xticklabels(), visible=False)

ax2.bar(x, w["volume"], color=colors, width=0.66, alpha=0.75)
ax2.plot(x, w["vol_ma5"], color="#e8a013", lw=1.0, label="VOL_MA5")
ax2.set_ylabel("成交量（手）")
ax2.legend(loc="upper left", fontsize=8, framealpha=0.6)
ax2.grid(alpha=0.25, lw=0.5)
date_ticks(ax2, w["date"])
fig.tight_layout()
fig.savefig(CH / "chart_kline.png", dpi=150)
plt.close(fig)

# ---------- 2. MACD / RSI / KDJ ----------
fig, axes = plt.subplots(3, 1, figsize=(12.6, 9), sharex=True,
                         gridspec_kw={"height_ratios": [1.2, 1, 1], "hspace": 0.12})
axm, axr, axk = axes
hist_colors = [UP if v >= 0 else DOWN for v in w["macd_hist"]]
axm.bar(x, w["macd_hist"], color=hist_colors, width=0.66, alpha=0.8, label="MACD柱")
axm.plot(x, w["dif"], color="#1d6fd1", lw=1.2, label="DIF")
axm.plot(x, w["dea"], color="#e8a013", lw=1.2, label="DEA")
axm.axhline(0, color="#888", lw=0.6)
axm.legend(loc="upper left", fontsize=9, ncol=3, framealpha=0.6)
axm.set_title(f"{meta['name']}({meta['code']}) 技术指标 · 近{N}个交易日", fontsize=13, pad=8)
axm.set_ylabel("MACD")
axm.grid(alpha=0.25, lw=0.5)

axr.plot(x, w["rsi6"], color="#d9463e", lw=1.1, label="RSI6")
axr.plot(x, w["rsi12"], color="#1d6fd1", lw=1.1, label="RSI12")
axr.plot(x, w["rsi24"], color="#555f6d", lw=1.1, label="RSI24")
axr.axhline(70, color="#d9463e", lw=0.7, ls="--", alpha=0.7)
axr.axhline(30, color="#159a6c", lw=0.7, ls="--", alpha=0.7)
axr.axhline(50, color="#aaa", lw=0.6, ls=":")
axr.set_ylim(0, 100)
axr.legend(loc="upper left", fontsize=9, ncol=3, framealpha=0.6)
axr.set_ylabel("RSI")
axr.grid(alpha=0.25, lw=0.5)

axk.plot(x, w["kdj_k"], color="#1d6fd1", lw=1.1, label="K")
axk.plot(x, w["kdj_d"], color="#e8a013", lw=1.1, label="D")
axk.plot(x, w["kdj_j"], color="#8e44ad", lw=1.0, label="J")
axk.axhline(80, color="#d9463e", lw=0.7, ls="--", alpha=0.7)
axk.axhline(20, color="#159a6c", lw=0.7, ls="--", alpha=0.7)
axk.legend(loc="upper left", fontsize=9, ncol=3, framealpha=0.6)
axk.set_ylabel("KDJ")
axk.grid(alpha=0.25, lw=0.5)
date_ticks(axk, w["date"])
fig.tight_layout()
fig.savefig(CH / "chart_indicators.png", dpi=150)
plt.close(fig)

# ---------- 3. 趋势外推 + 预测带 ----------
NH = 180
h = df.iloc[-NH:].reset_index(drop=True)
W_LR = res["prediction"]["lr"]["window_days"]
yh = np.log(df["close"].values[-W_LR:])
coef = np.polyfit(np.arange(W_LR), yh, 1)
sigma = res["prediction"]["lr"]["sigma"]
xf = np.arange(NH, NH + len(fc))
fit_x = np.arange(NH - W_LR, NH)
fit_y = np.exp(np.polyval(coef, np.arange(0, W_LR)))

fig, ax = plt.subplots(figsize=(12.6, 6.2))
ax.plot(np.arange(NH), h["close"], color="#1c2333", lw=1.4, label="历史收盘价")
ax.plot(fit_x, fit_y, color="#e8a013", lw=1.4, ls="--", label=f"对数线性拟合（近{W_LR}日）")
ax.plot(xf, fc["fit"], color="#d9463e", lw=1.6, label="外推趋势（未来20交易日）")
ax.fill_between(xf, fc["lo"], fc["hi"], color="#d9463e", alpha=0.15, label="±1.96σ 区间")
ax.axvline(NH - 0.5, color="#888", lw=0.8, ls=":")
ax.annotate("今日", xy=(NH - 0.5, ax.get_ylim()[0]), xytext=(NH - 12, ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.04), fontsize=9, color="#555")
ml = res["prediction"]["ml"]
ax.set_title(f"趋势外推（模型A）与置信带 ｜ 模型B当前5日方向预测：{ml['live_dir']} {ml['live_pred_5d_pct']:+.2f}%（walk-forward 准确率 {ml['acc_pct']}%）",
             fontsize=12, pad=10)
ax.set_ylabel("价格（元）")
ax.legend(loc="upper left", fontsize=9, framealpha=0.6)
ax.grid(alpha=0.25, lw=0.5)
ticks = list(range(0, NH, 30)) + [NH - 1] + [int(xf[-1])]
ax.set_xticks(sorted(set(ticks)))
ax.set_xticklabels([pd.Timestamp(h['date'].iloc[min(i, NH - 1)]).strftime("%y-%m-%d") for i in sorted(set(ticks))],
                   rotation=45, ha="right", fontsize=8)
fig.tight_layout()
fig.savefig(CH / "chart_prediction.png", dpi=150)
plt.close(fig)

# ---------- 4. 回测净值 + 回撤 ----------
n_bt = len(eq)
xb = np.arange(n_bt)


def dd(arr):
    arr = np.asarray(arr, dtype=float)
    return arr / np.maximum.accumulate(arr) - 1


fig = plt.figure(figsize=(12.6, 8))
gs = fig.add_gridspec(2, 1, height_ratios=[2.2, 1], hspace=0.1)
axe = fig.add_subplot(gs[0])
axd = fig.add_subplot(gs[1], sharex=axe)

btA, btB, btBH = res["backtest"]["strategyA"], res["backtest"]["strategyB"], res["backtest"]["buy_hold"]
axe.plot(xb, eq["strategyA"], color="#1d6fd1", lw=1.4,
         label=f"策略A 双均线MA5/20（{btA['total_return_pct']:+.1f}%）")
axe.plot(xb, eq["strategyB"], color="#e8a013", lw=1.4,
         label=f"策略B 双均线+MA60过滤（{btB['total_return_pct']:+.1f}%）")
axe.plot(xb, eq["buy_hold"], color="#8a8f98", lw=1.2, ls="--",
         label=f"买入持有（{btBH['total_return_pct']:+.1f}%）")
axe.axhline(100000, color="#888", lw=0.7, ls=":")
axe.set_title(f"回测净值对比（初始 {res['backtest']['assumptions']['initial_capital']/10000:.0f} 万元，含佣金/印花税/滑点，{res['backtest']['period']['start']} ~ {res['backtest']['period']['end']}）",
              fontsize=12, pad=10)
axe.set_ylabel("账户净值（元）")
axe.legend(loc="upper left", fontsize=9, framealpha=0.6)
axe.grid(alpha=0.25, lw=0.5)
plt.setp(axe.get_xticklabels(), visible=False)

axd.fill_between(xb, dd(eq["strategyA"]) * 100, 0, color="#1d6fd1", alpha=0.25, label="策略A回撤")
axd.fill_between(xb, dd(eq["strategyB"]) * 100, 0, color="#e8a013", alpha=0.22, label="策略B回撤")
axd.plot(xb, dd(eq["buy_hold"]) * 100, color="#8a8f98", lw=1.0, label="买入持有回撤")
axd.set_ylabel("回撤（%）")
axd.legend(loc="lower left", fontsize=8, framealpha=0.6)
axd.grid(alpha=0.25, lw=0.5)
date_ticks(axd, eq["date"])
fig.tight_layout()
fig.savefig(CH / "chart_backtest.png", dpi=150)
plt.close(fig)

print("OK: 4 charts ->", CH)
