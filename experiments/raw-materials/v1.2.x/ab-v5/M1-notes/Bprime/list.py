# -*- coding: utf-8 -*-
"""用法：python list.py [--tag 标签]

列出全部笔记，或按标签精确过滤。表格对齐输出（中文按 2 列宽计算）。
"""
import argparse
import sys

import storage


def main():
    storage.ensure_utf8_stdio()
    parser = argparse.ArgumentParser(description="列出笔记（可按标签过滤）")
    parser.add_argument("--tag", metavar="标签", help="按标签过滤（精确匹配）")
    args = parser.parse_args()

    notes = storage.load_notes()
    if args.tag is not None:
        notes = [n for n in notes if args.tag in n["tags"]]

    if not notes:
        if args.tag is None:
            print("（暂无笔记，先用 add.py 添加一条吧）")
        else:
            print("（没有标签为「%s」的笔记）" % args.tag)
        return

    storage.print_table(notes)
    tail = "（标签：%s）" % args.tag if args.tag else ""
    print("共 %d 条%s" % (len(notes), tail))


if __name__ == "__main__":
    main()
