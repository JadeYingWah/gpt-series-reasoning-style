# -*- coding: utf-8 -*-
"""可视化证据：全序列 + 主报告区段(红) + 附录候选区段(橙)。输出 detection_overview.png"""
import pandas as pd, numpy as np, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

SRC = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
df = pd.read_csv(SRC); df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)

cons = json.load(open("consensus_result.json"))

fig, ax = plt.subplots(figsize=(16, 6))
ax.plot(df['timestamp'], df['value'], lw=0.5, color="#3a6ea5")
for p in cons["primary"]:
    ax.axvspan(pd.Timestamp(p["start"]), pd.Timestamp(p["end"]), color="red", alpha=0.30,
               label="PRIMARY (consensus)" if "PRIMARY (consensus)" not in [l.get_label() for l in ax.get_children() if hasattr(l,'get_label')] else None)
for a in cons["appendix"]:
    if "start" in a and "end" in a:
        try:
            ax.axvspan(pd.Timestamp(a["start"]), pd.Timestamp(a["end"]), color="orange", alpha=0.35)
        except Exception:
            pass
ax.set_title("NAB machine temperature - anomaly detection overview (red=primary consensus, orange=appendix candidates)")
ax.set_ylabel("temperature (F)")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax.grid(alpha=0.3)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="red", alpha=0.3, label="PRIMARY (>=2 methods, strict)"),
                   Patch(color="orange", alpha=0.35, label="appendix candidates (single method / loose)")], loc="lower left")
plt.tight_layout()
plt.savefig("detection_overview.png", dpi=140)
print("saved detection_overview.png")
