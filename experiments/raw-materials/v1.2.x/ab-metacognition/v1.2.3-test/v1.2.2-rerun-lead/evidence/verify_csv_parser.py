#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csv_parser.py 独立验证脚本（第三方可复算）

用法:
    python evidence/verify_csv_parser.py
退出码: 0 = 全部通过; 1 = 存在失败
依赖: 仅 Python 标准库。确定性: 无网络、无随机; 临时文件经 tempfile 自动清理。

验证路径（相互独立，构成交叉验证）:
  A. 价值电池   —— 手工推导期望值，覆盖任务书全部功能要求与边界情况
  B. 差分对照   —— 与 Python 标准库 csv 模块（独立实现）逐用例比对语义一致的输入
  C. 反例电池   —— 格式非法输入必须抛 ValueError
  D. 变异自检   —— 对解析器源码做 3 处定点缺陷注入，测试电池必须全部杀伤
                   （回答「把要防的错误做一次，电池会不会红？」）
  E. CLI 实测   —— 子进程真实运行命令行接口，校验输出与退出码

已知语义分歧（差分对照 B 中排除，属刻意设计）:
  - 未闭合引号: 本解析器抛 ValueError（严格）; stdlib csv 宽容接受
  - "a"b（闭合后多余字符）: 本解析器抛 ValueError; stdlib csv 得 'ab'
  - UTF-8 BOM: 本解析器剥除; stdlib csv 保留为字段内容
"""

import csv
import importlib.util
import io
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True  # 不在交付目录留下 __pycache__

HERE = Path(__file__).resolve().parent
PARSER_PATH = HERE.parent / "csv_parser.py"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RESULTS = []
CUR_SEG = ""


def seg(name):
    global CUR_SEG
    CUR_SEG = name
    print("\n== %s ==" % name)


def record(case_id, ok, detail=""):
    RESULTS.append((CUR_SEG, case_id, ok, detail))
    print("  [%s] %-5s %s" % ("PASS" if ok else "FAIL", case_id, detail if not ok else ""))


# ---------------------------------------------------------------- A. 价值电池
# (case_id, 输入, 期望输出)  输入可为 str 或 bytes
VALUE_CASES = [
    # 正常解析
    ("V01", "a,b,c", [["a", "b", "c"]]),
    ("V02", "a,b\nc,d", [["a", "b"], ["c", "d"]]),
    ("V03", "a,b\n", [["a", "b"]]),                # 末尾换行不产生多余空行
    ("V04", "a", [["a"]]),                          # 最后一行无换行符
    ("V05", "1,2,3\n4,5,6\n", [["1", "2", "3"], ["4", "5", "6"]]),
    # 引号: 逗号/换行/转义
    ("V06", '"a,b",c', [["a,b", "c"]]),
    ("V07", '"a\nb",c', [["a\nb", "c"]]),
    ("V08", '"a""b",c', [['a"b', "c"]]),
    ("V09", '""', [[""]]),                          # 引号包裹的空字段 ≠ 空行
    ("V10", '"",x', [["", "x"]]),
    ("V11", 'a,"",c', [["a", "", "c"]]),
    ("V12", '"多行\n带,逗号与""引号"""', [["多行\n带,逗号与\"引号\""]]),
    # 空字段 / 空行
    ("V13", "a,,b", [["a", "", "b"]]),
    ("V14", ",a", [["", "a"]]),
    ("V15", "a,", [["a", ""]]),
    ("V16", ",", [["", ""]]),
    ("V17", "", []),                                # 空文件
    ("V18", "\n", [[]]),                            # 只有换行符
    ("V19", "\n\n\n", [[], [], []]),
    ("V20", "a\n\nb", [["a"], [], ["b"]]),
    # 行尾: \n \r\n \r 混合
    ("V21", "a\r\nb", [["a"], ["b"]]),
    ("V22", "a\rb", [["a"], ["b"]]),
    ("V23", "a\r\nb\nc\rd", [["a"], ["b"], ["c"], ["d"]]),
    ("V24", "a\r\n", [["a"]]),
    ("V25", "a\r", [["a"]]),
    ("V26", '"a\r\nb",c', [["a\r\nb", "c"]]),       # 引号内行尾是内容
    ("V27", '"a\rb",c', [["a\rb", "c"]]),
    # 字段前后空格（决策: RFC 4180, 原样保留）
    ("V28", "  a  ,  b  ", [["  a  ", "  b  "]]),
    ("V29", "a, b ,c", [["a", " b ", "c"]]),
    ("V30", ' "a",b', [[' "a"', "b"]]),             # 引号前空格 → 引号为字面字符
    ("V31", 'a"b"c', [['a"b"c']]),                  # 非引号字段内字面引号
    ("V36", 'a," b ",c', [["a", " b ", "c"]]),
    # UTF-8 BOM
    ("V32", "﻿a,b", [["a", "b"]]),                   # str 层 \ufeff 剥离
    ("V33", b"\xef\xbb\xbfa,b", [["a", "b"]]),      # bytes 层 BOM 检测
    ("V34", "a,b".encode("utf-8"), [["a", "b"]]),   # bytes 无 BOM
    ("V35", "﻿\"x\",y", [["x", "y"]]),               # BOM + 引号字段
]

