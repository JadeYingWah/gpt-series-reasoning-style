# -*- coding: utf-8 -*-
"""技术指标 + 趋势预测模型 + 回测验证
输入: data/600519_daily.csv (fetch_data.py 产出)
输出: data/600519_enriched.csv, data/forecast_lr.csv, data/wf_predictions.csv,
      data/backtest_trades.csv, data/backtest_equity.csv, output/results.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"
DATA.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
df = pd.read_csv(DATA / "600519_daily.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True)
for c in ["open", "close", "high", "low", "volume", "amount", "pct_chg"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df["turnover"] = pd.to_numeric(df["turnover"], errors="coerce")
assert df[["open", "close", "high", "low"]].notna().all().all(), "OHLC 存在缺失"

# ================= 1. 技术指标 =================
for n in (5, 10, 20, 60):
    df[f"ma{n}"] = df["close"].rolling(n).mean()
df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
df["ema26"] = df["close"].ewm(span=26, adjust=False).mean()
df["dif"] = df["ema12"] - df["ema26"]
df["dea"] = df["dif"].ewm(span=9, adjust=False).mean()
df["macd_hist"] = 2 * (df["dif"] - df["dea"])  # 国内口径 MACD柱=2×(DIF−DEA)


def rsi(s, n):
    d = s.diff()
    g = d.clip(lower=0)
    l = -d.clip(upper=0)
    ag = g.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    al = l.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    r = 100 - 100 / (1 + ag / al)
    r = r.mask((al == 0) & (ag > 0), 100.0)
    r = r.mask((al == 0) & (ag == 0), 50.0)
    return r


for n in (6, 12, 24):
    df[f"rsi{n}"] = rsi(df["close"], n)

low9 = df["low"].rolling(9).min()
high9 = df["high"].rolling(9).max()
rng9 = (high9 - low9).replace(0, np.nan)
rsv = ((df["close"] - low9) / rng9 * 100).fillna(50)
df["kdj_k"] = rsv.ewm(alpha=1 / 3, adjust=False).mean()
df["kdj_d"] = df["kdj_k"].ewm(alpha=1 / 3, adjust=False).mean()
df["kdj_j"] = 3 * df["kdj_k"] - 2 * df["kdj_d"]

df["boll_mid"] = df["ma20"]
sd20 = df["close"].rolling(20).std(ddof=0)
df["boll_up"] = df["boll_mid"] + 2 * sd20
df["boll_low"] = df["boll_mid"] - 2 * sd20
df["boll_width"] = (df["boll_up"] - df["boll_low"]) / df["boll_mid"]

prev_c = df["close"].shift(1)
tr = pd.concat([df["high"] - df["low"], (df["high"] - prev_c).abs(), (df["low"] - prev_c).abs()], axis=1).max(axis=1)
df["atr14"] = tr.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
df["obv"] = (np.sign(df["close"].diff()).fillna(0) * df["volume"]).cumsum()
df["vol_ma5"] = df["volume"].rolling(5).mean()
df["vol_ma10"] = df["volume"].rolling(10).mean()
df["ret"] = df["close"].pct_change()
df["vol20_ann"] = df["ret"].rolling(20).std() * np.sqrt(252)
df["hi52w"] = df["close"].rolling(244, min_periods=60).max()
df["lo52w"] = df["close"].rolling(244, min_periods=60).min()

df.to_csv(DATA / "600519_enriched.csv", index=False)

# ================= 2. 趋势预测模型 =================
# --- 模型A：对数价格线性回归，外推20个交易日（含±1.96σ带） ---
W_LR, H_FC = 120, 20
y = np.log(df["close"].values[-W_LR:])
x = np.arange(W_LR)
coef = np.polyfit(x, y, 1)
resid = y - np.polyval(coef, x)
sigma = float(resid.std(ddof=2))
xf = np.arange(W_LR, W_LR + H_FC)
fit_line = np.polyval(coef, xf)
fut_dates = pd.bdate_range(df["date"].iloc[-1] + pd.Timedelta(days=1), periods=H_FC)
forecast = pd.DataFrame({
    "date": fut_dates,
    "fit": np.exp(fit_line),
    "lo": np.exp(fit_line - 1.96 * sigma),
    "hi": np.exp(fit_line + 1.96 * sigma),
})
forecast.to_csv(DATA / "forecast_lr.csv", index=False)
lr = {
    "window_days": W_LR,
    "horizon_days": H_FC,
    "slope_ann_pct": round((np.exp(coef[0] * 252) - 1) * 100, 2),
    "sigma": round(sigma, 5),
    "fit_end": round(float(np.exp(np.polyval(coef, W_LR - 1))), 2),
    "forecast_end": round(float(forecast["fit"].iloc[-1]), 2),
    "band_end": [round(float(forecast["lo"].iloc[-1]), 2), round(float(forecast["hi"].iloc[-1]), 2)],
}

# --- 模型B：岭回归 walk-forward 预测未来5日收益 ---
f = pd.DataFrame({"date": df["date"]})
f["ret1"] = df["ret"]
f["ret2"] = df["close"].pct_change(2)
f["ret3"] = df["close"].pct_change(3)
f["ret5"] = df["close"].pct_change(5)
f["ret10"] = df["close"].pct_change(10)
f["ma5v"] = df["ma5"] / df["close"] - 1
f["ma20v"] = df["ma20"] / df["close"] - 1
f["ma60v"] = df["ma60"] / df["close"] - 1
f["rsi"] = df["rsi12"] / 100 - 0.5
f["macd"] = df["macd_hist"] / df["close"] * 100
f["volz"] = (df["volume"] - df["vol_ma5"]) / (df["vol_ma5"] + 1e-9)
f["atr"] = df["atr14"] / df["close"] * 100
f["target"] = df["close"].shift(-5) / df["close"] - 1
feats = ["ret1", "ret2", "ret3", "ret5", "ret10", "ma5v", "ma20v", "ma60v", "rsi", "macd", "volz", "atr"]
Vf = f.dropna(subset=feats).reset_index(drop=True)
X = Vf[feats].values
T = Vf["target"].values
n = len(Vf)
EVAL = 250
start = n - EVAL


def ridge_fit(i):
    """用截至第 i 日已实现的样本训练（j 需满足 j+5<=i，无未来函数）"""
    tr_idx = np.arange(0, i - 4)
    tr_idx = tr_idx[np.isfinite(T[tr_idx])]
    Xtr, ytr = X[tr_idx], T[tr_idx]
    mu = Xtr.mean(0)
    sd = Xtr.std(0)
    sd[sd < 1e-12] = 1.0
    Xs = (Xtr - mu) / sd
    yc = ytr - ytr.mean()
    A = Xs.T @ Xs + np.eye(len(feats))  # 标准化后 λ=1
    w = np.linalg.solve(A, Xs.T @ yc)
    return w, mu, sd, float(ytr.mean())


P, A_, D_, RET1_ = [], [], [], []
for i in range(start, n):
    if not np.isfinite(T[i]):
        continue
    w, mu, sd, ybar = ridge_fit(i)
    p = (X[i] - mu) / sd @ w + ybar
    P.append(p)
    A_.append(T[i])
    D_.append(Vf["date"].iloc[i])
    RET1_.append(X[i, 0])

P, A_ = np.array(P), np.array(A_)
acc = float(np.mean(np.sign(P) == np.sign(A_)))
base_up = float(np.mean(A_ > 0))
base_persist = float(np.mean(np.sign(np.array(RET1_)) == np.sign(A_)))
mae = float(np.mean(np.abs(P - A_)))
corr = float(np.corrcoef(P, A_)[0, 1]) if P.std() > 0 and A_.std() > 0 else None

w, mu, sd, ybar = ridge_fit(n - 1)
p_live = float((X[n - 1] - mu) / sd @ w + ybar)
pd.DataFrame({"date": pd.to_datetime(D_), "pred": P, "actual": A_}).to_csv(DATA / "wf_predictions.csv", index=False)
ml = {
    "features": feats,
    "eval_days": int(len(P)),
    "acc_pct": round(acc * 100, 2),
    "baseline_up_pct": round(base_up * 100, 2),
    "baseline_persist_pct": round(base_persist * 100, 2),
    "beats_baseline": bool(acc > max(base_up, base_persist)),
    "mae_pct": round(mae * 100, 3),
    "corr": round(corr, 3) if corr is not None else None,
    "live_pred_5d_pct": round(p_live * 100, 2),
    "live_dir": "看多" if p_live > 0 else "看空",
}

# ================= 3. 回测验证 =================
CAP = 1_000_000.0          # 贵州茅台一手约13万+，10万资金无法成交整手，故用100万
FEE_BUY = 0.00025          # 佣金 万2.5（最低5元另计）
FEE_SELL = 0.00025 + 0.0005  # 佣金 + 印花税0.05%（卖出）
SLIP = 0.0005              # 滑点 0.05%

i0 = int(df["ma60"].first_valid_index())
bt = df.iloc[i0:].reset_index(drop=True)
sigA = (bt["ma5"] > bt["ma20"]).astype(int).values
sigB = ((bt["ma5"] > bt["ma20"]) & (bt["close"] > bt["ma60"])).astype(int).values


def run_backtest(sig, dfo):
    opens, closes, dates = dfo["open"].values, dfo["close"].values, dfo["date"].tolist()
    cash, sh = CAP, 0
    entry_px = entry_i = entry_fee = None
    eq = np.empty(len(dfo))
    pos = np.zeros(len(dfo), dtype=int)
    trades = []
    for t in range(len(dfo)):
        if t > 0:
            s = sig[t - 1]  # 前一日收盘信号，当日开盘执行（T+1）
            if sh == 0 and s == 1:
                px = opens[t] * (1 + SLIP)
                n_sh = int(cash / (px * (1 + FEE_BUY)) // 100) * 100
                while n_sh > 0 and cash - n_sh * px - max(5.0, n_sh * px * FEE_BUY) < 0:
                    n_sh -= 100
                if n_sh > 0:
                    amt = n_sh * px
                    fee = max(5.0, amt * FEE_BUY)
                    cash -= amt + fee
                    sh, entry_px, entry_i, entry_fee = n_sh, px, t, fee
            elif sh > 0 and s == 0:
                px = opens[t] * (1 - SLIP)
                amt = sh * px
                fee = max(5.0, amt * FEE_SELL)
                cash += amt - fee
                pnl = sh * px - sh * entry_px - entry_fee - fee
                base = sh * entry_px + entry_fee
                trades.append({
                    "entry_date": str(dates[entry_i].date()), "exit_date": str(dates[t].date()),
                    "entry_price": round(float(entry_px), 2), "exit_price": round(float(px), 2),
                    "shares": int(sh), "pnl": round(float(pnl), 0),
                    "ret_pct": round(float(pnl / base) * 100, 2), "hold_days": t - entry_i,
                })
                sh = 0
        eq[t] = cash + sh * closes[t]
        pos[t] = 1 if sh > 0 else 0
    if sh > 0:  # 期末未平仓，按收盘价估值
        px = closes[-1]
        pnl = sh * px - sh * entry_px - entry_fee
        base = sh * entry_px + entry_fee
        trades.append({
            "entry_date": str(dates[entry_i].date()), "exit_date": "(未平仓)",
            "entry_price": round(float(entry_px), 2), "exit_price": round(float(px), 2),
            "shares": int(sh), "pnl": round(float(pnl), 0),
            "ret_pct": round(float(pnl / base) * 100, 2), "hold_days": len(dates) - 1 - entry_i,
        })
    return eq, trades, pos


def trade_stats(trades):
    closed = [t for t in trades if t["exit_date"] != "(未平仓)"]
    rets = [t["ret_pct"] for t in closed]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses else None
    return {
        "n_closed": len(closed), "n_open": len(trades) - len(closed),
        "win_rate_pct": round(len(wins) / len(rets) * 100, 1) if rets else None,
        "avg_win_pct": round(float(np.mean(wins)), 2) if wins else None,
        "avg_loss_pct": round(float(np.mean(losses)), 2) if losses else None,
        "profit_factor": round(pf, 2) if pf is not None else None,
        "avg_hold_days": round(float(np.mean([t["hold_days"] for t in closed])), 1) if closed else None,
    }


def perf_stats(eq, dates, pos):
    eq = np.asarray(eq, dtype=float)
    r = np.diff(eq) / eq[:-1]
    days = (pd.Timestamp(dates[-1]) - pd.Timestamp(dates[0])).days
    total = eq[-1] / eq[0] - 1
    cagr = (eq[-1] / eq[0]) ** (365.0 / days) - 1 if days > 30 else None
    vol = float(r.std(ddof=1) * np.sqrt(252))
    sharpe = float(r.mean() * 252 / vol) if vol > 1e-9 else None
    peak = np.maximum.accumulate(eq)
    mdd = float((eq / peak - 1).min())
    return {
        "final_equity": round(float(eq[-1]), 0),
        "total_return_pct": round(total * 100, 2),
        "cagr_pct": round(cagr * 100, 2) if cagr is not None else None,
        "ann_vol_pct": round(vol * 100, 2),
        "sharpe": round(sharpe, 2) if sharpe is not None else None,
        "max_drawdown_pct": round(mdd * 100, 2),
        "exposure_pct": round(float(np.mean(pos)) * 100, 1),
    }


eqA, trA, posA = run_backtest(sigA, bt)
eqB, trB, posB = run_backtest(sigB, bt)
px0 = bt["open"].iloc[0] * (1 + SLIP)
n_bh = int(CAP / (px0 * (1 + FEE_BUY)) // 100) * 100
cash_bh = CAP - n_bh * px0 - max(5.0, n_bh * px0 * FEE_BUY)
eqBH = cash_bh + n_bh * bt["close"].values
posBH = np.ones(len(bt))

pd.DataFrame({"date": bt["date"].dt.date.astype(str), "strategyA": eqA, "strategyB": eqB, "buy_hold": eqBH}) \
    .to_csv(DATA / "backtest_equity.csv", index=False)
pd.DataFrame(trA + [{**t, "strategy": "B"} for t in []]).to_csv(DATA / "backtest_trades_A.csv", index=False)
pd.DataFrame(trB).to_csv(DATA / "backtest_trades_B.csv", index=False)

btA = perf_stats(eqA, bt["date"].tolist(), posA)
btB = perf_stats(eqB, bt["date"].tolist(), posB)
btBH = perf_stats(eqBH, bt["date"].tolist(), posBH)
tsA, tsB = trade_stats(trA), trade_stats(trB)
bt_period = {"start": str(bt["date"].iloc[0].date()), "end": str(bt["date"].iloc[-1].date()),
             "days": int(len(bt))}
bt_assumptions = {
    "initial_capital": CAP, "signal": "收盘计算，次日开盘执行（T+1）",
    "commission": "万2.5/边，最低5元", "stamp_tax": "卖出0.05%",
    "slippage": "0.05%", "lot": "100股整手", "position": "全仓进出，无杠杆，无止损",
    "price_basis": "前复权价（分红已折入价格）",
}

# ================= 4. 快照 / 建议 / 汇总 =================
last = df.iloc[-1]
ma5, ma10, ma20, ma60 = (float(last[k]) for k in ("ma5", "ma10", "ma20", "ma60"))
close = float(last["close"])
dif, dea, hist = float(last["dif"]), float(last["dea"]), float(last["macd_hist"])
rsi6, rsi12, rsi24 = (float(last[k]) for k in ("rsi6", "rsi12", "rsi24"))
k_, d_, j_ = float(last["kdj_k"]), float(last["kdj_d"]), float(last["kdj_j"])
bu, bm, bl = float(last["boll_up"]), float(last["boll_mid"]), float(last["boll_low"])
bw = float(last["boll_width"])
bwp = float((df["boll_width"].iloc[-244:] <= bw).mean() * 100)
atr = float(last["atr14"])
vr = float(last["volume"] / last["vol_ma5"])
hi52, lo52 = float(last["hi52w"]), float(last["lo52w"])
pos52 = (close - lo52) / (hi52 - lo52) * 100
sup60 = float(df["low"].iloc[-60:].min())
res60 = float(df["high"].iloc[-60:].max())
ma20_slope = ma20 - float(df["ma20"].iloc[-6])

ma_align = "多头排列(MA5>MA10>MA20)" if ma5 > ma10 > ma20 else (
    "空头排列(MA5<MA10<MA20)" if ma5 < ma10 < ma20 else "均线交叉纠缠")
macd_state = ("金叉运行" if dif > dea else "死叉运行") + ("、柱体放大" if abs(hist) > abs(float(df["macd_hist"].iloc[-2])) else "、柱体收敛")
rsi_state = "偏超买(>70)" if rsi6 > 70 else ("偏超卖(<30)" if rsi6 < 30 else "中性区(30~70)")
kdj_state = "超买区(J>100)" if j_ > 100 else ("超卖区(J<0)" if j_ < 0 else ("K线在D线上方" if k_ > d_ else "K线在D线下方"))
boll_pos = "上轨上方" if close > bu else ("下轨下方" if close < bl else f"带内，距中轨{(close / bm - 1) * 100:+.2f}%")

trend = "上行" if (close > ma60 and ma20_slope > 0) else ("下行" if (close < ma60 and ma20_slope < 0) else "震荡")
trend_state = {
    "上行": "趋势结构偏多：价格站上MA60且MA20向上",
    "下行": "趋势结构偏空：价格位于MA60下方且MA20向下",
    "震荡": "趋势结构中性：方向信号互相矛盾，属震荡格局",
}[trend]

levels = {
    "支撑": round(sup60, 2),
    "压力": round(res60, 2),
    "止损参考": round(close - 2 * atr, 2),
    "ATR(14)": round(atr, 2),
}

advice_bullets = []
if trend == "上行":
    advice_bullets.append("顺势为主：持仓可继续持有，回调至MA10–MA20一带（当前约 %.0f–%.0f 元）且缩量企稳时视为低吸观察位。" % (min(ma10, ma20), max(ma10, ma20)))
elif trend == "下行":
    advice_bullets.append("防守为主：空仓者不急于抄底，反弹至MA20压力带（约 %.0f 元附近）考虑减仓；未持仓者等待趋势企稳信号。" % ma20)
else:
    advice_bullets.append("区间思路：参考60日支撑/压力（%.0f / %.0f 元）高抛低吸，突破区间并放量确认前控制总仓位。" % (sup60, res60))
if hist > 0 and dif > dea:
    advice_bullets.append("动量偏多：MACD 金叉且红柱运行，短线顺势交易胜率相对更高，但仍需防高位钝化。")
elif hist < 0 and dif < dea:
    advice_bullets.append("动量偏空：MACD 死叉且绿柱运行，反弹以修复性质对待，避免追高。")
else:
    advice_bullets.append("动量信号混杂：MACD 方向与柱体不一致，建议以日线级别小仓位试错、快进快出。")
if rsi6 > 70:
    advice_bullets.append("短线偏热：RSI6 已进入超买区，追高风险大于机会，可分批兑现浮盈。")
elif rsi6 < 30:
    advice_bullets.append("短线偏冷：RSI6 进入超卖区，急跌后存在技术性反抽需求，但需右侧确认。")
advice_discipline = [
    "仓位：单一标的建议不超过总资金的 20%–30%，避免全仓押注单一信号。",
    "止损：以 2×ATR（约 %.2f 元，即收盘下方约 %.1f%%）作为移动止损参考，跌破果断执行。" % (levels["止损参考"], (2 * atr / close) * 100),
    "执行：A股 T+1，隔夜跳空与停牌风险无法用日内止损规避，仓位即为风控的第一道闸。",
    "纪律：本报告所有信号均基于历史统计，实际执行前应结合基本面与自身风险承受能力独立决策。",
]

ov = {
    "first_date": str(df["date"].iloc[0].date()), "last_date": str(df["date"].iloc[-1].date()),
    "first_close": round(float(df["close"].iloc[0]), 2), "last_close": round(close, 2),
    "period_return_pct": round((close / float(df["close"].iloc[0]) - 1) * 100, 2),
    "max_high": round(float(df["high"].max()), 2),
    "max_high_date": str(df.loc[df["high"].idxmax(), "date"].date()),
    "min_low": round(float(df["low"].min()), 2),
    "min_low_date": str(df.loc[df["low"].idxmin(), "date"].date()),
    "avg_volume": int(df["volume"].mean()),
    "avg_amount_yi": round(float(df["amount"].mean()) / 1e8, 2) if df["amount"].notna().any() else None,
    "avg_turnover_pct": round(float(df["turnover"].mean()), 2) if df["turnover"].notna().any() else None,
    "ann_vol_20d_pct": round(float(last["vol20_ann"]) * 100, 2),
}

ind_table = [
    ["MA5 / MA10 / MA20 / MA60", f"{ma5:.2f} / {ma10:.2f} / {ma20:.2f} / {ma60:.2f}", ma_align],
    ["MACD(12,26,9)", f"DIF {dif:.2f}｜DEA {dea:.2f}｜柱 {hist:.2f}", macd_state],
    ["RSI(6/12/24)", f"{rsi6:.1f} / {rsi12:.1f} / {rsi24:.1f}", rsi_state],
    ["KDJ(9,3,3)", f"K {k_:.1f}｜D {d_:.1f}｜J {j_:.1f}", kdj_state],
    ["BOLL(20,2)", f"上 {bu:.2f}｜中 {bm:.2f}｜下 {bl:.2f}", f"{boll_pos}；带宽{bw * 100:.1f}%（近1年分位 {bwp:.0f}%）"],
    ["ATR(14)", f"{atr:.2f}（占价比 {atr / close * 100:.2f}%）", "日均真实波幅，用于止损定位"],
    ["量能", f"量比(今/5日均) {vr:.2f}", "放量" if vr > 1.2 else ("缩量" if vr < 0.8 else "量能平稳")],
    ["52周区间", f"{lo52:.2f} ~ {hi52:.2f}", f"现价位于52周区间 {pos52:.0f}% 分位"],
]

summary = [
    f"数据：{meta['name']}({meta['code']}) {meta['fq']}日线 {ov['first_date']} ~ {ov['last_date']} 共 {meta['rows']} 个交易日，区间累计涨跌 {ov['period_return_pct']:+.2f}%。",
    f"最新收盘 {ov['last_close']} 元（{ov['last_date']}），{ma_align}，价格相对MA20 {(close / ma20 - 1) * 100:+.2f}%、相对MA60 {(close / ma60 - 1) * 100:+.2f}%。",
    f"动量：MACD {macd_state}；RSI6={rsi6:.1f}（{rsi_state}）；KDJ {kdj_state}；20日年化波动率 {ov['ann_vol_20d_pct']}%。",
    f"预测：模型B walk-forward 方向准确率 {ml['acc_pct']}%（基线 最高{max(ml['baseline_up_pct'], ml['baseline_persist_pct'])}%），{'具备' if ml['beats_baseline'] else '不具备'}稳定预测边际；当前5日方向预测：{ml['live_dir']}（{ml['live_pred_5d_pct']:+.2f}%）。",
    f"回测（{bt_period['start']}~{bt_period['end']}）：策略A总收益 {btA['total_return_pct']:+.2f}%/回撤 {btA['max_drawdown_pct']:.2f}%；策略B {btB['total_return_pct']:+.2f}%/{btB['max_drawdown_pct']:.2f}%；买入持有 {btBH['total_return_pct']:+.2f}%/{btBH['max_drawdown_pct']:.2f}%。",
    f"操作参考：{trend_state}；关键位 支撑 {levels['支撑']} / 压力 {levels['压力']} / 止损参考 {levels['止损参考']}。",
    "声明：本报告由历史数据自动生成，仅供研究演示，不构成任何投资建议。",
]

results = {
    "meta": meta, "overview": ov, "snapshot_indicators": ind_table,
    "prediction": {"lr": lr, "ml": ml},
    "backtest": {"period": bt_period, "assumptions": bt_assumptions,
                 "strategyA": btA, "strategyB": btB, "buy_hold": btBH,
                 "trades_A": tsA, "trades_B": tsB},
    "advice": {"trend": trend, "trend_state": trend_state, "bullets": advice_bullets,
               "discipline": advice_discipline, "levels": levels},
    "summary": summary,
}
(OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print("OK: results.json")
print(f"ML acc={ml['acc_pct']}% vs base={ml['baseline_up_pct']}/{ml['baseline_persist_pct']}% | "
      f"A {btA['total_return_pct']}% MDD {btA['max_drawdown_pct']}% | "
      f"B {btB['total_return_pct']}% MDD {btB['max_drawdown_pct']}% | "
      f"BH {btBH['total_return_pct']}% MDD {btBH['max_drawdown_pct']}%")
