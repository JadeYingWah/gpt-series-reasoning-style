#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""list.py —— 列出全部笔记，或用 --tag 按标签过滤（表格对齐输出）。

用法：
    python list.py
    python list.py --tag 工作
"""

import argparse
import sys

from storage import load_notes, note_tags, one_line, render_table, setup_stdio, sort_notes


def main(argv=None):
    setup_stdio()
    parser = argparse.ArgumentParser(
        prog="list.py",
        description="列出全部笔记，或按标签过滤（精确匹配）。",
    )
    parser.add_argument("--tag", metavar="标签", help="只列出包含该标签的笔记")
    args = parser.parse_args(argv)

    notes = load_notes()
    if args.tag is not None:
        notes = [n for n in notes if args.tag in note_tags(n)]

    if not notes:
        if args.tag is not None:
            print(f"没有包含标签「{args.tag}」的笔记。")
        else:
            print('暂无笔记。先用 python add.py "标题" "内容" 添加一条吧。')
        return 0

    rows = [
        [
            n.get("id", "?"),
            one_line(n.get("title", "")),
            "、".join(note_tags(n)),
            n.get("created_at", ""),
        ]
        for n in sort_notes(notes)
    ]
    print(render_table(["ID", "标题", "标签", "创建时间"], rows))
    scope = f"（已按标签「{args.tag}」过滤）" if args.tag else ""
    print(f"共 {len(rows)} 条笔记{scope}。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
