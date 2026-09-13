#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csv_parser.py 的独立验证脚本（第三方可复算）。

运行方式（无需任何参数、无需任何第三方库）：

    cd Bprime-baseline
    python verify_csv_parser.py            # 人类可读报告
    python verify_csv_parser.py --quiet    # 只打印汇总
    python verify_csv_parser.py --json     # 机器可读结果

退出码：0 = 全部通过；1 = 存在失败。

验证分五组：
  A 功能用例      —— 手写输入/期望，覆盖 7 项功能要求
  B 边界用例      —— 覆盖任务书列出的 6 类边界（含 BOM、混合行尾等）
  C 反例用例      —— 证明"朴素实现"必然答错、畸形输入不崩、源码零依赖
  D 标准库对拍    —— 与 Python 标准库 csv 模块（默认方言）逐例对拍 + 随机差分模糊测试
  E 变异杀伤      —— 对解析器源码注入 4 处已知缺陷，验证测试集能抓到（证明测试非空转）
  F 文件/CLI 用例 —— 真实临时文件 + 子进程调用命令行接口
"""

import ast
import io
import csv as _stdlib_csv  # 仅作为对拍的"裁判"，被测解析器本身不得 import 它
import json
import os
import random
import subprocess
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
PARSER_PATH = os.path.join(HERE, "csv_parser.py")

VERBOSE = True
RESULTS = []


# --------------------------------------------------------------------------
# 工具
# --------------------------------------------------------------------------
def load_parser_module(source=None, name="csv_parser_under_test"):
    """从源码加载解析器模块（真实文件，或用于变异测试的注入源码）。"""
    if source is None:
        with open(PARSER_PATH, "r", encoding="utf-8") as fh:
            source = fh.read()
    module = types.ModuleType(name)
    module.__dict__["__file__"] = PARSER_PATH
    exec(compile(source, PARSER_PATH if source is None else "<mutant>", "exec"), module.__dict__)
    return module


PARSER = load_parser_module()
parse = PARSER.parse


def check(group, case_id, desc, actual, expected):
    ok = actual == expected
    RESULTS.append({"group": group, "id": case_id, "desc": desc, "ok": ok})
    if VERBOSE:
        mark = "PASS" if ok else "FAIL"
        line = "[%s] %-14s %s" % (mark, case_id, desc)
        print(line)
        if not ok:
            print("        期望: %r" % (expected,))
            print("        实际: %r" % (actual,))
    return ok


def check_true(group, case_id, desc, condition):
    return check(group, case_id, desc, bool(condition), True)


def stdlib_oracle(text):
    """标准库 csv 作为参考实现（newline='' 保留 \\r，交给 csv 自行断行）。

    注意：标准库 csv 不处理 BOM，对拍前先手工剥离 BOM，否则 BOM 用例会因"参考实现
    不剥 BOM"而假失败。BOM 行为本身由 A12/B14/B15、F04/F05 的显式期望覆盖。
    """
    if text.startswith("\ufeff"):
        text = text[1:]
    return list(_stdlib_csv.reader(io.StringIO(text, newline="")))


# --------------------------------------------------------------------------
# A 组：功能用例（对应任务书 7 条功能要求）
# --------------------------------------------------------------------------
FUNCTIONAL = [
    # id, 描述, 输入, 期望
    ("A01", "标准逗号分隔", 'a,b,c\n1,2,3', [["a", "b", "c"], ["1", "2", "3"]]),
    ("A02", "引号包裹字段", '"a","b,c"', [["a", "b,c"]]),
    ("A03", "引号内逗号", 'x,"1,2,3",y', [["x", "1,2,3", "y"]]),
    ("A04", "引号内换行(LF)", 'a,"line1\nline2",b', [["a", "line1\nline2", "b"]]),
    ("A05", '双引号转义 "" -> "', '"say ""hi"" now"', [['say "hi" now']]),
    ("A06", "空字段", 'a,,c', [["a", "", "c"]]),
    ("A07", "行尾空字段", 'a,b,\n', [["a", "b", ""]]),
    ("A08", "空行在中间", 'a\n\nc', [["a"], [], ["c"]]),
    ("A09", "行尾 \\n", 'a,b\nc,d', [["a", "b"], ["c", "d"]]),
    ("A10", "行尾 \\r\\n", 'a,b\r\nc,d', [["a", "b"], ["c", "d"]]),
    ("A11", "行尾 \\r", 'a,b\rc,d', [["a", "b"], ["c", "d"]]),
    ("A12", "UTF-8 BOM 跳过", '\ufeffa,b\n1,2', [["a", "b"], ["1", "2"]]),
    ("A13", "parse 返回列表的列表", 'a,b', [["a", "b"]]),
    ("A14", "引号内 CR 保留为数据", '"a\rb",x', [["a\rb", "x"]]),
    ("A15", "多行多列混合", 'id,name,note\n1,"a,b","he said ""ok"""\n2,"c",""\n',
     [["id", "name", "note"], ["1", "a,b", 'he said "ok"'], ["2", "c", ""]]),
]


