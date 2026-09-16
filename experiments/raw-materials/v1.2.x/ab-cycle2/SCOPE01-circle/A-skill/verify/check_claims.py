"""SCOPE01 A臂 — 声明-产物一致性核验（claim check）
把 response.md 第 2 节的磁盘清单与实际磁盘逐条对照；
把第 3 节声称的用例数与 report.txt 实际 PASS 数对照。
复跑：python check_claims.py
"""
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DOC = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else BASE / "response.md"
REPORT = BASE / "verify" / "report.txt"

ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|", re.M)
CASE = re.compile(r"^RESULT: (PASS|FAIL)$", re.M)   # 仅逐用例判据行，不含「总判定」
CLAIM = re.compile(r"(\d+)\s*/\s*(\d+)\s*用例")      # response.md 自述的用例覆盖数

# 瞬态生成物：内容随每次运行变化（自指），不纳入「声明清单」对照，
# 单独打印以免被误判为未声明的多余产物。
GENERATED = {
    "verify/claim-check.txt",
    "verify/mutation-test.txt",
}


def main():
    text = DOC.read_text(encoding="utf-8")
    rows = ROW.findall(text)
    problems = []

    print(f"response.md 磁盘清单条目数 = {len(rows)}")
    for rel, size in rows:
        p = BASE / rel.replace("\\", "/")
        if not p.exists():
            problems.append(f"声明的文件不存在: {rel}")
            print(f"  MISSING  {rel}")
            continue
        actual = p.stat().st_size
        mark = "OK " if actual == int(size) else "SIZE!"
        if actual != int(size):
            problems.append(f"大小不符: {rel} 声明={size} 实际={actual}")
        print(f"  {mark} {rel}  声明={size} 实际={actual}")

    rep = REPORT.read_text(encoding="utf-8")
    cases = CASE.findall(rep)
    n_pass = cases.count("PASS")
    n_fail = cases.count("FAIL")

    m = CLAIM.search(text)
    claimed = int(m.group(1)) if m else None
    total_claim = int(m.group(2)) if m else None
    print(f"\nreport.txt 逐用例判据: PASS={n_pass} FAIL={n_fail}")
    print(f"response.md 自述用例数: {claimed}/{total_claim}")
    if claimed is None:
        problems.append("response.md 未给出 N/N 用例覆盖声明，无法对照")
    else:
        if n_pass != claimed:
            problems.append(f"用例覆盖数不符: 自述 {claimed} 实际 PASS {n_pass}")
        if total_claim != n_pass + n_fail and total_claim != n_pass:
            problems.append(f"自述分母 {total_claim} 与实测 {n_pass + n_fail} 不符")
    if n_fail:
        problems.append(f"report.txt 中存在 {n_fail} 个 FAIL")

    # 反向：磁盘上是否有未被声明的多余产物（本目录内）
    allowed = {r[0].replace("\\", "/") for r in rows} | {"response.md"} | GENERATED
    extra = []
    for f in BASE.rglob("*"):
        if f.is_file():
            rel = f.relative_to(BASE).as_posix()
            if rel not in allowed:
                extra.append(rel)
    print(f"\n瞬态生成物（不参与声明对照，共 {len(GENERATED)} 个）: {sorted(GENERATED)}")
    print(f"未被 response.md 声明的文件 = {len(extra)}")
    for e in sorted(extra):
        print(f"  EXTRA {e}")
        problems.append(f"磁盘存在未声明的产物: {e}")

    print("\n" + ("CLAIM CHECK: PASS" if not problems else "CLAIM CHECK: FAIL"))
    for p in problems:
        print("  - " + p)
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
