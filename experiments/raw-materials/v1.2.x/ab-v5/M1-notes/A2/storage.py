"""共享存储与显示逻辑：四个命令脚本共用 notes.json 的读写与表格对齐输出。

存储文件固定位于本脚本所在目录，保证从任意工作目录运行时数据一致。
"""
import json
import os
import sys
import unicodedata
from time import strftime

NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.json")


def setup_stdio():
    """Windows 控制台默认 GBK，遇 emoji/生僻字会崩溃；尽力切换到 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def load_notes():
    """读取笔记列表。文件不存在返回空列表；JSON 损坏时报错退出，不做任何写入。"""
    if not os.path.exists(NOTES_FILE):
        return []
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(
            "错误：{} 已损坏或不可读（{}）。为防止数据丢失未做任何写入，"
            "请手工修复该文件后重试。".format(NOTES_FILE, e),
            file=sys.stderr,
        )
        raise SystemExit(1)
    if not isinstance(data, list):
        print("错误：{} 格式异常（顶层应为 JSON 数组）。".format(NOTES_FILE), file=sys.stderr)
        raise SystemExit(1)
    return [n for n in data if isinstance(n, dict)]


def save_notes(notes):
    """保存笔记列表：先写临时文件再原子替换，避免写一半损坏。"""
    tmp = NOTES_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, NOTES_FILE)


def next_id(notes):
    """自增 id：取现有最大 id + 1；即使文件被手工改出重复/缺失 id 也不会撞号。"""
    ids = [n["id"] for n in notes if isinstance(n.get("id"), int)]
    return (max(ids) if ids else 0) + 1


def new_note(notes, title, content, tags):
    """构造一条新笔记（时间戳 + 自增 id）。"""
    return {
        "id": next_id(notes),
        "title": title,
        "content": content,
        "tags": list(tags),
        "created_at": strftime("%Y-%m-%d %H:%M:%S"),
    }


def display_width(text):
    """终端显示宽度：CJK/全角字符按 2 列计，用于表格对齐。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1 for ch in text)


def pad(text, width):
    """按显示宽度右侧补空格。"""
    return text + " " * max(0, width - display_width(text))


def format_table(rows, headers):
    """按显示宽度对齐的表格文本。rows 为字符串列表的列表。"""
    widths = [display_width(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], display_width(cell))
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def line(row):
        return "| " + " | ".join(pad(c, widths[i]) for i, c in enumerate(row)) + " |"

    lines = [sep, line(headers), sep]
    lines.extend(line(r) for r in rows)
    lines.append(sep)
    return "\n".join(lines)