# --------------------------------------------------------------------------
# B 组：边界用例（对应任务书 6 类边界）
# --------------------------------------------------------------------------
EDGE = [
    ("B01", "引号未闭合(行尾)", 'a,"unclosed', [["a", "unclosed"]]),
    ("B02", "引号未闭合(含转义)", '"a""b', [['a"b']]),
    ("B03", "引号未闭合(内部换行)", '"x\ny,z', [["x\ny,z"]]),
    ("B04", "字段前后空格保留", ' a , b ', [[" a ", " b "]]),
    ("B05", "引号外空格使引号成为数据", ' "a" ', [[' "a" ']]),
    ("B06", "引号内空格保留", '" a "', [[" a "]]),
    ("B07", "最后一行无换行符", 'a,b\nc,d', [["a", "b"], ["c", "d"]]),
    ("B08", "末行为空字段且无换行", 'a,', [["a", ""]]),
    ("B09", "只有换行符的文件 \\n\\n\\n", '\n\n\n', [[], [], []]),
    ("B10", "只有 CRLF 的文件", '\r\n\r\n', [[], []]),
    ("B11", "完全空文件", '', []),
    ("B12", "混合行尾 \\n 与 \\r\\n", 'a,1\nb,2\r\nc,3', [["a", "1"], ["b", "2"], ["c", "3"]]),
    ("B13", "混合行尾 \\r 与 \\n", 'a,1\rb,2\nc,3', [["a", "1"], ["b", "2"], ["c", "3"]]),
    ("B14", "BOM + 引号 + 多字节", '\ufeff"中文,字段","emoji😀"', [["中文,字段", "emoji😀"]]),
    ("B15", "BOM 单独存在", '\ufeff', []),
    ("B16", "换行结尾不产生尾部空行", 'a\n', [["a"]]),
    ("B17", "CRLF 结尾不产生尾部空行", 'a\r\n', [["a"]]),
    ("B18", "引号内连续转义", '"a""""b"', [['a""b']]),
    ("B19", "空字段引号对", '""', [[""]]),
    ("B20", "仅分隔符", ',,,', [["", "", "", ""]]),
]


# --------------------------------------------------------------------------
# C 组：反例用例
# --------------------------------------------------------------------------
def naive_split(text):
    """反面对照：按换行/逗号硬切、再剥引号的朴素实现（正确实现必须与它分道扬镳）。"""
    rows = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        rows.append([tok.strip().strip('"').replace('""', '"') for tok in line.split(",")])
    return rows


NEGATIVE_TEXTS = [
    'a,"b,c",d',               # 引号内逗号
    'a,"b\nc",d',              # 引号内换行
    ' "a""b" , c',             # 字段起始位置之外 + 前后空格，引号应为字面量
    '"a,b\nc",d',              # 引号内逗号+换行
    'a,"""",b',                # 四个连续引号应解析为一个字面 "
]


