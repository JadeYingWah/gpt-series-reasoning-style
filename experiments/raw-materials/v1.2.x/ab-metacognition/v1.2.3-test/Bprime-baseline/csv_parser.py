#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CSV 解析器：单文件、零依赖。

约束
----
* 不 import 任何第三方库，也不 import 标准库 csv 模块（解析逻辑全部自实现）。
* Python 3.7+。

公开接口
--------
parse(text)                  -> list[list[str]]   解析字符串
parse_bytes(data, encoding)  -> list[list[str]]   解析字节（自动 BOM 检测）
read_file(path, encoding)    -> list[list[str]]   读文件并解析
main(argv)                   -> int               命令行入口

语义（与 RFC 4180 / Python 标准库 csv 默认方言一致，逐条有测试覆盖）
------------------------------------------------------------------
1. 分隔符为逗号，字段可用双引号包裹。
2. 引号内可含逗号、换行（\\n、\\r\\n、\\r）与转义双引号（"" 表示一个 "）。
3. 行尾支持 \\n、\\r\\n、\\r，且允许同一文件内混用。
4. 空格是数据：字段前后空格原样保留（不做 strip）；引号只在字段起始位置
   才具有"开启引用"的含义，例如  "a" 解析为  "a"（含引号与空格）。
5. 空字段（"a,,"）得到空字符串；完全空行得到空行 []。
6. 文件末尾无换行符时，最后一行照常产出；文件以换行结尾时不产生尾部空行。
7. 引号未闭合时按"到输入结尾自动闭合"处理（容错），不抛异常。
8. 输入开头的 UTF-8 BOM 被跳过（UTF-16 LE/BE BOM 亦可识别，见 _decode）。
"""

import sys

__all__ = ["parse", "parse_bytes", "read_file", "CsvError", "main"]

BOM_UTF8 = b"\xef\xbb\xbf"
BOM_UTF16_LE = b"\xff\xfe"
BOM_UTF16_BE = b"\xfe\xff"
BOM_STR = "\ufeff"

QUOTE = '"'
COMMA = ","
CR = "\r"
LF = "\n"


class CsvError(ValueError):
    """解析/解码输入失败时抛出。"""


def _decode(data, encoding=None):
    """bytes -> str，按 BOM 推断编码；同时剥掉 BOM。"""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data 必须是 bytes，收到 %s" % type(data).__name__)
    if encoding is None:
        if data.startswith(BOM_UTF8):
            encoding = "utf-8-sig"
        elif data.startswith(BOM_UTF16_LE) or data.startswith(BOM_UTF16_BE):
            encoding = "utf-16"
        else:
            encoding = "utf-8"
    try:
        text = bytes(data).decode(encoding)
    except (UnicodeDecodeError, LookupError) as exc:
        raise CsvError("解码失败（encoding=%s）：%s" % (encoding, exc)) from exc
    # 未走 codec 自动剥离时（例如调用方显式传入 utf-8），手工去掉 BOM
    if text.startswith(BOM_STR):
        text = text[1:]
    return text


def parse(text):
    """把 CSV 文本解析成 list[list[str]]。

    单趟字符级状态机：O(n) 时间，除结果外不随输入规模增长的额外内存。
    """
    if not isinstance(text, str):
        raise TypeError("text 必须是 str，收到 %s" % type(text).__name__)
    if text.startswith(BOM_STR):
        text = text[1:]

    rows = []
    row = []
    field = []          # 当前字段的字符缓冲
    in_quotes = False   # 是否处于引号内部
    quoted = False      # 当前字段是否以引号开头（决定后续 " 是否字面量）

    i = 0
    n = len(text)
    while i < n:
        ch = text[i]

        if in_quotes:
            if ch == QUOTE:
                if i + 1 < n and text[i + 1] == QUOTE:  # "" -> 一个字面 "
                    field.append(QUOTE)
                    i += 2
                    continue
                in_quotes = False                        # 闭合引号
                i += 1
                continue
            field.append(ch)
            i += 1
            continue

        if ch == QUOTE:
            if not field and not quoted:                 # 字段起始的引号才特殊
                in_quotes = True
                quoted = True
                i += 1
                continue
            field.append(ch)                             # 字段中间的引号是数据
            i += 1
            continue

        if ch == COMMA:
            row.append("".join(field))
            field = []
            quoted = False
            i += 1
            continue

        if ch == CR or ch == LF:
            if ch == CR and i + 1 < n and text[i + 1] == LF:
                i += 1                                   # \r\n 视作一个行尾
            i += 1
            if not field and not quoted and not row:
                rows.append([])                          # 完全空行 -> []
            else:
                row.append("".join(field))
                rows.append(row)
            row = []
            field = []
            quoted = False
            continue

        field.append(ch)
        i += 1

    # 文件末尾（in_quotes 未闭合时在此容错收尾）
    if field or quoted or row:
        row.append("".join(field))
        rows.append(row)

    return rows


def parse_bytes(data, encoding=None):
    """解析 bytes 输入，自动做 BOM 检测与剥离。"""
    return parse(_decode(data, encoding))


def read_file(path, encoding=None):
    """读取文件并解析；文件不存在或解码失败抛 CsvError/OSError。"""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        raise CsvError("读取文件失败：%s" % exc) from exc
    return parse_bytes(data, encoding)


def main(argv=None):
    """命令行：python csv_parser.py <file.csv> [--json] [--encoding ENC]

    解析结果写 stdout（每行一个 row 的 Python 字面量），统计信息写 stderr。
    """
    import json  # 标准库，仅用于 --json 输出

    argv = list(sys.argv[1:] if argv is None else argv)
    json_mode = False
    encoding = None
    args = []
    it = iter(range(len(argv)))
    for idx in it:
        arg = argv[idx]
        if arg == "--json":
            json_mode = True
        elif arg == "--encoding":
            nxt = idx + 1
            if nxt >= len(argv):
                sys.stderr.write("错误：--encoding 缺少参数\n")
                return 2
            encoding = argv[nxt]
            try:
                next(it)
            except StopIteration:
                pass
        elif arg in ("-h", "--help"):
            sys.stdout.write(
                "用法: python csv_parser.py <file.csv> [--json] [--encoding ENC]\n"
            )
            return 0
        else:
            args.append(arg)

    if len(args) != 1:
        sys.stderr.write("用法: python csv_parser.py <file.csv> [--json] [--encoding ENC]\n")
        return 2

    try:
        rows = read_file(args[0], encoding)
    except CsvError as exc:
        sys.stderr.write("错误：%s\n" % exc)
        return 1

    if json_mode:
        sys.stdout.write(json.dumps(rows, ensure_ascii=False) + "\n")
    else:
        out = []
        for row in rows:
            out.append("[" + ", ".join(repr(cell) for cell in row) + "]")
        sys.stdout.write("\n".join(out) + ("\n" if out else ""))

    cols = max((len(r) for r in rows), default=0)
    sys.stderr.write("rows=%d max_cols=%d\n" % (len(rows), cols))
    return 0


if __name__ == "__main__":
    sys.exit(main())