# ---------------------------------------------------------------- C. 反例电池
# (case_id, 输入, 缺陷说明)  —— 必须抛 ValueError
ERROR_CASES = [
    ("E01", '"a', "引号未闭合"),
    ("E02", 'a,"b', "引号未闭合"),
    ("E05", '"a\nb', "跨行引号未闭合"),
    ("E06", '"', "孤立引号"),
    ("E03", '"a"b', "引号闭合后多余字符"),
    ("E04", '""x', "引号闭合后多余字符"),
    ("E07", 'a,"b"c', "引号闭合后多余字符"),
]

# ------------------------------------------------- B. 差分对照排除清单（已知分歧）
ORACLE_EXCLUDED_SEGMENTS = ("UTF-8 BOM",)  # csv 模块不剥 BOM


def csv_reference(text):
    return list(csv.reader(io.StringIO(text, newline="")))


def main():
    print("环境: Python %s | %s" % (sys.version.split()[0], sys.platform))
    print("被测: %s" % PARSER_PATH)
    P = load_module(PARSER_PATH, "csv_parser")

    # ---- A. 价值电池
    seg("A. 价值电池（手工期望值）")
    for cid, data, expected in VALUE_CASES:
        try:
            got = P.parse(data)
            record(cid, got == expected, "got=%r want=%r" % (got, expected))
        except Exception as exc:  # noqa: BLE001
            record(cid, False, "异常 %s: %s" % (type(exc).__name__, exc))

    # ---- B. 差分对照（stdlib csv 独立实现）
    seg("B. 差分对照 vs stdlib csv")
    for cid, data, expected in VALUE_CASES:
        is_bom = cid in ("V32", "V33", "V34", "V35")
        if not isinstance(data, str) or is_bom:
            continue  # bytes/BOM 用例: csv 模块无对应语义（已知分歧, 见文件头）
        try:
            ref = csv_reference(data)
            record(cid + "-oracle", ref == expected,
                   "csv=%r want=%r（我方与 csv 语义分歧或期望值有误）" % (ref, expected))
        except Exception as exc:  # noqa: BLE001
            record(cid + "-oracle", False, "csv 参照异常: %s" % exc)

    # ---- C. 反例电池
    seg("C. 反例电池（必须 ValueError）")
    for cid, data, why in ERROR_CASES:
        try:
            got = P.parse(data)
            record(cid, False, "未报错, got=%r（%s）" % (got, why))
        except ValueError:
            record(cid, True)
        except Exception as exc:  # noqa: BLE001
            record(cid, False, "异常类型错误 %s: %s" % (type(exc).__name__, exc))

    # ---- D. 变异自检（测试电池鉴别力）
    seg("D. 变异自检（3 处缺陷注入必须全被杀伤）")
    MUTATIONS = [
        ("M1-转义失效", 'field.append(\'"\')  # "" 转义为一个双引号', "pass  # MUTATED"),
        ("M2-BOM失明", "text = text[1:]", "pass  # MUTATED"),
        ("M3-回车失明", 'if ch == "\\n" or ch == "\\r":', 'if ch == "\\n":'),
    ]
    src = PARSER_PATH.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        for name, needle, repl in MUTATIONS:
            assert src.count(needle) == 1, "变异锚点不唯一: %s" % name
            mpath = Path(tmp) / ("mutant_%s.py" % name.split("-")[0])
            mpath.write_text(src.replace(needle, repl), encoding="utf-8")
            M = load_module(mpath, "mutant_" + name)
            killed_by = []
            for cid, data, expected in VALUE_CASES:
                try:
                    if M.parse(data) != expected:
                        killed_by.append(cid)
                except Exception:  # noqa: BLE001
                    killed_by.append(cid)
            record(name, len(killed_by) >= 1, "未被杀伤（电池无鉴别力）")
            print("        杀伤用例: %s" % ", ".join(killed_by) if killed_by else "")

    # ---- E. CLI 实测
    seg("E. CLI 子进程实测")
    env = dict(__import__("os").environ, PYTHONIOENCODING="utf-8")

    def run_cli(*args):
        return subprocess.run(
            [sys.executable, str(PARSER_PATH), *args],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )

    cli_cases = [
        ("C01", "a,b\nc,d", None, 0, [["a", "b"], ["c", "d"]]),
        ("C02", None, b"\xef\xbb\xbfa,b", 0, [["a", "b"]]),          # BOM 文件
        ("C03", "a\r\nb\r\nc", None, 0, [["a"], ["b"], ["c"]]),      # CRLF 文件
        ("C04", '"x,y"\n"1""2"', None, 0, [["x,y"], ['1"2']]),
        ("C05", 'a,"b', None, 1, None),                              # 未闭合 → exit 1
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for cid, text, raw, want_code, want_rows in cli_cases:
            f = Path(tmp) / (cid + ".csv")
            f.write_bytes(raw if raw is not None else text.encode("utf-8"))
            proc = run_cli(str(f))
            ok = proc.returncode == want_code
            detail = "exit=%d want=%d" % (proc.returncode, want_code)
            if ok and want_rows is not None:
                got_lines = proc.stdout.splitlines()
                want_lines = [repr(r) for r in want_rows]
                ok = got_lines == want_lines
                detail = "stdout=%r want=%r" % (got_lines, want_lines)
            elif ok and want_rows is None:
                ok = bool(proc.stderr.strip())
                detail = "stderr 为空（应有错误信息）"
            record(cid, ok, detail)

        # C06: 文件不存在 → exit 1
        proc = run_cli(str(Path(tmp) / "no_such_file.csv"))
        record("C06", proc.returncode == 1 and proc.stderr.strip() != "",
               "exit=%d" % proc.returncode)
        # C07: 无参数 → exit 2
        proc = run_cli()
        record("C07", proc.returncode == 2 and proc.stderr.strip() != "",
               "exit=%d" % proc.returncode)

    # ---------------------------------------------------------------- 汇总
    total = len(RESULTS)
    failed = [r for r in RESULTS if not r[2]]
    print("\n" + "=" * 60)
    print("总计: %d 项 | 通过: %d | 失败: %d" % (total, total - len(failed), len(failed)))
    for s, cid, _, detail in failed:
        print("  FAIL %s/%s: %s" % (s, cid, detail))
    print("=" * 60)
    if not failed:
        print("ALL GREEN — 覆盖面声明见 evidence/证据报告.md")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
