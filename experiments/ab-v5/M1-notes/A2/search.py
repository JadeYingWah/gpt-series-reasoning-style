"""search.py 关键词 —— 标题+内容模糊搜索（大小写不敏感）。"""
import argparse
import sys

import storage


def main():
    storage.setup_stdio()
    parser = argparse.ArgumentParser(description="搜索笔记（标题+内容，大小写不敏感）")
    parser.add_argument("keyword", help="搜索关键词")
    args = parser.parse_args()

    keyword = args.keyword.strip().lower()
    if not keyword:
        print("错误：关键词不能为空。", file=sys.stderr)
        return 1

    notes = storage.load_notes()
    hits = [
        n for n in notes
        if keyword in (n.get("title") or "").lower()
        or keyword in (n.get("content") or "").lower()
    ]
    if not hits:
        print("没有包含“{}”的笔记。".format(args.keyword))
        return 0

    rows = [
        [
            str(n.get("id", "?")),
            n.get("created_at", "?"),
            ",".join(n.get("tags") or []),
            n.get("title", ""),
            (n.get("content") or "").replace("\n", " "),
        ]
        for n in hits
    ]
    print(storage.format_table(rows, ["ID", "时间", "标签", "标题", "内容"]))
    print("共 {} 条匹配。".format(len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
