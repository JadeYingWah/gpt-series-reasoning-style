# -*- coding: utf-8 -*-
"""archive_metrics.py — Phase 0 后处理第 1-2 步：jsonl 归档哈希 + token 实测
可重复运行（idempotent）：产物未完成的臂跳过归档，标 pending。
输出：<实验根目录>/ab-v3/phase0/archive/*.jsonl + metrics.json + 控制台表
"""
import hashlib
import json
import os
import shutil
from datetime import datetime

SUB = ("C:/Users/<用户名>/.workbuddy/projects/c-Users-<用户名>-WorkBuddy-2026-09-10-23-57-12/"
       "45c568dd-ff70-4d57-af10-5860ee739c6b/subagents")
PHASE0 = "<实验根目录>/ab-v3/phase0"
ARCHIVE = os.path.join(PHASE0, "archive")
os.makedirs(ARCHIVE, exist_ok=True)

ARMS = {  # hash -> (task, arm)
    "65189f58": ("D1-winequality", "Bprime"),
    "46ebafad": ("D1-winequality", "A2"),
    "5b3582c2": ("D1-winequality", "A1"),
    "c924ea46": ("D2-cafe", "Bprime"),
    "b7bd68e0": ("D2-cafe", "A2"),
    "a174d906": ("D2-cafe", "A1"),
    "4f5b2798": ("D3-nab", "Bprime"),
    "4a6e6aea": ("D3-nab", "A2"),
    "4ff20b7e": ("D3-nab", "A1"),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def process(hash_, task, arm):
    src = None
    for fn in os.listdir(SUB):
        if fn.startswith(f"agent-{hash_}") and fn.endswith(".jsonl"):
            src = os.path.join(SUB, fn)
    if src is None:
        return {"status": "jsonl_missing"}
    done = os.path.exists(os.path.join(PHASE0, task, arm, "report.md"))

    recs = 0
    reqs = in_toks = out_toks = cached = reasoning = 0
    ts_first = ts_last = None
    with open(src, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            recs += 1
            ts = rec.get("timestamp")
            if ts:
                if ts_first is None:
                    ts_first = ts
                ts_last = ts
            u = (rec.get("providerData") or {}).get("usage") or {}
            reqs += int(u.get("requests", 0) or 0)
            in_toks += int(u.get("inputTokens", 0) or 0)
            out_toks += int(u.get("outputTokens", 0) or 0)
            for d in u.get("inputTokensDetails") or []:
                cached += int(d.get("cached_tokens", 0) or 0)
            for d in u.get("outputTokensDetails") or []:
                reasoning += int(d.get("reasoning_tokens", 0) or 0)

    dur_min = None
    try:
        # timestamp 为 Unix 毫秒
        dur_min = round((int(ts_last) - int(ts_first)) / 60000.0, 2)
    except Exception:
        pass

    archived = None
    arch_sha = None
    if done:
        dst = os.path.join(ARCHIVE, f"{task}_{arm}.jsonl")
        shutil.copyfile(src, dst)
        archived = dst
        arch_sha = sha256(dst)

    return {
        "task": task, "arm": arm, "agent_hash": hash_,
        "deliverable_done": done,
        "records": recs, "requests": reqs,
        "input_tokens": in_toks, "output_tokens": out_toks,
        "cached_tokens": cached, "reasoning_tokens": reasoning,
        "total_tokens": in_toks + out_toks,
        "duration_min": dur_min,
        "speed_flag_lt3min": bool(dur_min is not None and dur_min < 3),
        "archived_path": archived, "archived_sha256": arch_sha,
        "status": "archived" if done else "pending_execution",
    }


def main():
    out = {}
    for hash_, (task, arm) in ARMS.items():
        out[f"{task}/{arm}"] = process(hash_, task, arm)
    with open(os.path.join(PHASE0, "metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    hdr = f"{'arm':28s} {'state':6s} {'min':>6s} {'FLAG':>4s} {'reqs':>5s} {'input':>8s} {'output':>7s} {'cached':>8s} {'reason':>7s} {'total':>9s}"
    print(hdr)
    print("-" * len(hdr))
    for k, r in out.items():
        if r.get("status") == "jsonl_missing":
            print(f"{k:28s} MISSING")
            continue
        st = "done" if r["deliverable_done"] else "pend"
        flag = "YES" if r["speed_flag_lt3min"] else "-"
        print(f"{k:28s} {st:6s} {r['duration_min']!s:>6} {flag:>4s} {r['requests']:>5d} "
              f"{r['input_tokens']:>8d} {r['output_tokens']:>7d} {r['cached_tokens']:>8d} "
              f"{r['reasoning_tokens']:>7d} {r['total_tokens']:>9d}")
    print("\nmetrics.json ->", os.path.join(PHASE0, "metrics.json"))


if __name__ == "__main__":
    main()
