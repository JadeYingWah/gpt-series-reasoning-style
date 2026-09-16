"""stats.py —— 统计输出：总数、最新 3 条、最长笔记。"""
import sys

import storage


def main():
    storage.setup_stdio()
    notes = storage.load_notes()
    print("总笔记数：{}".format(len(notes)))
    if not notes:
        return 0

    latest = sorted(notes, key=lambda n: n.get("id", 0), reverse=True)[:3]
    print()
    print("最新 3 条：")
    for n in latest:
        print("  #{} [{}] {}".format(n.get("id", "?"), n.get("created_at", "?"), n.get("title", "")))

    longest = max(notes, key=lambda n: len(n.get("content") or ""))
    print()
    print("最长笔记：#{} 《{}》（内容 {} 字符）".format(
        longest.get("id", "?"), longest.get("title", ""), len(longest.get("content") or "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
