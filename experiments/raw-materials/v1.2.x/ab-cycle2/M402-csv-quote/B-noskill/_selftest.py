# -*- coding: utf-8 -*-
import csv
import io
import sys

from csv_parser import parse_line

# (输入, 期望字段列表)
CASES = [
    # 原始行为的回归用例
    ("a,b,c", ["a", "b", "c"]),
    ("a,b,c\n", ["a", "b", "c"]),
    ("", [""]),
    ("\n", [""]),
    ("a,", ["a", ""]),
    (",a", ["", "a"]),
    (",,", ["", "", ""]),
    # 目标缺陷 1：引号内逗号
    ('a,"b,c",d', ["a", "b,c", "d"]),
    ('"a,b",c', ["a,b", "c"]),
    ('a,"b,c,d",e,"f"', ["a", "b,c,d", "e", "f"]),
    # 目标缺陷 2："" 转义
    ('a,"b""c",d', ["a", 'b"c', "d"]),
    ('"a""b"', ['a"b']),
    ('a,"""",b', ["a", '"', "b"]),
    ('"he said ""hi""",x', ['he said "hi"', "x"]),
    # 引号包裹空字段 / 仅引号
    ('""', [""]),
    ('a,"",b', ["a", "", "b"]),
    ('""""', ['"']),
    # 引号内换行
    ('a,"b\nc",d', ["a", "b\nc", "d"]),
    ('"l1\nl2\nl3",z', ["l1\nl2\nl3", "z"]),
    ('a,"x\ny"', ["a", "x\ny"]),
    # 非字段起始位置的引号按字面处理
    ('a"b,c', ['a"b', "c"]),
    ('a,b"c"d', ["a", 'b"c"d']),
    # 闭合引号后跟普通字符（宽松处理）
    ('"ab"cd,e', ["abcd", "e"]),
    # 经典实测值
    ('1997,Ford,E350', ["1997", "Ford", "E350"]),
    (
        '1997,Ford,E350,"ac, abs, moon",3000.00',
        ["1997", "Ford", "E350", "ac, abs, moon", "3000.00"],
    ),
]

# 与标准库 csv 模块交叉验证的输入（仅取 csv 模块能单行解析的部分）
ORACLE = [
    'a,"b,c",d',
    'a,"b""c",d',
    '"he said ""hi""",x',
    'a,"",b',
    '""""',
    'a"b,c',
    'a,b"c"d',
    '"ab"cd,e',
    '1997,Ford,E350,"ac, abs, moon",3000.00',
]

fails = 0
for raw, expected in CASES:
    got = parse_line(raw)
    ok = got == expected
    if not ok:
        fails += 1
    print(("PASS" if ok else "FAIL"), repr(raw), "->", repr(got), "" if ok else "(期望 %r)" % (expected,))

print("--- 与标准库 csv 交叉验证 ---")
for raw in ORACLE:
    mine = parse_line(raw)
    theirs = next(csv.reader(io.StringIO(raw + "\n")))
    ok = mine == theirs
    if not ok:
        fails += 1
    print(("PASS" if ok else "FAIL"), repr(raw), "mine=%r csv=%r" % (mine, theirs))

print("--- 合计 ---")
print("用例数 =", len(CASES) + len(ORACLE), " 失败 =", fails)
sys.exit(1 if fails else 0)
