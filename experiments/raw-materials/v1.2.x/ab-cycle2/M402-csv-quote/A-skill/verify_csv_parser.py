# -*- coding: utf-8 -*-
"""csv_parser.parse_line 的验证脚本（阶段 2 证据产物）。

运行： python verify_csv_parser.py

包含三层：
1) 正向用例：修复版 parse_line 输出 == 期望值；
2) 负向对照（杀伤率）：把修复前的实现内联进来，确认它在「目标缺陷用例」上
   必然失败——用于证明这些用例有鉴别力，而不是恒真的空检查；
3) 交叉对照：对良构输入与标准库 csv 模块比对。

修复前实现按 task.md 所述现状内联（`line.rstrip("\n").split(",")`）。
"""
import csv
import sys

from csv_parser import parse_line


def broken_parse_line(line):
    """修复前的实现（原文照抄，仅作负向对照）。"""
    return line.rstrip("\n").split(",")


# 目标缺陷用例：修复前应当失败，修复后应当通过。
BUG_CASES = [
    ('a,"b,c",d', ['a', 'b,c', 'd'], '字段内逗号（核心缺陷：原会切成 4 列）'),
    ('a,"b""c",d', ['a', 'b"c', 'd'], '"" 转义为字面引号'),
    ('"a""b"', ['a"b'], '整字段 "" 转义'),
    ('a,"",d', ['a', '', 'd'], '空引号字段'),
    ('"a,b","c,d"', ['a,b', 'c,d'], '多个引号字段'),
    ('a,"b\nc",d', ['a', 'b\nc', 'd'], '引号内的换行不作为记录边界'),
    ('"x\ny"', ['x\ny'], '引号内换行整体保留'),
]

# 回归用例：修复前已正确，修复后必须保持一致（其余行为不变）。
REG_CASES = [
    ('a,b,c', ['a', 'b', 'c'], '普通行'),
    ('', [''], '空字符串'),
    (',', ['', ''], '单个逗号'),
    ('a,', ['a', ''], '尾随逗号'),
    ('a,,c', ['a', '', 'c'], '中间空字段'),
    ('a,b\n', ['a', 'b'], '行尾换行剥离'),
]

# 与标准库 csv 交叉对照（良构输入）。
ORACLE_INPUTS = [
    'a,b,c',
    'a,"b,c",d',
    'a,"b""c",d',
    '"a""b"',
    'a,"",d',
    '"a,b","c,d"',
    'a,"b\nc",d',
]


def main():
    failures = 0

    print('== 1) 正向用例（修复版）==')
    for inp, exp, desc in BUG_CASES + REG_CASES:
        got = parse_line(inp)
        ok = got == exp
        failures += 0 if ok else 1
        print('[%s] %s: %r -> %r (期望 %r)' % ('PASS' if ok else 'FAIL', desc, inp, got, exp))

    print('\n== 2) 负向对照 / 杀伤率（修复前实现）==')
    killed = 0
    for inp, exp, desc in BUG_CASES:
        got = broken_parse_line(inp)
        did_fail = got != exp
        killed += 1 if did_fail else 0
        print('[%s] %s: %r -> %r (期望 %r)' % ('KILLED' if did_fail else 'SURVIVED', desc, inp, got, exp))
    reg_intact = all(broken_parse_line(i) == e for i, e, _ in REG_CASES)
    print('修复前实现在目标缺陷用例上被杀死: %d/%d' % (killed, len(BUG_CASES)))
    print('修复前实现在回归用例上保持原行为: %s' % reg_intact)
    if killed != len(BUG_CASES):
        failures += 1
        print('!! 杀伤率未达 100%%，用例鉴别力不足')

    print('\n== 3) 与标准库 csv 交叉对照 ==')
    mismatches = 0
    for inp in ORACLE_INPUTS:
        mine = parse_line(inp)
        ref = next(csv.reader([inp]))
        ok = mine == ref
        mismatches += 0 if ok else 1
        print('[%s] %r -> mine=%r csv=%r' % ('AGREE' if ok else 'DIFF', inp, mine, ref))
    if mismatches:
        failures += 1

    print('\n== 汇总 ==')
    print('失败项合计: %d' % failures)
    print('结论: %s' % ('全部通过' if failures == 0 else '存在失败'))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
