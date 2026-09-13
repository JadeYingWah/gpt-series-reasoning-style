#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csv_parser.py — 单文件零依赖 CSV 解析器

用法:
    作为模块:  from csv_parser import parse; parse(text_or_bytes)
    命令行:    python csv_parser.py <file.csv>

语义决策（详见 evidence/证据报告.md）:
    - 逗号分隔；字段可被双引号包裹；引号内逗号/换行为字段内容；
      引号内两个连续双引号 ("") 转义为一个双引号
    - 行尾支持 \\n、\\r\\n、\\r，可混合；最后一个换行不产生多余空行
    - 空行（两个行尾之间无任何字符）解析为空列表 []；
      "" （引号包裹的空字段）解析为含一个空字符串的行
    - 字段前后空格按 RFC 4180 属于字段内容，原样保留
    - 非引号字段内的双引号按字面字符处理（与 Python csv 模块一致）
    - 严格模式错误：引号未闭合、引号闭合后出现多余字符 → ValueError
    - UTF-8 BOM：bytes 输入检测并跳过；str 输入剥离开头 \\ufeff
"""

import sys

__all__ = ["parse"]

_UTF8_BOM = b"\xef\xbb\xbf"

# 解析器状态
_S_FIELD_START = 0  # 字段起点（本字段尚无内容）
_S_UNQUOTED = 1     # 非引号字段内
_S_QUOTED = 2       # 引号字段内
_S_QUOTE_CLOSE = 3  # 引号字段刚闭合（仅允许逗号/行尾/EOF）


def _decode(data):
    """bytes -> str：检测并跳过 UTF-8 BOM 后按 UTF-8 解码；str 原样返回。"""
    if isinstance(data, str):
        return data
    if data.startswith(_UTF8_BOM):
        return data[3:].decode("utf-8")
    return data.decode("utf-8")


def parse(data):
    """解析 CSV 文本，返回列表的列表。

    参数 data: str 或 bytes（bytes 自动做 UTF-8 BOM 检测与跳过）。
    引号未闭合或引号闭合后有多余字符时抛出 ValueError。
    """
    text = _decode(data)
    if text.startswith("\ufeff"):
        text = text[1:]

    rows = []
    row = []
    field = []
    state = _S_FIELD_START

    i = 0
    n = len(text)
    while i < n:
        ch = text[i]

        if state == _S_QUOTED:
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"')  # "" 转义为一个双引号
                    i += 2
                else:
                    state = _S_QUOTE_CLOSE
                    i += 1
            else:
                field.append(ch)  # 引号内的逗号/换行/其他均为字段内容
                i += 1
            continue

        if state == _S_QUOTE_CLOSE and ch not in ",\r\n":
            raise ValueError(
                "引号闭合后出现多余字符 %r（第 %d 字段）" % (ch, len(row) + 1)
            )

        if ch == '"':
            if state == _S_FIELD_START:
                state = _S_QUOTED
            else:
                field.append(ch)  # 非引号字段内的引号按字面字符处理
            i += 1
            continue

        if ch == ",":
            row.append("".join(field))
            field = []
            state = _S_FIELD_START
            i += 1
            continue

        if ch == "\n" or ch == "\r":
            if ch == "\r" and i + 1 < n and text[i + 1] == "\n":
                i += 2  # \r\n 合并为一个行尾
            else:
                i += 1
            row.append("".join(field))
            field = []
            # 空行：整行无内容且无字段边界 → 空列表 []
            if state == _S_FIELD_START and len(row) == 1 and row[0] == "":
                rows.append([])
            else:
                rows.append(row)
            row = []
            state = _S_FIELD_START
            continue

        field.append(ch)
        if state == _S_FIELD_START:
            state = _S_UNQUOTED
        i += 1

    # EOF 收尾
    if state == _S_QUOTED:
        raise ValueError("引号未闭合（输入在引号字段内结束）")
    if state != _S_FIELD_START or row or field:
        row.append("".join(field))
        rows.append(row)
    return rows


def main(argv):
    if len(argv) != 2:
        print("用法: python csv_parser.py <file.csv>", file=sys.stderr)
        return 2
    path = argv[1]
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as exc:
        print("错误：无法读取文件 %s: %s" % (path, exc), file=sys.stderr)
        return 1
    try:
        result = parse(data)
    except (ValueError, UnicodeDecodeError) as exc:
        print("错误：CSV 解析失败: %s" % exc, file=sys.stderr)
        return 1
    for row in result:
        print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
