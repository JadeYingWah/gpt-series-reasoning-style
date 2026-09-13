# -*- coding: utf-8 -*-
"""数据探索：行数、时间范围、采样间隔、缺失、基本统计。输出 explore_result.json + 文本摘要。"""
import pandas as pd, numpy as np, json

SRC = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
df = pd.read_csv(SRC)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)

info = {
    "rows": int(len(df)),
    "cols": list(df.columns),
    "time_start": str(df['timestamp'].min()),
    "time_end": str(df['timestamp'].max()),
    "value_dtype": str(df['value'].dtype),
    "missing_timestamp": int(df['timestamp'].isna().sum()),
    "missing_value": int(df['value'].isna().sum()),
    "dup_timestamps": int(df['timestamp'].duplicated().sum()),
}
gaps = df['timestamp'].diff().dropna()
info["median_interval_sec"] = float(gaps.dt.total_seconds().median())
info["interval_counts_top"] = {str(k): int(v) for k, v in gaps.dt.total_seconds().value_counts().head(5).items()}
info["value_stats"] = {k: float(v) for k, v in df['value'].describe().items()}
# 按天看值域，识别低频区段
daily = df.set_index('timestamp')['value'].resample('D').agg(['min', 'max', 'mean', 'count'])
info["daily_summary_head"] = {str(k): v for k, v in daily.head(3).round(2).to_dict('index').items()}
info["daily_summary_tail"] = {str(k): v for k, v in daily.tail(3).round(2).to_dict('index').items()}
with open("explore_result.json", "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=2, default=str)
print(json.dumps(info, ensure_ascii=False, indent=2, default=str))
