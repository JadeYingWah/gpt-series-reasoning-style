#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""search.py —— 按关键词模糊搜索标题与内容（大小写不敏感）。

用法：
    python search.py 关键词
"""

import argparse
import sys

from storage import (
    load_notes,
    note_tags,
    one_line,
    render_table,
    setup_stdio,
    sort_notes,
    truncate,
)


def main(argv=None):
    setup_stdio()
    parser = argparse.ArgumentParser(
        prog="search.py",
        description="按关键词模糊搜索笔记标题与内容（大小写不敏感）。",
    )
    parser.add_argument("keyword", help="搜索关键词")
    args = parser.parse_args(argv)

    keyword = args.keyword.strip()
    if not keyword:
        print("[错误] 关键词不能为空（全空白也不行）。", file=sys.stderr)
        return 1

    kw = keyword.casefold()
    hits = [
        n for n in load_notes()
        if kw in one_line(n.get("title", "")).casefold()
        or kw in one_line(n.get("content", "")).casefold()
    ]

    if not hits:
        print(f"未找到包含「{keyword}」的笔记。")
        return 0

    rows = [
        [
            n.get("id", "?"),
            one_line(n.get("title", "")),
            truncate(one_line(n.get("content", "")), 40),
            "、".join(note_tags(n)),
            n.get("created_at", ""),
        ]
        for n in sort_notes(hits)
    ]
    print(render_table(["ID", "标题", "内容预览", "标签", "创建时间"], rows))
    print(f"共匹配 {len(rows)} 条笔记。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
