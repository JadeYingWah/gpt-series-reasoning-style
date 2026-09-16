#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stats.py —— 笔记统计：总数、最新 3 条、最长笔记。

用法：
    python stats.py
"""

import sys

from storage import (
    load_notes,
    one_line,
    render_table,
    setup_stdio,
    sort_notes,
    truncate,
)

LATEST_COUNT = 3


def main(argv=None):
    setup_stdio()
    notes = load_notes()
    print(f"笔记总数：{len(notes)}")

    if not notes:
        print("（暂无笔记）")
        return 0

    print(f"\n最新 {LATEST_COUNT} 条：")
    rows = [
        [n.get("id", "?"), one_line(n.get("title", "")), n.get("created_at", "")]
        for n in sort_notes(notes, reverse=True)[:LATEST_COUNT]
    ]
    print(render_table(["ID", "标题", "创建时间"], rows))

    longest = max(notes, key=lambda n: len(str(n.get("content", ""))))
    length = len(str(longest.get("content", "")))
    print(f"\n最长笔记：#{longest.get('id', '?')}《{one_line(longest.get('title', ''))}》—— 内容 {length} 字")
    print(f"内容预览：{truncate(one_line(longest.get('content', '')), 60)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
