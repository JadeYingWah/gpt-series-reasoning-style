# -*- coding: utf-8 -*-
"""用法：python add.py "标题" "内容" [--tag 标签 ...]

新增一条笔记：自动记时间戳、自增 id，写入 notes.json。
标题不能为空（纯空白也算空）；内容允许为空；标签可选、可重复 --tag 传入多个。
"""
import argparse
import sys

import storage


def main():
    storage.ensure_utf8_stdio()
    parser = argparse.ArgumentParser(description="新增一条笔记")
    parser.add_argument("title", help="笔记标题（不能为空）")
    parser.add_argument("content", help="笔记内容（允许为空）")
    parser.add_argument("--tag", action="append", default=[], dest="tags",
                        metavar="标签", help="标签，可重复使用本选项添加多个")
    args = parser.parse_args()

    if not args.title.strip():
        print("错误：标题不能为空。", file=sys.stderr)
        sys.exit(1)

    notes = storage.load_notes()
    note = {
        "id": storage.next_id(notes),
        "title": args.title.strip(),
        "content": args.content,
        "tags": args.tags,
        "created_at": storage.now_iso(),
    }
    notes.append(note)
    storage.save_notes(notes)
    print("已添加笔记 #%d：%s" % (note["id"], note["title"]))


if __name__ == "__main__":
    main()
