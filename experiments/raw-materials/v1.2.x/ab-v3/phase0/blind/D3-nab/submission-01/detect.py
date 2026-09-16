# -*- coding: utf-8 -*-
r"""D3 时序异常检测：NAB machine temperature（<实验根目录>\ab-v3\datasets\nab_machine_temp.csv）
方法：Hampel 滤波器（居中滑动窗口的稳健 z-score）
  - 滑动中位数 m_t、滑动 MAD_t（乘 1.4826 近似标准差）
  - z_t = (x_t - m_t) / (1.4826 * MAD_t)
  - |z_t| > K 判为异常点；相邻异常点合并为段；段间隔 <= GAP 点再合并为同一异常区段
窗口 ±72 点（6 小时）：跟随日内周期与缓慢漂移，避免正常周期峰谷误判。
阈值敏感性：K=5.5/6.0/6.5/7.0 对比，主事件在 6.0~7.0 间稳定；取 K=6.0。
"""
import pandas as pd
import numpy as np

DATA = r"<实验根目录>\ab-v3\datasets\nab_machine_temp.csv"
OUT  = r"<实验根目录>\ab-v3\phase0\D3-nab\SUB\anomalies.csv"

W, K, GAP = 72, 6.0, 4   # 半窗 72 点=6h；阈值 6.0；段间隔 <=4 点(20min)合并

df = pd.read_csv(DATA, parse_dates=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
s = df["value"].astype(float)

med = s.rolling(2*W+1, center=True, min_periods=2*W+1).median()
mad = (s - med).abs().rolling(2*W+1, center=True, min_periods=2*W+1).median()
z = ((s - med) / (1.4826 * mad)).replace([np.inf, -np.inf], np.nan).fillna(0.0)
df["z"] = z

flag = (z.abs() > K).to_numpy()
idx = np.where(flag)[0]
print(f"K={K}: 异常点数 {len(idx)} / {len(df)}")

# 合并相邻异常点为段
segments = []
if len(idx):
    st = pv = idx[0]
    for i in idx[1:]:
        if i == pv + 1:
            pv = i
        else:
            segments.append((st, pv)); st = pv = i
    segments.append((st, pv))

# 间隔 <= GAP 点的段合并为同一异常区段
merged = []
for seg in segments:
    if merged and seg[0] - merged[-1][1] <= GAP:
        merged[-1] = (merged[-1][0], seg[1])
    else:
        merged.append(list(seg))

rows = []
for a, b in merged:
    zz = z.iloc[a:b+1]
    ext_i = zz.abs().idxmax()           # |z| 最大的点为区段极值点
    is_peak = z.loc[ext_i] > 0
    rows.append({
        "start": df.loc[a, "timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
        "end":   df.loc[b, "timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
        "type":  "peak" if is_peak else "trough",
        "peak_or_trough_value": round(df.loc[ext_i, "value"], 2),
        "extreme_time": df.loc[ext_i, "timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
        "max_abs_z": round(abs(z.loc[ext_i]), 2),
        "n_points": b - a + 1,
    })

res = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print("\n异常区段（间隔<=20min 的检测段已合并）：")
print(res.to_string(index=False))
res.to_csv(OUT, index=False)
print("\n已写出:", OUT)
