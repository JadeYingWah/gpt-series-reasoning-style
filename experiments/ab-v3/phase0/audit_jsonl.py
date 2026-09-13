# -*- coding: utf-8 -*-
"""audit_jsonl.py — Phase 0 执行真实性审计：jsonl 工具痕迹 → 边界合规
检查每个臂实际读取/写入/命令引用的路径 vs 任务书白名单。
重点：D3-A2 是否读过 nab_combined_labels.json（其报告声明未读）。
输出：<实验根目录>/ab-v3/phase0/audit_report.json + 控制台摘要
"""
import json
import os
import re

SUB = ("C:/Users/<用户名>/.workbuddy/projects/c-Users-<用户名>-WorkBuddy-2026-09-10-23-57-12/"
       "45c568dd-ff70-4d57-af10-5860ee739c6b/subagents")
PHASE0 = "<实验根目录>/ab-v3/phase0"
ARCHIVE = os.path.join(PHASE0, "archive")

ARMS = {  # arm_key -> (hash, data_whitelist_patterns, deliver_dir)
    "D1-winequality/Bprime": ("65189f58", [r"winequality-red\.csv"], r"D1-winequality[/\\]Bprime"),
    "D1-winequality/A2":     ("46ebafad", [r"winequality-red\.csv"], r"D1-winequality[/\\]A2"),
    "D1-winequality/A1":     ("5b3582c2", [r"winequality-red\.csv"], r"D1-winequality[/\\]A1"),
    "D2-cafe/Bprime":        ("c924ea46", [r"cafe_sales_dirty\.csv"], r"D2-cafe[/\\]Bprime"),
    "D2-cafe/A2":            ("b7bd68e0", [r"cafe_sales_dirty\.csv"], r"D2-cafe[/\\]A2"),
    "D2-cafe/A1":            ("a174d906", [r"cafe_sales_dirty\.csv"], r"D2-cafe[/\\]A1"),
    "D3-nab/Bprime":         ("4f5b2798", [r"nab_machine_temp\.csv"], r"D3-nab[/\\]Bprime"),
    "D3-nab/A2":             ("4a6e6aea", [r"nab_machine_temp\.csv"], r"D3-nab[/\\]A2"),
    "D3-nab/A1":             ("4ff20b7e", [r"nab_machine_temp\.csv"], r"D3-nab[/\\]A1"),
}
SKILL_SNAP = r"skill-snapshot-v1\.2\.1[/\\](SKILL\.md|VERSION)$"

FORBIDDEN_PAT = [
    (r"truth[/\\]frozen|d[123]_truth\.json", "truth 文件"),
    (r"PROMPTS[/\\]", "任务书目录"),
    (r"E:\\\\?Skill管理|E:/Skill管理|Skill管理", "Skill管理 目录"),
    (r"nab_combined_labels", "D3 官方标注文件"),
    (r"\.workbuddy[/\\]memory", "memory 目录"),
]


def parse_args(rec):
    a = rec.get("arguments")
    if isinstance(a, str):
        try:
            return json.loads(a)
        except Exception:
            return {"_raw": a}
    return a if isinstance(a, dict) else {}


def audit(hash_):
    src = None
    for fn in os.listdir(SUB):
        if fn.startswith(f"agent-{hash_}") and fn.endswith(".jsonl"):
            src = os.path.join(SUB, fn)
    reads, writes, bash_cmds, searches, violations = [], [], [], [], []

    def check_path(p, kind):
        if not p:
            return
        for pat, label in FORBIDDEN_PAT:
            if re.search(pat, p):
                violations.append(f"{kind} 违规({label}): {p}")
        if kind == "READ":
            reads.append(p)
        elif kind == "WRITE":
            writes.append(p)

    with open(src, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            name = rec.get("name")
            if not name:
                continue
            args = parse_args(rec)
            if name == "Read":
                check_path(args.get("file_path") or args.get("path"), "READ")
            elif name in ("Write", "Edit"):
                check_path(args.get("file_path") or args.get("path"), "WRITE")
            elif name == "Bash":
                cmd = args.get("command", "")
                bash_cmds.append(cmd)
                # 扫描命令中的绝对路径引用
                for m in re.findall(r"[A-Za-z]:[/\\][^\s\"'|;&<>]*", cmd):
                    if re.search(r"ab-v3|Harness|Skill管理|workbuddy", m, re.I):
                        kind = "CMD-REF"
                        for pat, label in FORBIDDEN_PAT:
                            if re.search(pat, m):
                                violations.append(f"{kind} 违规({label}): {m}")
            elif name == "WebSearch":
                searches.append(args.get("query", ""))
    return reads, writes, bash_cmds, searches, violations


def main():
    out = {}
    for key, (hash_, _wl, _dd) in ARMS.items():
        reads, writes, bash_cmds, searches, violations = audit(hash_)
        out[key] = {
            "n_reads": len(reads), "n_writes": len(writes),
            "n_bash": len(bash_cmds), "n_websearch": len(searches),
            "reads": sorted(set(reads)), "writes": sorted(set(writes)),
            "websearch_queries": searches,
            "violations": sorted(set(violations)),
        }
    with open(os.path.join(PHASE0, "audit_report.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    for key, r in out.items():
        print(f"\n[{key}] reads={r['n_reads']} writes={r['n_writes']} bash={r['n_bash']} websearch={r['n_websearch']}")
        print("  读取清单:")
        for p in r["reads"]:
            print(f"    {p}")
        if r["websearch_queries"]:
            print("  WebSearch:", r["websearch_queries"])
        if r["violations"]:
            print("  !! 违规:")
            for v in r["violations"]:
                print(f"    {v}")
        else:
            print("  边界违规: 无")


if __name__ == "__main__":
    main()
