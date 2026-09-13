"""add.py "标题" "内容" [--tag 标签]... —— 新增笔记（自动记时间戳、自增 id）。"""
import argparse
import sys

import storage


def main():
    storage.setup_stdio()
    parser = argparse.ArgumentParser(description="新增一条笔记")
    parser.add_argument("title", help="笔记标题（不能为空）")
    parser.add_argument("content", help="笔记内容")
    parser.add_argument("--tag", dest="tags", action="append", default=[],
                        metavar="标签", help="标签，可重复使用打多个标签")
    args = parser.parse_args()

    title = args.title.strip()
    if not title:
        print("错误：标题不能为空。", file=sys.stderr)
        return 1

    notes = storage.load_notes()
    note = storage.new_note(notes, title, args.content, args.tags)
    notes.append(note)
    storage.save_notes(notes)
    tag_note = "，标签：{}".format(",".join(note["tags"])) if note["tags"] else ""
    print("已添加笔记 #{}：{}{}".format(note["id"], title, tag_note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
