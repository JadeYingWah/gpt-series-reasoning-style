# -*- coding: utf-8 -*-
"""
03 趋势预测模型（概率情景推演, 非确定性预测）
方法:
  M1 对数线性回归: 最近60交易日 ln(close) 对时间 OLS, 外推斜率
  M2 GBM 蒙特卡洛: 最近250交易日对数收益的 mu/sigma, 10000路径 × 20交易日, 固定种子
  M3 长周期回归: 最近250交易日 ln(close) OLS 斜率 (对照)
  M4 随机游走对照: mu=0, 仅 sigma (检验 M2 的漂移项贡献)
输出: data/forecast.json (分位区间 P5/P25/P50/P75/P95 @ 5/10/20日 + 下跌概率)
自检: 滚动起源可信度检验 —— 取 2024-01 至 2026-08 每月末为起源, 用截至起源的数据
      做同样的 GBM 预测, 统计 20 日后真实落点落在 P5~P95 区间内的比例(期望≈90%),
      以及落在 P25~P75 的比例(期望≈50%)。覆盖率显著偏离则说明不确定性带宽不可信。
"""
import json
import math
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
HORIZON = 20
N_PATHS = 10000
SEED = 20260916
TRADING_DAYS = 250


def ols_log_slope(close: pd.Series):
    y = np.log(close.values)
    x = np.arange(len(y), dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    return slope, intercept


def gbm_quantiles(s0, mu_daily, sigma_daily, horizon=HORIZON, n_paths=N_PATHS, seed=SEED):
    rng = np.random.default_rng(seed)
    shocks = rng.standard_normal((n_paths, horizon))
    log_paths = math.log(s0) + np.cumsum(
        (mu_daily - 0.5 * sigma_daily**2) + sigma_daily * shocks, axis=1)
    paths = np.exp(log_paths)
    qs = {}
    for h in (5, 10, 20):
        vals = paths[:, h - 1]
        qs[h] = {f"P{p}": float(np.percentile(vals, p)) for p in (5, 25, 50, 75, 95)}
        qs[h]["P_down"] = float((vals < s0).mean())
    return qs, paths


def rolling_origin_coverage(close: pd.Series, n_origins=20):
    """滚动起源检验: 每个起源用其前250日估 mu/sigma, 预测20日, 看真实值落带比例"""
    closes = close.values
    origins = []
    # 以月末附近的交易日为起源, 从倒数第 (n_origins*21+21) 根开始每隔约21根取一个
    start_idx = len(closes) - (n_origins * 21 + HORIZON + 1)
    for i in range(n_origins):
        t = start_idx + i * 21
        if t < TRADING_DAYS + 1 or t + HORIZON >= len(closes):
            continue
        hist = closes[t - TRADING_DAYS:t]
        rets = np.diff(np.log(hist))
        mu, sigma = rets.mean(), rets.std(ddof=1)
        s0 = closes[t - 1]
        q, _ = gbm_quantiles(s0, mu, sigma, horizon=HORIZON, n_paths=2000, seed=SEED + i)
        actual = closes[t - 1 + HORIZON]
        origins.append({
            "origin_idx": int(t),
            "s0": float(s0),
            "actual_20d": float(actual),
            "in_P5_P95": bool(q[20]["P5"] <= actual <= q[20]["P95"]),
            "in_P25_P75": bool(q[20]["P25"] <= actual <= q[20]["P75"]),
        })
    cov90 = sum(o["in_P5_P95"] for o in origins) / len(origins)
    cov50 = sum(o["in_P25_P75"] for o in origins) / len(origins)
    return origins, cov90, cov50


def main():
    df = pd.read_csv(os.path.join(DATA, "600519_daily_qfq.csv"))
    df = df.sort_values("date").reset_index(drop=True)
    c = df["close"]
    s0 = float(c.iloc[-1])
    as_of = df["date"].iloc[-1]

    # ---- 参数估计 ----
    rets250 = np.diff(np.log(c.values[-TRADING_DAYS - 1:]))
    mu250, sigma250 = float(rets250.mean()), float(rets250.std(ddof=1))
    rets60 = np.diff(np.log(c.values[-61:]))
    sigma60 = float(rets60.std(ddof=1))

    # ---- M1: 60日对数线性外推 ----
    slope60, intercept60 = ols_log_slope(c.iloc[-60:])
    # ---- M3: 250日对数线性外推 ----
    slope250, _ = ols_log_slope(c.iloc[-250:])

    # ---- M2/M4: 蒙特卡洛 ----
    q_gbm, _ = gbm_quantiles(s0, mu250, sigma250)
    q_rw, _ = gbm_quantiles(s0, 0.0, sigma250, seed=SEED + 1)

    # ---- M1/M3 点预测 (外推 HORIZON 日) ----
    m1 = {h: float(math.exp(intercept60 + slope60 * (59 + h))) for h in (5, 10, 20)}
    m3 = {h: float(math.exp(slope250 * (249 + h) + np.log(s0) - slope250 * 249)) for h in (5, 10, 20)}

    # ---- 滚动起源可信度检验 ----
    origins, cov90, cov50 = rolling_origin_coverage(c)

    result = {
        "as_of": as_of,
        "s0": s0,
        "horizon_trading_days": HORIZON,
        "model_params": {
            "mu_daily_250d": round(mu250, 6),
            "sigma_daily_250d": round(sigma250, 6),
            "sigma_annualized_250d": round(sigma250 * math.sqrt(TRADING_DAYS), 4),
            "sigma_daily_60d": round(sigma60, 6),
            "ols_log_slope_60d": round(slope60, 6),
            "ols_log_slope_250d": round(slope250, 6),
        },
        "M2_gbm_quantiles": q_gbm,
        "M4_random_walk_quantiles": q_rw,
        "M1_linear60_point": m1,
        "M3_linear250_point": m3,
        "rolling_origin_check": {
            "n_origins": len(origins),
            "coverage_P5_P95": round(cov90, 3),
            "coverage_P25_P75": round(cov50, 3),
            "expected_P5_P95": 0.9,
            "expected_P25_P75": 0.5,
            "detail": origins,
        },
        "disclaimer": "以上为概率情景推演而非确定性预测; 参数由历史估计, 未来分布可能变化。",
    }
    with open(os.path.join(DATA, "forecast.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[OK] 截面 {as_of} 收盘 {s0}")
    print(f"[OK] 年化波动率 {result['model_params']['sigma_annualized_250d']*100:.1f}%")
    print(f"[OK] GBM 20日: P5={q_gbm[20]['P5']:.0f} P25={q_gbm[20]['P25']:.0f} "
          f"P50={q_gbm[20]['P50']:.0f} P75={q_gbm[20]['P75']:.0f} P95={q_gbm[20]['P95']:.0f} "
          f"P(下跌)={q_gbm[20]['P_down']*100:.1f}%")
    print(f"[OK] M1线性60日外推 20日: {m1[20]:.0f} | M3线性250日外推: {m3[20]:.0f}")
    print(f"[OK] 滚动起源检验: {len(origins)} 个起源, P5~P95 覆盖率 {cov90*100:.0f}% (期望90%), "
          f"P25~P75 覆盖率 {cov50*100:.0f}% (期望50%)")


if __name__ == "__main__":
    main()
