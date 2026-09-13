# -*- coding: utf-8 -*-
"""
敏感性审计（鉴别力验证）：扰动阈值 / burn-in / 合并间隔，检查主报告 4 组区段的共识稳定性。
扰动下共识支持数下降但仍 >=2 → 稳定(robust)；降为 1 → 标记 fragile。
输出: sensitivity_result.json
"""
import pandas as pd, numpy as np, json

SRC = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
PRIMARY = [
    {"name": "P1_shutdown_1216",  "s": "2013-12-16 15:30:00", "e": "2013-12-16 18:40:00"},
    {"name": "P2_transient_1228", "s": "2013-12-28 02:50:00", "e": "2013-12-28 06:15:00"},
    {"name": "P3_transient_0102", "s": "2014-01-02 08:30:00", "e": "2014-01-02 09:55:00"},
    {"name": "P4_drop_0208_09",   "s": "2014-02-08 02:00:00", "e": "2014-02-09 12:10:00"},
]

df = pd.read_csv(SRC)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').drop_duplicates('timestamp', keep='first').reset_index(drop=True)
x = df['value'].to_numpy(float); n = len(df)
t = df['timestamp']

def run_all(burn_frac, z_th, iforest_q):
    burn = int(n * burn_frac)
    idx = np.arange(n)
    scores = {}
    # M1
    med = np.median(x); mad = np.median(np.abs(x-med))*1.4826
    scores["M1"] = np.abs((x-med)/mad)
    # M2 相位
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
    scores["M2"] = np.abs(z2)
    # M3
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
    scores["M3"] = np.abs(z3)
    # M4（q 固定 0.5%，重训成本高，单次训练缓存分数）
    global _IF_SCORE
    if "_IF_SCORE" not in globals():
        from sklearn.ensemble import IsolationForest
        f = pd.DataFrame({"value": x,
                          "rm1h": s.rolling(12, center=True, min_periods=6).mean(),
                          "rs1h": s.rolling(12, center=True, min_periods=6).std()})
        td = t.dt.hour*60 + t.dt.minute
        f["tod_sin"] = np.sin(2*np.pi*td/1440); f["tod_cos"] = np.cos(2*np.pi*td/1440)
        f = f.bfill().ffill()
        iso = IsolationForest(n_estimators=300, random_state=42, n_jobs=-1).fit(f)
        _IF_SCORE = -iso.decision_function(f)
    scores["M4"] = _IF_SCORE
    m4_th = np.quantile(_IF_SCORE[burn:], iforest_q)
    masks = {}
    for k, sc in scores.items():
        masks[k] = (sc >= (m4_th if k == "M4" else z_th)) & (idx >= burn)
    return masks

def seg_hits(mask, s, e, gap_min=60):
    """mask 点区段化(60min)后与 [s,e] 有交集的区段数"""
    pts = t[mask].reset_index(drop=True)
    if len(pts) == 0: return 0
    segs, start, prev = [], pts[0], pts[0]
    for cur in pts[1:]:
        if cur - prev <= pd.Timedelta(minutes=gap_min): prev = cur
        else: segs.append((start, prev)); start = prev = cur
    segs.append((start, prev))
    S, E = pd.Timestamp(s), pd.Timestamp(e)
    return sum(1 for a, b in segs if a <= E and b >= S)

grids = []
for burn_frac in [0.10, 0.15, 0.20]:
    for z_th in [5.0, 5.5, 6.0, 6.5, 7.0]:
        masks = run_all(burn_frac, z_th, 0.005)
        for p in PRIMARY:
            sup = {k: int(seg_hits(m, p["s"], p["e"])) for k, m in masks.items()}
            grids.append({"perturb": f"burn={burn_frac},z={z_th}", **{"region": p["name"]},
                          **{f"{k}_segs": v for k, v in sup.items()},
                          "n_methods": sum(1 for v in sup.values() if v > 0)})
json.dump(grids, open("sensitivity_result.json", "w"), indent=2)

# 汇总：仅统计「区段完全在 burn-in 之后」的组合（burn-in 屏蔽属预期行为，不计入失效）
n_pts = len(df)
summary = {}
for p in PRIMARY:
    vals_all, vals_eff = [], []
    for g in grids:
        if g["region"] != p["name"]:
            continue
        vals_all.append(g["n_methods"])
        burn_frac = float(g["perturb"].split(",")[0].split("=")[1])
        if pd.Timestamp(p["s"]) > t.iloc[int(n_pts * burn_frac)]:
            vals_eff.append(g["n_methods"])
    summary[p["name"]] = {"min_support_all": min(vals_all),
                          "min_support_effective": min(vals_eff) if vals_eff else None,
                          "median_support": int(np.median(vals_all)),
                          "n_perturbs_burnin_masked": len(vals_all) - len(vals_eff),
                          "robust_effective": bool(min(vals_eff) >= 2) if vals_eff else False}
json.dump(summary, open("sensitivity_summary.json", "w"), indent=2)
print(json.dumps(summary, indent=2))
