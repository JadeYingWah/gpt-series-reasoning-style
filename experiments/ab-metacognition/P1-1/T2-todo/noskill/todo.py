#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""todo.py —— 单文件、零依赖的命令行待办清单工具。

用法：
    python todo.py add "标题"      新增待办（自增 id / 默认未完成 / 记录创建时间）
    python todo.py done <id>      标记指定 id 为已完成
    python todo.py list           列出未完成的待办（表格对齐）
    python todo.py list --all     列出全部待办
    python todo.py rm <id>        删除指定 id 的待办

数据文件：默认 <本脚本所在目录>/todos.json，首次写入时自动创建。
可用环境变量 TODO_FILE 指定其他路径（供自动化测试隔离使用）。

退出码：
    0  成功
    1  运行期错误（如 id 不存在）
    2  用法错误（如标题为空、id 不是整数、未知命令）

JSON 结构（UTF-8，indent=2）：
    [{"id": 1, "title": "买牛奶", "done": false, "created_at": "2026-09-13T22:10:00"}, ...]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import unicodedata
from datetime import datetime

# 标题在表格中的最大展示宽度（超出以 … 截断，仅影响显示，不截断存储数据）
TITLE_COL_MAX = 40
BACKUP_SUFFIX = ".bak"


# --------------------------------------------------------------------------
# 输出基础设施
# --------------------------------------------------------------------------
def _force_utf8() -> None:
    """Windows 控制台默认 GBK，emoji / 特殊符号会抛 UnicodeEncodeError，这里强制 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - 流已被替换或不支持重配置时忽略
            pass


def info(msg: str) -> None:
    print(msg)


def warn(msg: str) -> None:
    print("警告：" + msg, file=sys.stderr)


def die(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


# --------------------------------------------------------------------------
# 宽度计算：CJK / 全角 / emoji 在等宽终端里占两列
# --------------------------------------------------------------------------
def _char_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def display_width(text: str) -> int:
    return sum(_char_width(ch) for ch in text)


def pad_right(text: str, width: int) -> str:
    return text + " " * max(0, width - display_width(text))


def pad_left(text: str, width: int) -> str:
    return " " * max(0, width - display_width(text)) + text


def truncate(text: str, max_width: int) -> str:
    """按显示宽度截断，末尾补 …（占 1 列）。"""
    if display_width(text) <= max_width:
        return text
    out, used = [], 0
    for ch in text:
        cw = _char_width(ch)
        if used + cw > max_width - 1:
            break
        out.append(ch)
        used += cw
    return "".join(out) + "…"


def one_line(text: str) -> str:
    """把换行 / 制表符转成字面转义，保证表格每行只有一行。存储数据不受影响。"""
    return (
        text.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


# --------------------------------------------------------------------------
# 数据读写
# --------------------------------------------------------------------------
def data_path() -> str:
    override = os.environ.get("TODO_FILE")
    if override:
        return os.path.abspath(override)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")


def _backup(path: str) -> None:
    try:
        shutil.copy2(path, path + BACKUP_SUFFIX)
    except OSError:
        pass


def load(path: str) -> list:
    """读取待办。任何异常情况下都不崩溃，退化为「空清单」并在 stderr 给出警告。"""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        warn("数据文件无法读取（%s），本次按空清单处理。" % exc)
        return []

    if not raw.strip():
        return []

    try:
        data = json.loads(raw)
    except ValueError as exc:
        _backup(path)
        warn("数据文件不是合法 JSON（%s），已备份为 %s，本次按空清单处理。"
             % (exc, path + BACKUP_SUFFIX))
        return []

    if not isinstance(data, list):
        _backup(path)
        warn("数据文件结构不是数组，已备份为 %s，本次按空清单处理。"
             % (path + BACKUP_SUFFIX))
        return []

    items, dropped = [], 0
    for entry in data:
        if not isinstance(entry, dict):
            dropped += 1
            continue
        try:
            item_id = int(entry.get("id"))
        except (TypeError, ValueError):
            dropped += 1
            continue
        title = entry.get("title")
        if not isinstance(title, str):
            dropped += 1
            continue
        items.append(
            {
                "id": item_id,
                "title": title,
                "done": bool(entry.get("done", False)),
                "created_at": entry.get("created_at")
                if isinstance(entry.get("created_at"), str)
                else "",
            }
        )
    if dropped:
        warn("数据文件中有 %d 条记录格式非法，已忽略。" % dropped)
    return items


def save(path: str, items: list) -> None:
    """原子写入：先写临时文件再 os.replace，避免写一半留下损坏的 todos.json。"""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".todos-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(items, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# --------------------------------------------------------------------------
# 命令实现
# --------------------------------------------------------------------------
def next_id(items: list) -> int:
    """取现有最大 id + 1，保证删除后不会复用（重复）id。"""
    return (max((item["id"] for item in items), default=0)) + 1


def cmd_add(args: argparse.Namespace) -> int:
    title = " ".join(args.title).strip() if args.title else ""
    if not title:
        die("错误：标题不能为空或只包含空白字符。用法：python todo.py add \"标题\"", 2)

    path = data_path()
    items = load(path)
    item = {
        "id": next_id(items),
        "title": title,
        "done": False,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    items.append(item)
    save(path, items)
    info("已添加 #%d：%s" % (item["id"], one_line(title)))
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    path = data_path()
    items = load(path)
    for item in items:
        if item["id"] == args.id:
            if item["done"]:
                info("#%d 已经是完成状态，无需重复标记。" % args.id)
                return 0
            item["done"] = True
            save(path, items)
            info("已完成 #%d：%s" % (args.id, one_line(item["title"])))
            return 0
    die("错误：找不到 id 为 %d 的待办。可用 python todo.py list --all 查看现有待办。" % args.id, 1)


def cmd_rm(args: argparse.Namespace) -> int:
    path = data_path()
    items = load(path)
    for index, item in enumerate(items):
        if item["id"] == args.id:
            del items[index]
            save(path, items)
            info("已删除 #%d：%s" % (args.id, one_line(item["title"])))
            return 0
    die("错误：找不到 id 为 %d 的待办。可用 python todo.py list --all 查看现有待办。" % args.id, 1)


def render_table(items: list) -> None:
    headers = ("ID", "状态", "创建时间", "标题")
    rows = []
    for item in items:
        rows.append(
            (
                str(item["id"]),
                "已完成" if item["done"] else "未完成",
                item.get("created_at") or "-",
                truncate(one_line(item["title"]), TITLE_COL_MAX),
            )
        )
    widths = [
        max(display_width(headers[i]), *(display_width(r[i]) for r in rows)) if rows
        else display_width(headers[i])
        for i in range(len(headers))
    ]
    # ID 右对齐，其余左对齐
    line = "%s | %s | %s | %s" % (
        pad_left(headers[0], widths[0]),
        pad_right(headers[1], widths[1]),
        pad_right(headers[2], widths[2]),
        pad_right(headers[3], widths[3]),
    )
    # 分隔行使用与数据行相同的列分隔位置（“ | ” 连接），保证整张表共用一套栅格
    sep = " | ".join("-" * w for w in widths)
    print(line.rstrip())
    print(sep.rstrip())
    for row in rows:
        print(
            (
                "%s | %s | %s | %s"
                % (
                    pad_left(row[0], widths[0]),
                    pad_right(row[1], widths[1]),
                    pad_right(row[2], widths[2]),
                    pad_right(row[3], widths[3]),
                )
            ).rstrip()
        )


def cmd_list(args: argparse.Namespace) -> int:
    items = load(data_path())
    if args.all:
        shown = items
    else:
        shown = [item for item in items if not item["done"]]

    if not items:
        print("待办清单还是空的。用 python todo.py add \"标题\" 添加第一条吧。")
        return 0
    if not shown:
        print("没有未完成的待办了（共 %d 条已完成）。用 python todo.py list --all 查看全部。" % len(items))
        return 0

    render_table(shown)
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo.py",
        description="单文件零依赖命令行待办清单",
        epilog="数据文件默认与 todo.py 同目录的 todos.json；可用环境变量 TODO_FILE 覆盖。",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="{add,done,list,rm}")

    p_add = sub.add_parser("add", help="新增待办")
    p_add.add_argument("title", nargs="+", help="待办标题（可用引号包裹，含空格）")
    p_add.set_defaults(func=cmd_add)

    p_done = sub.add_parser("done", help="标记完成")
    p_done.add_argument("id", type=int, help="待办 id")
    p_done.set_defaults(func=cmd_done)

    p_list = sub.add_parser("list", help="列出待办")
    p_list.add_argument("--all", action="store_true", help="包含已完成的待办")
    p_list.set_defaults(func=cmd_list)

    p_rm = sub.add_parser("rm", help="删除待办")
    p_rm.add_argument("id", type=int, help="待办 id")
    p_rm.set_defaults(func=cmd_rm)

    return parser


def main(argv: list | None = None) -> int:
    _force_utf8()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SystemExit:
        raise
    except OSError as exc:
        die("错误：数据文件读写失败（%s）。" % exc, 1)


if __name__ == "__main__":
    sys.exit(main())
