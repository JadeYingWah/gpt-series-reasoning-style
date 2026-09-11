#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mutation-kill.py -- 变异杀伤检验器 / Mutation-kill checker.

用途：验证「一份产物自带的检查」到底有没有鉴别力。
把产物自检当被测对象，注入若干**单点变异体**（各改一处的合理错误），逐个跑产物自带的自检：

- 期望被抓住的变异体（expect=FAIL）若自检仍报通过  => 该自检对该错误类别**不敏感**；
- 按错误类别统计 **杀伤率 = 命中期望的变异体数 / 该类变异体总数**；
- 杀伤率 0% 表示该类错误的验证证据为零（不是"证据较弱"）。

原则（与本仓库纪律一致）：
- **原产物只读**：只读其文本，变异体一律写在 workdir；前后比对 sha256，被改动即报错退出。
- **永不自动判 PASS**：本工具输出的是「产物自检自己的判定」，加上"是否符合期望"的比对；
  自检说 PASS 不等于产物正确，自检说 FAIL 也不等于产物错误。
- **静默替换即伪造**：每处 `find` 的命中数必须等于 `count`（默认 1），否则该变异体记 ERROR 而不是"通过"。

用法：
    python scripts/mutation-kill.py --help
    python scripts/mutation-kill.py run <manifest.json>

可运行的示例（与文档同仓）：
    python scripts/mutation-kill.py run scripts/examples/mutation-kill-demo.manifest.json
示例里 `artifact` / `workdir` 用相对路径，按 manifest 自身所在目录解析。

manifest.json 结构（唯一必须的字段是 artifact 与 mutants）：
{
  "artifact": "产物路径（只读）；相对路径按 manifest 所在目录解析",
  "workdir":  "可选，变异体与 profile 的落盘目录，默认系统临时目录",
  "chrome":   "可选，Chrome 可执行文件路径；不填则按常见路径探测",
  "budget_ms": 6000,
  "marker":   "自检结果标记串（须在 inject 源码里以拼接形式出现，否则会匹配到源码本身）",
  "inject":   "一段 <script>：调用产物自带的自检，把结果写成 marker + JSON 追加进 DOM",
  "mutants": [
    {"name": "m00-orig", "category": "baseline", "desc": "原样", "edits": []},
    {"name": "m01-fix",  "category": "render",   "desc": "把符号改回正确", "expect": "FAIL",
     "edits": [{"find": "旧串", "replace": "新串", "count": 1}]}
  ]
}

