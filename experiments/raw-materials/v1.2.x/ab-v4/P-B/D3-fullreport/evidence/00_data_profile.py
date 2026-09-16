# -*- coding: utf-8 -*-
"""数据画像：基础统计与结构检查（方法 A/B/D 的前置步骤）"""
import pandas as pd
import numpy as np
import json

DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
OUT = "<实验根目录>/ab-v4/P-B/D3-fullreport/evidence/00_data_profile.json"

df = pd.read_csv(DATA)
assert list(df.columns) == ["timestamp", "value"], f"列不符: {df.columns}"

ts = pd.to_datetime(df["timestamp"])
v = df["value"].astype(float)

# 时间等间隔性检查
dt = ts.diff().dropna().dt.total_seconds()
profile = {
    "rows": int(len(df)),
    "columns": list(df.columns),
    "time_start": str(ts.iloc[0]),
    "time_end": str(ts.iloc[-1]),
    "time_monotonic_increasing": bool(ts.is_monotonic_increasing),
    "time_unique": bool(ts.is_unique),
    "interval_seconds_median": float(dt.median()),
    "interval_seconds_min": float(dt.min()),
    "interval_seconds_max": float(dt.max()),
    "interval_non_median_count": int((dt != dt.median()).sum()),
    "value_min": float(v.min()),
    "value_max": float(v.max()),
    "value_mean": float(v.mean()),
    "value_median": float(v.median()),
    "value_std": float(v.std()),
    "value_q01": float(v.quantile(0.01)),
    "value_q99": float(v.quantile(0.99)),
    "nan_count": int(v.isna().sum()),
}
# 采样间隔推断
profile["implied_freq"] = f"{int(dt.median())}s"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(profile, f, ensure_ascii=False, indent=2)

print(json.dumps(profile, ensure_ascii=False, indent=2))
