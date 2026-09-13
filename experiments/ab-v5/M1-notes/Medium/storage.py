# -*- coding: utf-8 -*-
"""storage.py —— 命令行笔记工具的共享存储与输出逻辑。

所有命令（add/list/search/stats）共用本模块：
- notes.json 读写（缺失自动创建、损坏时保护数据、原子写入）
- 自增 id 生成（现有最大 id + 1，天然避免重复 id）
- 终端对齐表格渲染（中文全角字符按 2 列宽计算）
"""

import json
import os
import sys
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
NOTES_FILE = BASE_DIR / "notes.json"


def setup_stdio():
    """输出容错：终端编码不支持某字符时替换为替代符而非崩溃。

    不改变终端编码本身（避免在 GBK 控制台强制 UTF-8 反而乱码）。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def load_notes():
    """读取 notes.json 并返回笔记列表；文件缺失或为空时自动创建空库。

    文件损坏（非法 JSON / 顶层不是数组）时直接报错退出，不覆盖旧数据。
    """
    if not NOTES_FILE.exists():
        save_notes([])
        return []
    try:
        raw = NOTES_FILE.read_text(encoding="utf-8").strip()
    except OSError as exc:
        sys.exit(f"[错误] 无法读取 {NOTES_FILE.name}：{exc}")
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.exit(f"[错误] {NOTES_FILE.name} 内容不是合法 JSON（{exc}），已停止操作以保护数据。")
    if not isinstance(data, list):
        sys.exit(f"[错误] {NOTES_FILE.name} 格式异常（顶层应为数组），已停止操作以保护数据。")
    return [item for item in data if isinstance(item, dict)]


def save_notes(notes):
    """原子写入 notes.json（先写同目录临时文件，再 os.replace 原子替换）。"""
    tmp_fd, tmp_path = tempfile.mkstemp(
        prefix=".notes-", suffix=".tmp", dir=str(NOTES_FILE.parent)
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            json.dump(notes, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp_path, NOTES_FILE)
    except OSError as exc:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        sys.exit(f"[错误] 无法写入 {NOTES_FILE.name}：{exc}")


def next_id(notes):
    """自增 id：现有最大 id + 1；非法 id 字段自动跳过，避免重复 id。"""
    max_id = 0
    for note in notes:
        try:
            max_id = max(max_id, int(note.get("id", 0)))
        except (TypeError, ValueError):
            continue
    return max_id + 1


def add_note(title, content, tags):
    """新增一条笔记并立即落盘，返回新笔记字典。"""
    notes = load_notes()
    note = {
        "id": next_id(notes),
        "title": title,
        "content": content,
        "tags": list(tags),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    notes.append(note)
    save_notes(notes)
    return note


def note_tags(note):
    """安全取笔记标签列表（字段损坏时返回空列表）。"""
    tags = note.get("tags", [])
    return tags if isinstance(tags, list) else []


def sort_notes(notes, reverse=False):
    """按 id 数值排序（非法 id 视为 0）。"""
    return sorted(
        notes,
        key=lambda n: n.get("id") if isinstance(n.get("id"), int) else 0,
        reverse=reverse,
    )


def one_line(text):
    """压平换行/制表符/多余空白，保证表格单行显示。"""
    return " ".join(str(text).split())


def _char_width(ch):
    """单字符显示宽度：全角/宽字符按 2，其余按 1（组合字符按 0）。

    说明：East Asian Ambiguous 字符（如 ·、±）按 1 列计（西文终端惯例），
    个别中文终端下此类字符可能造成 1 列对齐误差。
    """
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def display_width(text):
    """字符串的终端显示列宽。"""
    return sum(_char_width(ch) for ch in str(text))


def truncate(text, limit):
    """按显示宽度截断文本，超出部分以 ASCII 省略号 ... 结尾。"""
    text = str(text)
    if display_width(text) <= limit:
        return text
    out = []
    width = 0
    for ch in text:
        cw = _char_width(ch)
        if width + cw > limit - 3:
            break
        out.append(ch)
        width += cw
    return "".join(out) + "..."


def pad(text, width):
    """按显示宽度在右侧补空格。"""
    gap = width - display_width(text)
    return str(text) + " " * max(gap, 0)


def render_table(headers, rows):
    """渲染 ASCII 边框的对齐表格。"""
    rows = [[str(cell) for cell in row] for row in rows]
    widths = [display_width(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], display_width(cell))
    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    lines = [
        border,
        "| " + " | ".join(pad(h, widths[i]) for i, h in enumerate(headers)) + " |",
        border,
    ]
    for row in rows:
        lines.append("| " + " | ".join(pad(cell, widths[i]) for i, cell in enumerate(row)) + " |")
    lines.append(border)
    return "\n".join(lines)
