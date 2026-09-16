# -*- coding: utf-8 -*-
"""用法：python search.py 关键词

在标题和内容中做模糊搜索，大小写不敏感。命中则表格输出，未命中提示并正常退出。
"""
import argparse
import sys

import storage


def main():
    storage.ensure_utf8_stdio()
    parser = argparse.ArgumentParser(description="按关键词搜索笔记（标题+内容，大小写不敏感）")
    parser.add_argument("keyword", help="搜索关键词")
    args = parser.parse_args()

    kw = args.keyword.lower()
    notes = storage.load_notes()
    hits = [n for n in notes
            if kw in n["title"].lower() or kw in n["content"].lower()]

    if not hits:
        print("（未找到包含「%s」的笔记）" % args.keyword)
        return

    storage.print_table(hits)
    print("共 %d 条匹配「%s」" % (len(hits), args.keyword))


if __name__ == "__main__":
    main()
