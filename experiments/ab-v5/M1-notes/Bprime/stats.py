# -*- coding: utf-8 -*-
"""用法：python stats.py

统计输出：笔记总数、最新 3 条（按创建时间倒序）、最长笔记（按内容字数）。
"""
import sys

import storage


def main():
    storage.ensure_utf8_stdio()
    notes = storage.load_notes()
    print("总笔记数：%d" % len(notes))

    if not notes:
        print("最新 3 条：（无）")
        print("最长笔记：（无）")
        return

    # ISO 时间戳按字符串排序即时间排序；同秒内以 id 大者为新
    latest = sorted(notes, key=lambda n: (n["created_at"], n["id"]), reverse=True)[:3]
    print("最新 3 条：")
    storage.print_table(latest)

    longest = max(notes, key=lambda n: len(n["content"]))
    print("最长笔记：#%d《%s》内容 %d 字" % (longest["id"], longest["title"], len(longest["content"])))


if __name__ == "__main__":
    main()
