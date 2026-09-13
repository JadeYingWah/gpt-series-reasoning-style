#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""add.py —— 新增一条笔记（自动记录时间戳、自增 id）。

用法：
    python add.py "标题" "内容" [--tag 标签]...

示例：
    python add.py "会议纪要" "讨论 Q3 计划" --tag 工作 --tag 计划
"""

import argparse
import sys

from storage import add_note, setup_stdio


def build_parser():
    parser = argparse.ArgumentParser(
        prog="add.py",
        description="新增一条笔记（自动记录时间戳、自增 id），可选打标签。",
    )
    parser.add_argument("title", help="笔记标题（不能为空）")
    parser.add_argument("content", help="笔记内容（可为空字符串）")
    parser.add_argument(
        "-t", "--tag", action="append", default=[], metavar="标签",
        help="为笔记打标签，可重复使用（如 --tag 工作 --tag 计划）",
    )
    return parser


def main(argv=None):
    setup_stdio()
    args = build_parser().parse_args(argv)

    title = args.title.strip()
    if not title:
        print("[错误] 标题不能为空（全空白也不行）。", file=sys.stderr)
        return 1

    tags = [t.strip() for t in args.tag if t.strip()]
    note = add_note(title, args.content, tags)
    tag_text = f"；标签：{'、'.join(note['tags'])}" if note["tags"] else ""
    print(f"[OK] 已新增笔记 #{note['id']}：{note['title']}（{note['created_at']}）{tag_text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
