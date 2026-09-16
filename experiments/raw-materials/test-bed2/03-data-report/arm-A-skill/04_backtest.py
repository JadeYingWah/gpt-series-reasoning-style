# -*- coding: utf-8 -*-
"""
04 回测验证：MA10/MA30 双均线金叉死叉策略 vs 买入持有
口径:
  - 标的: 贵州茅台 600519, 前复权日线, 2020-01-02 ~ 2026-09-16
  - 信号: MA10 上穿 MA30 金叉 → 持有; 下穿 死叉 → 清仓 (全仓进出, 长多)
  - 正确版成交: 信号出现后的下一交易日开盘价 (无前视)
  - 负对照版成交: 信号当日收盘价判信号、当日开盘价成交 —— 经典前视偏差,
    用于量化"前视偏差虚增收益"(审查面第4条: 把要防的错误故意做一次, 看指标变红)
  - 成本: 佣金 0.025% 双边 + 印花税 0.05% 仅卖出 + 滑点 0.1% 双边
指标: 总收益 / CAGR / 年化波动 / 夏普(rf=0) / 最大回撤 / Calmar / 胜率 / 交易次数 / 露头比例
关键数字重算(审查面第5条): 两套独立实现 ——
  (a) 向量化: 用 position 序列 × 次日收益率 累乘
  (b) 逐bar账本: 现金/持股逐日结算(含成本)
  两者期末净值必须一致(相对误差 < 1e-6), 否则报错。
"""
import json
import math
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

COMMISSION = 0.00025   # 佣金 双边
STAMP_TAX = 0.0005     # 印花税 仅卖出 (2023-08-28 起 0.05%)
SLIPPAGE = 0.001       # 滑点 双边
BUY_COST = COMMISSION + SLIPPAGE            # 买入附加成本率
SELL_COST = COMMISSION + STAMP_TAX + SLIPPAGE  # 卖出附加成本率

FAST, SLOW = 10, 30