def run_group_c():
    print("\n--- C 组：反例用例 ---")
    for idx, text in enumerate(NEGATIVE_TEXTS, 1):
        got = parse(text)
        bad = naive_split(text)
        check_true("C", "C%02d" % idx,
                   "与朴素实现结果不同：%r" % (text[:28],),
                   got != bad)

    # 畸形输入不得抛异常（引号未闭合 / 孤立引号 / 超长未闭合）
    malformed = ['"', '"""', '"a', 'a,"', '"a"b"c', '"",",', '"\\', '"""",', '"' * 9]
    ok_all = True
    detail = None
    for text in malformed:
        try:
            parse(text)
        except Exception as exc:  # noqa: BLE001 - 故意捕获一切
            ok_all = False
            detail = "%r -> %s" % (text, exc)
            break
    check_true("C", "C90", "9 个畸形输入均不抛异常", ok_all)
    if not ok_all and VERBOSE:
        print("        %s" % detail)

    # 类型契约
    try:
        parse(b"a,b")
        type_ok = False
    except TypeError:
        type_ok = True
    check_true("C", "C91", "parse(bytes) 抛 TypeError", type_ok)

    rows = parse("a,b")
    shape_ok = (isinstance(rows, list) and all(isinstance(r, list) for r in rows)
                and all(isinstance(c, str) for r in rows for c in r))
    check_true("C", "C92", "返回值是 list[list[str]]", shape_ok)

    # 零依赖：源码里不得出现 csv / 第三方 import
    with open(PARSER_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    imported = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    allowed = {"sys", "json"}
    check_true("C", "C93", "源码 import 仅 %s（无 csv、无第三方）：实际 %s"
               % (sorted(allowed), sorted(imported)), imported <= allowed)
    check_true("C", "C94", "源码未使用标准库 csv 模块", "csv" not in imported)


# --------------------------------------------------------------------------
# D 组：与标准库对拍 + 随机差分模糊测试
# --------------------------------------------------------------------------
def run_group_d():
    print("\n--- D 组：标准库对拍 + 随机差分模糊测试 ---")
    texts = [t for (_, _, t, _) in FUNCTIONAL] + [t for (_, _, t, _) in EDGE]
    for idx, text in enumerate(texts, 1):
        got = parse(text)
        exp = stdlib_oracle(text)
        check("D", "D%03d" % idx, "对拍 stdlib：%r" % (text[:34],), got, exp)

    # 随机差分（固定种子，可复算）
    rnd = random.Random(20260913)
    tokens = ['a', 'bb', '', ' ', '  x  ', '"q"', '""', '"a""b"', '"a,b"', '"a\nb"',
              '"a\r\nb"', '"a\rb"', '"unclosed', '"', '""""', 'x"y', '" "', '中文',
              '"multi\nline, with ""quote"""']
    seps = [',', ',', ',', '\n', '\r\n', '\r', ',,', '\n\n']
    mismatches = 0
    cases = 0
    worst = None
    for _ in range(3000):
        k = rnd.randint(1, 8)
        parts = []
        for j in range(k):
            parts.append(rnd.choice(tokens))
            if j < k - 1:
                parts.append(rnd.choice(seps))
        text = "".join(parts)
        got = parse(text)
        exp = stdlib_oracle(text)
        cases += 1
        if got != exp:
            mismatches += 1
            if worst is None:
                worst = (text, got, exp)
    check("D", "D900", "随机差分 %d 例与 stdlib 一致（不一致 %d）" % (cases - mismatches, mismatches),
          mismatches, 0)
    if worst is not None and VERBOSE:
        print("        首例不一致: 输入=%r\n        我方=%r\n        stdlib=%r" % worst)


# --------------------------------------------------------------------------
# E 组：变异杀伤（证明测试集有鉴别力）
# --------------------------------------------------------------------------
MUTATIONS = [
    ("M1 去掉 \"\" 转义处理",
     "if i + 1 < n and text[i + 1] == QUOTE:", "if False:"),
    ("M2 任何位置的引号都当作引用起始",
     "if not field and not quoted:", "if True:"),
    ("M3 不识别 \\r\\n",
     "if ch == CR and i + 1 < n and text[i + 1] == LF:", "if False:"),
    ("M4 parse() 不跳过 BOM（精确定位 parse 内的那处，而非 _decode 内的同形代码）",
     "if text.startswith(BOM_STR):\n        text = text[1:]\n\n    rows = []",
     "if False:\n        text = text[1:]\n\n    rows = []"),
]

CORE_CASES = FUNCTIONAL + EDGE


def run_group_e():
    print("\n--- E 组：变异杀伤（测试集鉴别力自检） ---")
    with open(PARSER_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for idx, (name, old, new) in enumerate(MUTATIONS, 1):
        if old not in src:
            check_true("E", "E%02d" % idx, "%s：变异点未命中源码" % name, False)
            continue
        mutant_src = src.replace(old, new, 1)
        try:
            mutant = load_parser_module(mutant_src, name="mutant_%d" % idx)
        except Exception as exc:  # noqa: BLE001
            check_true("E", "E%02d" % idx, "%s：变异体无法加载 (%s)" % (name, exc), False)
            continue
        killed = 0
        for _cid, _desc, text, expected in CORE_CASES:
            try:
                got = mutant.parse(text)
            except Exception:  # noqa: BLE001 - 崩溃也算被抓到
                killed += 1
                continue
            if got != expected:
                killed += 1
        check_true("E", "E%02d" % idx,
                   "%s：被 %d/%d 条用例抓到" % (name, killed, len(CORE_CASES)),
                   killed >= 1)


# --------------------------------------------------------------------------
# F 组：文件级 + 命令行接口
# --------------------------------------------------------------------------
FILE_CASES = [
    ("F01", "LF 文件", b"a,b\n1,2\n", None, [["a", "b"], ["1", "2"]]),
    ("F02", "CRLF 文件", b"a,b\r\n1,2\r\n", None, [["a", "b"], ["1", "2"]]),
    ("F03", "CR 文件", b"a,b\r1,2\r", None, [["a", "b"], ["1", "2"]]),
    ("F04", "UTF-8 BOM 文件", b"\xef\xbb\xbfa,b\n1,2\n", None, [["a", "b"], ["1", "2"]]),
    ("F05", "UTF-16LE BOM 文件", "﻿a,b\n1,2\n".encode("utf-16-le"), None,
     [["a", "b"], ["1", "2"]]),
    ("F06", "末行无换行", b"a,b\n1,2", None, [["a", "b"], ["1", "2"]]),
    ("F07", "只有换行符的文件", b"\n\n\n", None, [[], [], []]),
    ("F08", "空文件", b"", None, []),
    ("F09", "混合行尾文件", b"a,1\nb,2\r\nc,3\rd,4\n", None,
     [["a", "1"], ["b", "2"], ["c", "3"], ["d", "4"]]),
    ("F10", "引号内换行文件", b'id,note\n1,"x\ny"\n2,"q""q"\n', None,
     [["id", "note"], ["1", "x\ny"], ["2", 'q"q']]),
    ("F11", "GBK 编码显式指定", "姓名,年龄\n张三,30\n".encode("gbk"), "gbk",
     [["姓名", "年龄"], ["张三", "30"]]),
    ("F12", "BOM+中文+引号", b'\xef\xbb\xbf"a,b",\xe4\xb8\xad\xe6\x96\x87\n', None,
     [["a,b", "中文"]]),
]


def run_group_f():
    print("\n--- F 组：文件级与命令行接口 ---")
    tmpdir = tempfile.mkdtemp(prefix="csv_verify_")
    py = sys.executable
    for cid, desc, raw, enc, expected in FILE_CASES:
        path = os.path.join(tmpdir, cid + ".csv")
        with open(path, "wb") as fh:
            fh.write(raw)
        try:
            got = PARSER.read_file(path, enc)
        except Exception as exc:  # noqa: BLE001
            got = "EXC:%s" % exc
        check("F", cid, "read_file %s" % desc, got, expected)

    # CLI：默认输出
    cli_path = os.path.join(tmpdir, "cli.csv")
    with open(cli_path, "wb") as fh:
        fh.write(b'\xef\xbb\xbfname,note\n"a,b","he said ""hi"""\n')
    proc = subprocess.run([py, PARSER_PATH, cli_path], capture_output=True, text=True)
    check("F", "F90", "CLI 退出码 0", proc.returncode, 0)
    check("F", "F91", "CLI stdout 解析结果",
          proc.stdout, "['name', 'note']\n['a,b', 'he said \"hi\"']\n")
    check_true("F", "F92", "CLI stderr 含统计 rows=2", "rows=2" in proc.stderr)

    # CLI --json
    proc = subprocess.run([py, PARSER_PATH, cli_path, "--json"], capture_output=True, text=True)
    try:
        decoded = json.loads(proc.stdout)
    except Exception:  # noqa: BLE001
        decoded = None
    check("F", "F93", "CLI --json 输出可解析且内容正确",
          decoded, [["name", "note"], ["a,b", 'he said "hi"']])

    # CLI 缺参数 / 文件不存在
    proc = subprocess.run([py, PARSER_PATH], capture_output=True, text=True)
    check("F", "F94", "CLI 无参数退出码 2", proc.returncode, 2)
    proc = subprocess.run([py, PARSER_PATH, os.path.join(tmpdir, "nope.csv")],
                          capture_output=True, text=True)
    check("F", "F95", "CLI 文件不存在退出码 1", proc.returncode, 1)

    # 非 UTF-8 字节 -> 必须报 CsvError，不能静默产出乱码
    # （注意：无 BOM 的 UTF-16LE 恰巧也能被 UTF-8 解出字符，故此处用真·非法 UTF-8 序列）
    bad = os.path.join(tmpdir, "bad.csv")
    with open(bad, "wb") as fh:
        fh.write(b"a,b,\xff\xfe\x80\n")
    try:
        PARSER.read_file(bad)
        raised = False
    except PARSER.CsvError:
        raised = True
    check_true("F", "F96", "非法 UTF-8 字节抛 CsvError（不静默乱码）", raised)


# --------------------------------------------------------------------------
def main(argv):
    global VERBOSE
    if "--quiet" in argv:
        VERBOSE = False
    print("=" * 72)
    print("csv_parser.py 验证报告")
    print("解析器: %s" % PARSER_PATH)
    print("Python : %s" % sys.version.split()[0])
    print("=" * 72)

    print("\n--- A 组：功能用例 ---")
    for cid, desc, text, expected in FUNCTIONAL:
        check("A", cid, desc, parse(text), expected)

    print("\n--- B 组：边界用例 ---")
    for cid, desc, text, expected in EDGE:
        check("B", cid, desc, parse(text), expected)

    run_group_c()
    run_group_d()
    run_group_e()
    run_group_f()

    total = len(RESULTS)
    failed = [r for r in RESULTS if not r["ok"]]
    print("\n" + "=" * 72)
    print("汇总: %d 项检查，通过 %d，失败 %d" % (total, total - len(failed), len(failed)))
    for r in failed:
        print("  失败: [%s] %s %s" % (r["group"], r["id"], r["desc"]))
    print("=" * 72)
    if "--json" in argv:
        print(json.dumps({"total": total, "failed": len(failed),
                          "results": RESULTS}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
