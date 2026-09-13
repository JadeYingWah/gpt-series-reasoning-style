"""list.py [--tag 标签] —— 列出全部笔记，或按标签过滤（表格对齐输出）。"""
import argparse
import sys

import storage

CONTENT_MAX_CHARS = 20  # 内容列超长截断显示


def brief(content):
    content = (content or "").replace("\n", " ")
    if len(content) > CONTENT_MAX_CHARS:
        content = content[: CONTENT_MAX_CHARS - 3] + "..."
    return content


def main():
    storage.setup_stdio()
    parser = argparse.ArgumentParser(description="列出笔记")
    parser.add_argument("--tag", metavar="标签", help="只列出带该标签的笔记")
    args = parser.parse_args()

    notes = storage.load_notes()
    if args.tag is not None:
        notes = [n for n in notes if args.tag in (n.get("tags") or [])]

    if not notes:
        if args.tag is not None:
            print('没有带标签“{}”的笔记。'.format(args.tag))
        else:
            print("暂无笔记。先用 add.py 添加一条吧。")
        return 0

    rows = [
        [
            str(n.get("id", "?")),
            n.get("created_at", "?"),
            ",".join(n.get("tags") or []),
            n.get("title", ""),
            brief(n.get("content")),
        ]
        for n in notes
    ]
    print(storage.format_table(rows, ["ID", "时间", "标签", "标题", "内容"]))
    print("共 {} 条笔记。".format(len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
