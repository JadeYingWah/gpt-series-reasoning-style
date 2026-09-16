"""SCOPE01 A臂 — 核验器鉴别力测试（变异杀伤）
思路：把 response.md 篡改几处，看 check_claims.py 是否会变红。
若篡改后仍报 PASS，说明该核验器只是「看起来很足」，不构成证据。
复跑：python mutate_test.py
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
CHECKER = HERE / "check_claims.py"
# 变异文档写到系统临时目录，不污染交付目录（也避免触发目录内清理守卫）
TMP = Path(tempfile.gettempdir()) / "scope01-mutated-response.md"


def run(doc: Path):
    p = subprocess.run([sys.executable, str(CHECKER), str(doc)],
                       capture_output=True, text=True)
    return p.returncode, p.stdout


def mutations(src):
    return [
        ("① 把 art.html 的大小 520 改成 999",
         src.replace("| `art.html` | 520 |", "| `art.html` | 999 |")),
        ("② 把自述用例数 4/4 改成 3/3",
         src.replace("4/4 用例", "3/3 用例")),
        ("③ 删掉 prove_clamp.py 的声明行",
         re.sub(r"\| `verify/prove_clamp\.py` \| 1251 \|[^\n]*\n", "", src)),
        ("④ 声明一个磁盘上不存在的文件",
         src.replace("| `verify/verify_pixels.py` | 4006 |",
                     "| `verify/ghost.py` | 4006 |")),
    ]


def main():
    src = (BASE / "response.md").read_text(encoding="utf-8")

    print("=== 基线（未篡改）===")
    code, out = run(BASE / "response.md")
    print(f"exit={code}  末行={out.strip().splitlines()[-1]}")
    base_ok = code == 0

    killed = 0
    cases = mutations(src)
    for name, text in cases:
        if text == src:
            print(f"{name} -> 变异未生效（原文未匹配），计为漏检")
            continue
        TMP.write_text(text, encoding="utf-8")
        code, out = run(TMP)
        died = code != 0 and "CLAIM CHECK: FAIL" in out
        killed += 1 if died else 0
        tail = [l.strip() for l in out.strip().splitlines() if l.strip().startswith("- ")]
        print(f"{name} -> {'RED 被杀死' if died else 'GREEN 漏检!'}  {tail}")
    TMP.unlink(missing_ok=True)
    if TMP.exists():
        print(f"（提示：临时文件未能删除，位于系统临时目录 {TMP}，不影响交付目录）")

    print(f"\n基线通过={base_ok}  变异杀伤率={killed}/{len(cases)}")
    ok = base_ok and killed == len(cases)
    print("RESULT: " + ("PASS（核验器有鉴别力）" if ok else "FAIL（核验器无鉴别力）"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