def load():
    df = pd.read_csv(os.path.join(DATA, "600519_daily_qfq.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def gen_signals(df):
    ma_f = df["close"].rolling(FAST).mean()
    ma_s = df["close"].rolling(SLOW).mean()
    above = (ma_f > ma_s).astype(int)
    cross = above.diff()
    # +1 金叉, -1 死叉, 0 无
    sig = pd.Series(0, index=df.index)
    sig[cross == 1] = 1
    sig[cross == -1] = -1
    return sig, ma_f, ma_s


def backtest_correct(df, sig):
    """正确版: 信号次日开盘成交。向量化实现。
    position[i] = 第 i 日收盘时的目标仓位(0/1)。金叉信号 sig[i]=+1 → position[i+1..] = 1 (从 i+1 开盘买入)。
    收益链: r[i] = close[i]/close[i-1]-1 中, 持仓日的收益归属于 position[i-1] (i-1 收盘已建仓)。
    实际以开盘价成交, 与"以 i 日开盘买入、i 日收盘价计值"一致:
      当日贡献 = close[i]*(1-SELL_COST... ) 复杂; 简化口径: 以开盘价成交, 当日起按收盘计值。
      精确逐bar账本在 backtest_ledger 中实现; 向量化版按 开盘成交价/前收 计算当日成交腿。
    """
    n = len(df)
    pos = np.zeros(n)
    cur = 0
    open_px = df["open"].values
    close_px = df["close"].values
    for i in range(n - 1):
        if sig[i] == 1:
            cur = 1
        elif sig[i] == -1:
            cur = 0
        pos[i + 1] = cur
    # 净值: 无仓日 r=0; 持仓日 r=close[i]/close[i-1]-1; 换仓日的成交腿按开盘价与成本修正
    nav = np.ones(n)
    equity = 1.0
    trades = []
    pending = None  # (i+1, 'buy'/'sell')
    for i in range(1, n):
        r = 0.0
        if pending is not None:
            j, action = pending
            if j == i:  # 今日开盘执行
                if action == "buy":
                    buy_px = open_px[i] * (1 + BUY_COST)
                    # 当日持仓收益 = close[i]/buy_px - 1
                    r = close_px[i] / buy_px - 1
                    trades.append({"date": df["date"].iloc[i], "action": "buy", "price": float(open_px[i])})
                else:
                    # 昨收至今持有一晚? 无仓后无收益; 卖出腿: close[i-1] → open[i]*(1-SELL_COST)
                    r = open_px[i] * (1 - SELL_COST) / close_px[i - 1] - 1
                    trades.append({"date": df["date"].iloc[i], "action": "sell", "price": float(open_px[i])})
                pending = None
        elif pos[i] == 1 and pos[i - 1] == 1:
            r = close_px[i] / close_px[i - 1] - 1
        # 建仓信号记录 (次日执行)
        if sig[i] == 1:
            pending = (i + 1, "buy")
        elif sig[i] == -1:
            pending = (i + 1, "sell")
        equity *= (1 + r)
        nav[i] = equity
    return nav, trades


def backtest_lookahead(df, sig):
    """负对照(前视偏差): 信号日开盘价成交 —— 用了当日收盘才能算出的信号, 在当日开盘执行。
    即比正确版提前一天入场/离场, 捕捉信号日当天的涨跌。"""
    n = len(df)
    open_px = df["open"].values
    close_px = df["close"].values
    nav = np.ones(n)
    equity = 1.0
    trades = []
    holding = False
    for i in range(1, n):
        r = 0.0
        if sig[i] == 1 and not holding:
            # 前视: 当日收盘才可知的金叉, 当日开盘即买入
            buy_px = open_px[i] * (1 + BUY_COST)
            r = close_px[i] / buy_px - 1
            trades.append({"date": df["date"].iloc[i], "action": "buy", "price": float(open_px[i])})
            holding = True
        elif sig[i] == -1 and holding:
            sell_px = open_px[i] * (1 - SELL_COST)
            r = sell_px / close_px[i - 1] - 1
            trades.append({"date": df["date"].iloc[i], "action": "sell", "price": float(open_px[i])})
            holding = False
        elif holding:
            r = close_px[i] / close_px[i - 1] - 1
        equity *= (1 + r)
        nav[i] = equity
    return nav, trades


def backtest_ledger(df, sig):
    """独立重算实现(b): 逐bar现金/股数账本, 次日开盘成交, 含成本。用于与向量化版对账。"""
    n = len(df)
    cash = 1.0
    shares = 0.0
    open_px = df["open"].values
    close_px = df["close"].values
    nav = np.ones(n)
    trades = 0
    pending = None
    for i in range(n):
        if pending is not None:
            j, action = pending
            if j == i:
                if action == "buy":
                    px = open_px[i] * (1 + BUY_COST)
                    shares = cash / px
                    cash = 0.0
                    trades += 1
                else:
                    px = open_px[i] * (1 - SELL_COST)
                    cash = shares * px
                    shares = 0.0
                    trades += 1
                pending = None
        if i + 1 < n and sig[i] in (1, -1):
            pending = (i + 1, "buy" if sig[i] == 1 else "sell")
        nav[i] = cash + shares * close_px[i]
    return nav, trades


def metrics(nav, dates, trades_list):
    nav = np.asarray(nav, dtype=float)
    n = len(nav)
    years = n / 244.0  # A股年均交易日约243-244
    total_ret = nav[-1] / nav[0] - 1
    cagr = (nav[-1] / nav[0]) ** (1 / years) - 1
    r = nav[1:] / nav[:-1] - 1
    vol = float(r.std(ddof=1) * math.sqrt(244))
    sharpe = float((r.mean() * 244) / (r.std(ddof=1) * math.sqrt(244))) if r.std(ddof=1) > 0 else 0.0
    peak = np.maximum.accumulate(nav)
    dd = nav / peak - 1
    mdd = float(dd.min())
    calmar = float(cagr / abs(mdd)) if mdd < 0 else 0.0
    # 胜率: 每对买卖(buy→sell)的盈亏
    wins, pairs = 0, 0
    entry_px = None
    for t in trades_list:
        if t["action"] == "buy":
            entry_px = t["price"]
        elif t["action"] == "sell" and entry_px is not None:
            pairs += 1
            if t["price"] > entry_px:
                wins += 1
            entry_px = None
    exposure = float((nav[1:] != nav[:-1]).mean())  # 近似: 净值变动日比例
    # 精确露头: 重算
    return {
        "total_return": round(total_ret, 4),
        "cagr": round(cagr, 4),
        "annual_vol": round(vol, 4),
        "sharpe_rf0": round(sharpe, 3),
        "max_drawdown": round(mdd, 4),
        "calmar": round(calmar, 3),
        "trades": len(trades_list),
        "round_trips": pairs,
        "win_rate": round(wins / pairs, 3) if pairs else None,
        "exposure_approx": round(exposure, 3),
        "start": str(dates.iloc[0].date()),
        "end": str(dates.iloc[-1].date()),
    }


def main():
    df = load()
    sig, ma_f, ma_s = gen_signals(df)
    df["MA10"] = ma_f
    df["MA30"] = ma_s

    nav_ok, trades_ok = backtest_correct(df, sig)
    nav_la, trades_la = backtest_lookahead(df, sig)
    nav_ledger, trades_ledger = backtest_ledger(df, sig)

    # 关键数字重算: 向量化 vs 逐bar账本
    rel_diff = abs(nav_ok[-1] - nav_ledger[-1]) / nav_ledger[-1]
    assert rel_diff < 1e-6, f"两套实现期末净值不一致: {nav_ok[-1]} vs {nav_ledger[-1]} rel={rel_diff}"

    m_ok = metrics(nav_ok, df["date"], trades_ok)
    m_la = metrics(nav_la, df["date"], trades_la)

    # 买入持有基准 (首日开盘买入, 含成本; 期末不卖出以免虚减 — 注明口径)
    bh = df["close"].values / (df["open"].values[0] * (1 + BUY_COST))
    m_bh = metrics(bh, df["date"], [])

    out = {
        "params": {
            "fast": FAST, "slow": SLOW,
            "buy_cost_rate": BUY_COST, "sell_cost_rate": SELL_COST,
            "cost_note": "佣金0.025%双边+印花税0.05%卖出+滑点0.1%双边; 前复权价; 年化按244交易日",
        },
        "correct_next_open": m_ok,
        "lookahead_same_open": m_la,
        "buy_and_hold": m_bh,
        "dual_implementation_check": {
            "vectorized_final_nav": round(float(nav_ok[-1]), 8),
            "ledger_final_nav": round(float(nav_ledger[-1]), 8),
            "relative_diff": float(rel_diff),
            "pass": bool(rel_diff < 1e-6),
        },
        "lookahead_inflation": {
            "total_return_diff": round(m_la["total_return"] - m_ok["total_return"], 4),
            "note": "负对照: 前视偏差版(信号日开盘成交)比正确版(次日开盘成交)虚增的收益",
        },
    }
    with open(os.path.join(DATA, "backtest_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    eq = pd.DataFrame({
        "date": df["date"].dt.strftime("%Y-%m-%d"),
        "nav_strategy": nav_ok,
        "nav_lookahead": nav_la,
        "nav_buyhold": bh,
        "signal": sig,
        "MA10": ma_f, "MA30": ma_s,
        "close": df["close"],
    })
    eq.to_csv(os.path.join(DATA, "600519_backtest_equity.csv"), index=False)

    print("[OK] 正确版(次日开盘):", m_ok)
    print("[OK] 负对照(前视偏差):", m_la)
    print("[OK] 买入持有       :", m_bh)
    print(f"[OK] 双实现对账: 相对误差 {rel_diff:.2e} -> {'PASS' if rel_diff < 1e-6 else 'FAIL'}")
    print(f"[OK] 前视偏差虚增收益: {out['lookahead_inflation']['total_return_diff']*100:+.1f} pct")


if __name__ == "__main__":
    main()