判定口径：
- `expect` 默认 "FAIL"（变异体应当被自检抓住）；"PASS" 用于基线或"预期自检抓不到"的变异体。
- `hit` = 实测判定 == expect。区分率按 category 分别统计。
- ERROR（find 命中数不符 / 取不到结果 / 超时）**不计入区分率分母**——它不是"没被抓住"，是根本没测成。
- 另打印「零区分力」告警：判定与基线相同的变异体。
"""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def find_chrome(explicit=None):
    if explicit and os.path.isfile(explicit):
        return explicit
    for c in CHROME_CANDIDATES:
        if os.path.isfile(c):
            return c
    return shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chrome")


def apply_edits(text, edits):
    """返回 (新文本, 问题列表)。命中数不符即记问题——静默替换等于伪造。"""
    problems = []
    out = text
    for i, e in enumerate(edits):
        find = e["find"]
        repl = e["replace"]
        want = int(e.get("count", 1))
        got = out.count(find)
        if want <= 0:                      # count<=0 表示"全部替换"，但必须命中至少一次
            if got == 0:
                problems.append("edit[%d] 命中 0 次（期望至少 1 次）：%s" % (i, find[:60]))
                continue
            out = out.replace(find, repl)
        else:
            if got != want:
                problems.append("edit[%d] 命中 %d 次，期望 %d 次：%s" % (i, got, want, find[:60]))
                continue
            out = out.replace(find, repl, want)
    return out, problems


def run_mutant(chrome, workdir, name, html, budget_ms, marker, inject, artifact_path):
    path = os.path.join(workdir, name + ".html")
    if inject and "</body>" in html:
        html = html.replace("</body>", inject + "\n</body>", 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    profile = os.path.join(workdir, "profile_" + name)
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + profile,
           "--virtual-time-budget=" + str(budget_ms),
           "--dump-dom", "file:///" + path.replace("\\", "/")]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=180)
        dom = p.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return "ERROR", "chrome 超时"
    m = re.search(re.escape(marker) + r"(\{[^\n<]*\}|ERROR[^\n<]*)", dom)
    if not m:
        return "ERROR", "未取到自检结果（注入脚本或 marker 不对？）"
    payload = m.group(1)
    if payload.startswith("ERROR"):
        return "ERROR", payload
    try:
        data = json.loads(payload)
    except ValueError as exc:
        return "ERROR", "结果 JSON 解析失败：%s" % exc
    return ("PASS" if data.get("pass") else "FAIL"), data.get("fails", data)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="mutation-kill.py",
        description="变异杀伤检验器：验证一份产物自带的自检有没有鉴别力（原产物只读，结果按错误类别统计杀伤率）")
    sub = ap.add_subparsers(dest="cmd")
    rp = sub.add_parser("run", help="按 manifest 执行变异杀伤实验")
    rp.add_argument("manifest", help="manifest.json 路径")
    args = ap.parse_args(argv)

    if args.cmd != "run":
        ap.print_help()
        return 0

    with open(args.manifest, encoding="utf-8") as f:
        man = json.load(f)
    man_dir = os.path.dirname(os.path.abspath(args.manifest))
    artifact = man["artifact"]
    if not os.path.isabs(artifact):                      # 相对路径按 manifest 所在目录解析
        artifact = os.path.normpath(os.path.join(man_dir, artifact))
    mutants = man.get("mutants") or []
    if not mutants:
        print("manifest 里没有任何 mutants，无事可做", file=sys.stderr)
        return 1
    marker = man.get("marker", "MUTRESULT:")
    inject = man.get("inject", "")
    budget = int(man.get("budget_ms", 6000))
    workdir = man.get("workdir") or os.path.join(tempfile.gettempdir(), "mutation-kill")
    if not os.path.isabs(workdir):                       # 同上
        workdir = os.path.normpath(os.path.join(man_dir, workdir))
    os.makedirs(workdir, exist_ok=True)

    chrome = find_chrome(man.get("chrome"))
    if not chrome:
        print("找不到 Chrome；请用 manifest 的 chrome 字段指定可执行文件路径", file=sys.stderr)
        return 1

    with open(artifact, encoding="utf-8") as f:
        src = f.read()
    before = sha256_text(src)

    rows = []
    base_verdict = None
    for mu in mutants:
        name = mu.get("name") or ("mutant%d" % (len(rows) + 1))
        cat = mu.get("category", "uncategorized")
        expect = mu.get("expect", "FAIL")
        html, problems = apply_edits(src, mu.get("edits") or [])
        declare_expect = "expect" in mu
        if problems:
            rows.append({"name": name, "category": cat, "expect": expect,
                         "expect_declared": declare_expect,
                         "verdict": "ERROR", "detail": "; ".join(problems),
                         "hit": False, "same_as_baseline": None})
            print("[ERROR] %-22s cat=%-12s %s" % (name, cat, "; ".join(problems)))
            continue
        verdict, detail = run_mutant(chrome, workdir, name, html, budget, marker, inject, artifact)
        row = {"name": name, "category": cat, "expect": expect,
               "expect_declared": declare_expect,
               "verdict": verdict, "detail": detail,
               "hit": verdict == expect, "same_as_baseline": None}
        if not mu.get("edits"):
            base_verdict = verdict
            row["category"] = "baseline"
        elif base_verdict is not None:
            row["same_as_baseline"] = (verdict == base_verdict)
        rows.append(row)
        print("[%-5s] %-22s cat=%-12s%s" % (
            verdict, name, row["category"],
            ("   <-- 与基线判定相同：零区分力" if row["same_as_baseline"] else "")))

    after = sha256_text(open(artifact, encoding="utf-8").read())
    print("")
    print("原产物只读校验：%s -> %s  %s" % (
        before[:16], after[:16], "OK" if before == after else "!!! 原产物被改动，结果作废"))

    cats = {}
    errored = []
    for r in rows:
        if r["category"] == "baseline":
            continue
        if r["verdict"] == "ERROR":
            errored.append(r["name"])            # ERROR 不计入分母：它不是"没被抓住"，是根本没测成
            continue
        d = cats.setdefault(r["category"], {"n": 0, "distinguished": 0, "hit": 0, "exp": 0})
        d["n"] += 1
        d["distinguished"] += 1 if r["same_as_baseline"] is False else 0
        if r.get("expect_declared"):
            d["exp"] += 1
            d["hit"] += 1 if r["hit"] else 0
    print("")
    print("区分率 = 判定与基线不同的变异体 / 该类有效变异体总数（核心指标）")
    for c in sorted(cats):
        d = cats[c]
        line = "  %-14s 区分 %d/%d = %5.1f%%" % (c, d["distinguished"], d["n"],
                                               100.0 * d["distinguished"] / d["n"])
        if d["exp"]:
            line += "   命中期望 %d/%d" % (d["hit"], d["exp"])
        print(line)
    zero = [r["name"] for r in rows if r["same_as_baseline"]]
    if zero:
        print("")
        print("零区分力告警（变异后判定与基线完全相同，即这份自检没看出差别）：")
        for n in zero:
            print("  - " + n)
    if errored:
        print("")
        print("未测成（ERROR，不计入区分率，需先修 manifest/环境）：")
        for n in errored:
            print("  - " + n)

    out = os.path.join(workdir, "mutation-kill-report.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"artifact": artifact, "sha256_before": before, "sha256_after": after,
                   "baseline_verdict": base_verdict, "mutants": rows,
                   "per_category": cats}, f, ensure_ascii=False, indent=1, default=str)
    print("")
    print("报告：" + out)
    err = [r for r in rows if r["verdict"] == "ERROR"]
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
