# -*- coding: utf-8 -*-
"""极简 CSV 记录解析（已修复双引号包裹字段）。

支持以双引号包裹的字段：
- 字段内的逗号、换行原样保留（不被当作分隔符）；
- 连续两个双引号 ``""`` 转义为字面双引号；
- 未被引号包裹的字段按逗号切分（与原实现一致）。

公开接口 ``parse_line(line)`` 的名称与签名保持不变。
调用方若传入完整记录（含引号内换行），即可解析跨行字段；
行尾的换行符仍按原实现剥离。
"""


def parse_line(line):
    """把一行 CSV 解析成字段列表。"""
    # 与修复前一致：仅剥离行尾换行符，其余字符原样进入解析。
    return _split_fields(line.rstrip("\n"))


def _split_fields(text):
    """按 CSV 规则把文本切成字段列表（单遍状态机）。"""
    fields = []
    buf = []
    in_quotes = False   # 当前是否位于引号包裹的字段内部
    field_open = False  # 当前字段是否已开始（用于判定引号是否可开启包裹）
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if in_quotes:
            if ch == '"':
                # "" 转义为字面引号，否则视为结束包裹。
                if i + 1 < n and text[i + 1] == '"':
                    buf.append('"')
                    i += 2
                    continue
                in_quotes = False
                i += 1
                continue
            # 引号内的逗号/换行等一律作为字面字符。
            buf.append(ch)
            i += 1
            continue

        if ch == ',':
            fields.append(''.join(buf))
            buf = []
            field_open = False
            i += 1
            continue

        if ch == '"' and not field_open:
            in_quotes = True
            field_open = True
            i += 1
            continue

        # 未包裹字段中的普通字符（含字段中途出现的孤立引号，按字面处理）。
        buf.append(ch)
        field_open = True
        i += 1

    fields.append(''.join(buf))
    return fields
