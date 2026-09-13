#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G1-A2plus 独立 oracle（多路径交叉验证之路径 2 的期望值来源）
1) UI 序列模拟器：按任务规格用 Python 独立实现（不复用 JS 代码）
2) eval_exact：fractions 精确分数求值（非浮点，与 JS float 路线独立）
3) fmt12：12 位有效数字显示格式化（对齐 JS parseFloat(n.toPrecision(12)) 语义）
输出 vectors.json，供 test-core.mjs（Node 核心电池）与 test-browser.mjs（CDP E2E）消费。
域限制：结果绝对值 <= 1e15（超出则断言失败——该域内 JS String() 无科学计数法显示分叉）。
"""
import json
import os
import re
from fractions import Fraction
from decimal import Decimal, getcontext, ROUND_HALF_UP

getcontext().prec = 60
MAX_SEG = 18
DOMAIN_LIMIT = Decimal(10) ** 15


def is_op(c):
    return c in '+-*/'


def disp(s):
    """与 index.html toDisplay 相同的显示符号映射（纯字符串替换，语义 trivially 一致）"""
    return s.replace('*', '×').replace('/', '÷').replace('-', '−')


def segment(e):
    idx = -1
    for i in range(len(e) - 1, -1, -1):
        if is_op(e[i]):
            idx = i
            break
    return e[idx + 1:]


def eval_exact(expr):
    """精确分数求值。返回 ('OK', Fraction) | ('DIV0', None) | ('SYNTAX', None) | ('EMPTY', None)"""
    tokens = []
    i = 0
    while i < len(expr):
        c = expr[i]
        if c.isdigit() or c == '.':
            j = i
            while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                j += 1
            num = expr[i:j]
            if not re.fullmatch(r'\d+(\.\d*)?|\.\d+', num):
                return ('SYNTAX', None)
            tokens.append(('num', Fraction(num.rstrip('.') if num.endswith('.') else num)))
            i = j
        elif is_op(c):
            tokens.append(('op', c))
            i += 1
        else:
            return ('SYNTAX', None)
    if not tokens:
        return ('EMPTY', None)
    if tokens[0][0] != 'num':
        return ('SYNTAX', None)
    for k in range(1, len(tokens)):
        if tokens[k][0] == tokens[k - 1][0]:
            return ('SYNTAX', None)
    pass1 = [tokens[0]]
    m = 1
    while m < len(tokens):
        typ, opv = tokens[m]
        nxt = tokens[m + 1] if m + 1 < len(tokens) else None
        if nxt is None:
            return ('SYNTAX', None)
        if opv == '*':
            pass1[-1] = ('num', pass1[-1][1] * nxt[1])
        elif opv == '/':
            if nxt[1] == 0:
                return ('DIV0', None)
            pass1[-1] = ('num', pass1[-1][1] / nxt[1])
        else:
            pass1.extend([(typ, opv), nxt])
        m += 2
    acc = pass1[0][1]
    m = 1
    while m < len(pass1):
        if pass1[m][1] == '+':
            acc += pass1[m + 1][1]
        else:
            acc -= pass1[m + 1][1]
        m += 2
    return ('OK', acc)


def fmt12(fr):
    """精确分数 -> 12 位有效数字十进制字符串（JS: toPrecision(12)+parseFloat+String 的显示语义）"""
    if fr == 0:
        return '0'
    d = Decimal(fr.numerator) / Decimal(fr.denominator)
    if d == 0:
        return '0'
    if abs(d) > DOMAIN_LIMIT:
        raise ValueError('超出 oracle 显示域（>1e15）: %s' % d)
    exp = d.adjusted()
    q = Decimal(1).scaleb(exp - 11)
    r = d.quantize(q, rounding=ROUND_HALF_UP)
    s = format(r, 'f')
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    if s in ('-0', '+0'):
        s = '0'
    return s


def simulate(keys):
    """按 index.html 规格独立实现的 UI 状态机（Model B：单表达式字符串事实源）"""
    expr = ''
    just_evaluated = False
    error = False
    top_override = None
    eval_points = []  # 每次 "=" 实际求值的 (full, resultStr|None, errorKind|None)

    for k in keys:
        if error:
            if k == 'C' or k == 'back' or k.isdigit() or k == '.':
                expr = ''
                just_evaluated = False
                error = False
                top_override = None
            else:
                continue
        if k == 'C':
            expr = ''
            just_evaluated = False
            error = False
            top_override = None
        elif k == 'back':
            if expr == '':
                continue
            if just_evaluated:
                just_evaluated = False
                top_override = None
            expr = expr[:-1]
        elif k == '=':
            if expr == '':
                continue
            if just_evaluated and 'e' in expr.lower():
                continue
            full = expr[:-1] if is_op(expr[-1]) else expr
            st, v = eval_exact(full)
            if st != 'OK':
                top_override = disp(full) + ' ='
                error = True
                just_evaluated = False
                eval_points.append({'expr': full, 'result': None, 'error': st})
            else:
                res = fmt12(v)
                top_override = disp(full) + ' ='
                expr = res
                just_evaluated = True
                eval_points.append({'expr': full, 'result': res, 'error': None})
        elif k == '.':
            if just_evaluated:
                expr = '0.'
                just_evaluated = False
                top_override = None
            else:
                seg = segment(expr)
                if '.' not in seg:
                    expr += ('0.' if seg == '' else '.')
        elif k.isdigit():
            if just_evaluated:
                expr = k
                just_evaluated = False
                top_override = None
            else:
                seg = segment(expr)
                if seg == '0':
                    expr = expr[:-1] + k
                elif len(seg) < MAX_SEG:
                    expr += k
        elif is_op(k):
            if just_evaluated:
                if 'e' in expr.lower():
                    continue
                expr += k
                just_evaluated = False
                top_override = None
            elif expr == '':
                continue
            elif is_op(expr[-1]):
                expr = expr[:-1] + k
            else:
                expr += k

    return {
        'expr': expr,
        'justEvaluated': just_evaluated,
        'error': error,
        'topOverride': top_override,
        'eval_points': eval_points,
    }


def expected_main(st):
    if st['error']:
        return '错误'
    if st['justEvaluated']:
        return disp(st['expr'])
    seg = segment(st['expr'])
    return disp(seg) if seg else '0'


def expected_top(st):
    if st['topOverride'] is not None:
        return st['topOverride']
    return disp(st['expr']) if st['expr'] else ''


VECTORS = [
    ('basic_add',            ['7', '+', '3', '='], '四则-加法'),
    ('precedence',           ['2', '+', '3', '*', '4', '='], '乘法优先于加法'),
    ('float_add',            ['0', '.', '1', '+', '0', '.', '2', '='], '浮点噪声清理 0.1+0.2=0.3'),
    ('basic_div',            ['8', '/', '4', '='], '四则-除法'),
    ('div_zero',             ['5', '/', '0', '='], '除零 -> 错误'),
    ('decimal_mul',          ['3', '.', '5', '*', '2', '='], '小数乘法'),
    ('leading_dot',          ['.', '5', '+', '1', '='], '前导点补零 0.5'),
    ('chain',                ['1', '2', '+', '3', '.', '5', '*', '2', '='], '链式混合运算'),
    ('left_assoc_sub',       ['9', '-', '4', '-', '3', '='], '减法左结合'),
    ('left_assoc_div',       ['2', '0', '/', '4', '*', '3', '='], '除乘左结合'),
    ('backspace_digit',      ['1', '2', '3', 'back'], '退格删除数字'),
    ('backspace_op',         ['8', '*', '2', 'back', 'back'], '退格穿越运算符'),
    ('clear_mid',            ['9', '*', '9', 'C', '5', '+', '5', '='], '中途清除后重算'),
    ('dot_ignore',           ['1', '.', '.', '5', '+', '1', '='], '重复小数点忽略'),
    ('leading_zero',         ['0', '0', '5', '+', '5', '='], '前导零抑制'),
    ('float_mul',            ['9', '.', '9', '*', '9', '='], '浮点噪声清理 9.9*9=89.1'),
    ('third',                ['1', '/', '3', '='], '循环小数 12 位有效'),
    ('op_after_result',      ['7', '+', '3', '=', '*', '2', '='], '结果续算'),
    ('trailing_op_eq',       ['5', '+', '='], '尾部运算符被丢弃后求值'),
    ('replace_op',           ['5', '+', '*', '2', '='], '连续运算符替换'),
    ('negative_result',      ['3', '-', '5', '='], '负结果显示'),
    ('error_recover',        ['5', '/', '0', '=', 'C', '6', '+', '4', '='], '错误状态可恢复'),
    ('equals_empty',         ['='], '空表达式等号无操作'),
    ('backspace_after_result', ['7', '+', '3', '=', 'back'], '结果态退格进入编辑'),
    ('chained_decimal',      ['1', '/', '3', '=', '*', '3', '='], '非终止小数结果反馈续算'),
    ('two_thirds',           ['1', '/', '3', '=', '+', '1', '/', '3', '='], '小数结果反馈链式相加'),
]


def main():
    out = []
    for vid, keys, note in VECTORS:
        st = simulate(keys)
        out.append({
            'id': vid,
            'keys': keys,
            'note': note,
            'expected_main': expected_main(st),
            'expected_top': expected_top(st),
            'eval_points': st['eval_points'],
        })
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vectors.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('vectors.json 写入 %d 条向量' % len(out))
    for v in out:
        print('%-24s main=%-18r top=%r' % (v['id'], v['expected_main'], v['expected_top']))


if __name__ == '__main__':
    main()
