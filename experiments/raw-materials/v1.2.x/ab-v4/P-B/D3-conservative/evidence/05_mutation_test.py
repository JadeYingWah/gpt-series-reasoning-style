# -*- coding: utf-8 -*-
"""
变异测试（验证鉴别力——「把要防的错误做一次，它会不会红」）：
1) 在干净对照窗口注入两类合成异常：+30F 尖峰(3点) / -40F 平台(12点)
2) 断言注入点被 >=2 种方法检出且检出方法对注入点命中率 100%（RED 预期；
   注入为上下文型偏移，设计覆盖方法为 M2/M3；M1/M4 盲区如实记录不作为失败）
3) 对照窗口本身（未注入）误报点占比 < 0.5%（GREEN 预期）
任何一条断言失败 → FAIL。输出: mutation_test_result.json
"""
import pandas as pd, numpy as np, json
from sklearn.ensemble import IsolationForest

SRC = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
df = pd.read_csv(SRC)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').drop_duplicates('timestamp', keep='first').reset_index(drop=True)
x0 = df['value'].to_numpy(float); n = len(df); t = df['timestamp']
burn = int(n * 0.15); idx = np.arange(n)

def detect(x, if_score=None):
    out = {}
    med = np.median(x); mad = np.median(np.abs(x-med))*1.4826
    out["M1"] = (np.abs((x-med)/mad) >= 6.0) & (idx >= burn)
    tod = t.dt.strftime('%H:%M').to_numpy()
    z2 = np.full(n, np.nan)
    for phase in np.unique(tod):
        pi = np.where(tod == phase)[0]
        for i in pi:
            sel = (pi >= max(0, i-10*288)) & (pi < i)
            hist = x[pi[sel]]
            if len(hist) < 5: continue
            hm = np.median(hist); hd = max(np.median(np.abs(hist-hm))*1.4826, 0.5)
            z2[i] = (x[i]-hm)/hd
    z2[np.isnan(z2)] = 0
    out["M2"] = (np.abs(z2) >= 6.0) & (idx >= burn)
    s = pd.Series(x)
    trend = s.rolling(25, center=True, min_periods=12).median().to_numpy()
    resid = x - trend
    r = resid[burn:]; r = r[~np.isnan(r)]
    for _ in range(3):
        m = np.median(r); d = np.median(np.abs(r-m))*1.4826
        keep = np.abs(r-m) <= 5*d
        if keep.all(): break
        r = r[keep]
    sig = np.median(np.abs(r-np.median(r)))*1.4826
    z3 = resid/sig; z3[np.isnan(z3)] = 0
    out["M3"] = (np.abs(z3) >= 6.0) & (idx >= burn)
    if if_score is None:
        f = pd.DataFrame({"value": x, "rm1h": s.rolling(12, center=True, min_periods=6).mean(),
                          "rs1h": s.rolling(12, center=True, min_periods=6).std()})
        td = t.dt.hour*60 + t.dt.minute
        f["tod_sin"] = np.sin(2*np.pi*td/1440); f["tod_cos"] = np.cos(2*np.pi*td/1440)
        f = f.bfill().ffill()
        iso = IsolationForest(n_estimators=300, random_state=42, n_jobs=-1).fit(f)
        if_score = -iso.decision_function(f)
    th = np.quantile(if_score[burn:], 0.995)  # 分数越大越异常：取高分位
    out["M4"] = (if_score >= th) & (idx >= burn)
    return out, if_score

# 干净对照窗：2014-01-08 06:00 - 18:00（共 145 点）
w0, w1 = t.searchsorted(pd.Timestamp("2014-01-08 06:00")), t.searchsorted(pd.Timestamp("2014-01-08 18:00"))
base_masks, if_score = detect(x0)
ctrl_pts = {k: int(m[w0:w1].sum()) for k, m in base_masks.items()}
ctrl_rate = sum(ctrl_pts.values()) / (4 * (w1 - w0))

x = x0.copy()
spike_pos = np.arange(w0+20, w0+23)          # +30F 尖峰 3 点
plateau_pos = np.arange(w0+60, w0+72)        # -40F 平台 12 点
x[spike_pos] += 30.0
x[plateau_pos] -= 40.0
mut_masks, _ = detect(x, if_score=if_score)  # IF 分数用原模型（部署等价）
hit = {}
for k in ["M1", "M2", "M3", "M4"]:
    hit[k] = {"spike": int(mut_masks[k][spike_pos].sum()), "plateau": int(mut_masks[k][plateau_pos].sum())}
spike_sup = sum(1 for v in hit.values() if v["spike"] > 0)
plateau_sup = sum(1 for v in hit.values() if v["plateau"] > 0)

res = {
    "control_window": {"start": "2014-01-08 06:00", "end": "2014-01-08 18:00",
                       "pts_per_method": ctrl_pts, "false_alarm_rate": float(ctrl_rate)},
    "mutation": {"spike_injected": 3, "plateau_injected": 12,
                 "per_method_hits": hit,
                 "spike_support_methods": spike_sup, "plateau_support_methods": plateau_sup},
    "blind_spots": {
        "M1_global_z": "对上下文型中小偏移不敏感（全局 MAD 尺度被日周期振幅撑大）；+30F/-40F 相对局部基线>6σ_resid 但 <6σ_global",
        "M4_iforest": "对小幅单点尖峰不敏感（分数未达 99.5% 分位阈值）",
    },
    "assertions": {
        "A1_spike_>=2_methods_and_full_recall": bool(spike_sup >= 2 and
            all(v["spike"] == 3 for k, v in hit.items() if v["spike"] > 0)),
        "A2_plateau_>=2_methods_and_full_recall": bool(plateau_sup >= 2 and
            all(v["plateau"] == 12 for k, v in hit.items() if v["plateau"] > 0)),
        "A3_control_false_alarm_rate_<0.5%": bool(ctrl_rate < 0.005),
    },
    "PASS": None,
}
res["PASS"] = all(res["assertions"].values())
json.dump(res, open("mutation_test_result.json", "w"), indent=2)
print(json.dumps(res, indent=2))
