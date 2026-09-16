# -*- coding: utf-8 -*-
"""极简 CSV 行解析。

支持 RFC 4180 风格的双引号包裹字段：
  * 引号字段内可出现分隔符逗号；
  * 引号字段内可出现换行符；
  * 字段内连续两个双引号 ``""`` 转义为一个字面双引号。

未加引号的字段保持原样（不做去空白、不做转义）。
"""


def parse_line(line):
    """把一行（或含引号内换行的多行）CSV 文本解析成字段列表。"""
    s = line.rstrip("\n")
    if not s:
        return [""]

    fields = []
    buf = []
    i = 0
    n = len(s)
    in_quotes = False

    while i < n:
        ch = s[i]

        if in_quotes:
            if ch == '"':
                # 连续两个引号 -> 字面引号
                if i + 1 < n and s[i + 1] == '"':
                    buf.append('"')
                    i += 2
                    continue
                # 单个引号 -> 结束引号段
                in_quotes = False
                i += 1
                continue
            buf.append(ch)
            i += 1
            continue

        if ch == ",":
            fields.append("".join(buf))
            buf = []
            i += 1
            continue

        # 只有位于字段起始位置的引号才具备包裹语义
        if ch == '"' and not buf:
            in_quotes = True
            i += 1
            continue

        buf.append(ch)
        i += 1

    fields.append("".join(buf))
    return fields
