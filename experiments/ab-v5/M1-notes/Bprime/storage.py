# -*- coding: utf-8 -*-
"""storage.py —— 共享存储与格式化工具。

所有命令共用 notes.json 的读写逻辑：
- 数据文件位于本脚本同目录下的 notes.json，由 add.py 首次运行时自动创建
- 读取时自动修复重复/非法 id（并写回），损坏的 JSON 会报错退出而不是静默丢失
- 写入采用「先写临时文件再原子替换」，避免中途失败写坏数据
"""
import json
import os
import sys
import unicodedata
from datetime import datetime

NOTES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.json")


def ensure_utf8_stdio():
    """Windows 控制台可能是 GBK，强制 UTF-8 输出并用 replace 兜底，
    避免特殊字符（emoji 等）导致打印崩溃。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def load_notes():
    """读取全部笔记。文件不存在返回 []；JSON 损坏/格式错误时报错退出（exit 2）。"""
    if not os.path.exists(NOTES_PATH):
        return []
    try:
        with open(NOTES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print("错误：notes.json 读取失败（%s），文件可能已损坏。" % e, file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, list):
        print("错误：notes.json 格式不正确（顶层应为数组）。", file=sys.stderr)
        sys.exit(2)
    notes, changed = _sanitize(data)
    if changed:  # 自愈：把修复结果写回
        save_notes(notes)
    return notes


def _sanitize(notes):
    """清理数据：丢弃非对象项、补齐缺失字段、修复重复/非法 id。

    修复规则：非法（非正整数）或重复的 id，从当前最大 id+1 起重新编号。
    返回 (清洗后的列表, 是否发生修改)。
    """
    cleaned = []
    for item in notes:
        if not isinstance(item, dict):
            continue
        tags = item.get("tags")
        cleaned.append({
            "id": item.get("id"),
            "title": str(item.get("title", "")),
            "content": str(item.get("content", "")),
            "tags": [str(t) for t in tags if str(t).strip()] if isinstance(tags, list) else [],
            "created_at": str(item.get("created_at", "")),
        })

    max_id = 0
    for n in cleaned:
        try:
            max_id = max(max_id, int(n["id"]))
        except (TypeError, ValueError):
            pass

    seen = set()
    changed = False
    for n in cleaned:
        try:
            nid = int(n["id"])
        except (TypeError, ValueError):
            nid = None
        if nid is None or nid <= 0 or nid in seen:
            max_id += 1
            n["id"] = max_id
            changed = True
        else:
            if n["id"] != nid:
                changed = True
            n["id"] = nid
            seen.add(nid)
    return cleaned, changed


def save_notes(notes):
    """原子写入 notes.json（先写 .tmp 再替换）。"""
    tmp = NOTES_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, NOTES_PATH)


def next_id(notes):
    """自增 id：现有最大 id + 1，空库从 1 开始。"""
    return max((n["id"] for n in notes), default=0) + 1


def now_iso():
    """本地时间的 ISO 时间戳（精确到秒）。"""
    return datetime.now().isoformat(timespec="seconds")


def fmt_time(iso_str):
    """'2026-09-13T10:00:00' -> '2026-09-13 10:00'；解析失败原样返回。"""
    try:
        return datetime.fromisoformat(iso_str).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return iso_str


# ---------- 终端对齐辅助（中文/全角按 2 列宽计算） ----------

def display_width(s):
    w = 0
    for ch in s:
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


def truncate_width(s, max_width):
    """按显示宽度截断，超出以 … 结尾。"""
    if display_width(s) <= max_width:
        return s
    w = 0
    out = []
    for ch in s:
        cw = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        if w + cw > max_width - 1:
            break
        out.append(ch)
        w += cw
    return "".join(out) + "…"


def pad_width(s, width):
    """按显示宽度右侧补空格。"""
    return s + " " * max(0, width - display_width(s))


# ---------- 共享表格输出（list.py / search.py / stats.py 复用） ----------

TABLE_COLS = ("ID", "标题", "标签", "时间", "内容")
TABLE_WIDTHS = [4, 24, 14, 16, 30]


def print_table(notes):
    widths = list(TABLE_WIDTHS)
    if notes:
        widths[0] = max(widths[0], max(len(str(n["id"])) for n in notes))
    last = len(widths) - 1

    header = [pad_width(TABLE_COLS[i], widths[i]) for i in range(last)]
    header.append(TABLE_COLS[last])
    print("  ".join(header).rstrip())
    print("  ".join("-" * w for w in widths))

    for n in notes:
        row = [
            str(n["id"]),
            truncate_width(n["title"], widths[1]),
            truncate_width(",".join(n["tags"]), widths[2]),
            truncate_width(fmt_time(n["created_at"]), widths[3]),
            truncate_width(n["content"].replace("\r", "").replace("\n", "\\n"), widths[4]),
        ]
        cells = [pad_width(row[i], widths[i]) for i in range(last)]
        cells.append(row[last])
        print("  ".join(cells).rstrip())
