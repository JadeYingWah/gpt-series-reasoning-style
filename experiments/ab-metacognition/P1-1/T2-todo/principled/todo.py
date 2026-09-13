#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""todo.py —— 单文件、零依赖的命令行待办清单工具。

用法:
    python todo.py add "标题"      新增待办（自增 id / 默认未完成 / 记录创建时间）
    python todo.py done <id>       标记为完成
    python todo.py list [--all]    列出未完成（默认）或全部（--all），表格对齐输出
    python todo.py rm <id>         删除待办

数据:
    当前工作目录下的 todos.json，首次写入时自动创建；写入采用「临时文件 + 原子替换」。

退出码:
    0 成功 / 1 运行时错误（空标题、id 不存在）/ 2 命令行用法错误（argparse）

设计取舍与验证证据见同目录 EVIDENCE.md 与 evidence/。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path

DATA_FILE_NAME = "todos.json"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DONE_LABEL = "已完成"
UNDONE_LABEL = "未完成"
STATUS_WIDTH = 6          # 三个汉字的显示宽度
CREATED_WIDTH = 19        # "2026-09-13 23:57:12"
MIN_TITLE_WIDTH = 8
ELLIPSIS = "…"
# 除 \t \n \r 之外的 C0 控制字符与 DEL：会破坏表格/终端，统一剔除
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

EXIT_OK = 0
EXIT_ERROR = 1


# --------------------------------------------------------------------------- 编码


def force_utf8() -> None:
    """Windows 控制台默认代码页（GBK）无法编码 emoji/部分符号，直接 print 会抛
    UnicodeEncodeError 崩溃。这里在写任何输出之前把标准流统一切成 UTF-8。"""
    if os.name == "nt" and sys.stdout.isatty():
        try:  # 让控制台本身按 UTF-8 渲染，否则 UTF-8 字节会被 GBK 解释成乱码
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# ------------------------------------------------------------------- 显示宽度工具


def char_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def display_width(text: str) -> int:
    """按「终端显示列数」计算宽度：CJK/全角/emoji 记 2 列，组合记号记 0 列。
    表格对齐必须用它而不是 len()，否则含中文/emoji 的行会错位。"""
    return sum(char_width(ch) for ch in text)


def pad(text: str, width: int, align: str = "left") -> str:
    filling = " " * max(0, width - display_width(text))
    return text + filling if align == "left" else filling + text


def truncate(text: str, max_width: int) -> str:
    if display_width(text) <= max_width:
        return text
    kept: list[str] = []
    used = 0
    budget = max(1, max_width - display_width(ELLIPSIS))
    for ch in text:
        cost = char_width(ch)
        if used + cost > budget:
            break
        kept.append(ch)
        used += cost
    return "".join(kept) + ELLIPSIS


# ----------------------------------------------------------------------- 标题清洗


def sanitize_title(raw: str) -> str:
    """去掉会破坏表格的控制字符（换行/制表符折算成空格），并去掉首尾空白。
    只做「必要清洗」，不改动引号、emoji 等其它字符。"""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\n", " ").replace("\t", " ")
    text = CONTROL_CHARS_RE.sub("", text)
    return text.strip()


# ------------------------------------------------------------------------- 存储层


class Store:
    def __init__(self, todos: list[dict], next_id: int, warning: str | None = None) -> None:
        self.todos = todos
        self.next_id = next_id
        self.warning = warning


def load_store(path: Path) -> Store:
    """读取存储。文件缺失 / 非 UTF-8 / JSON 损坏 / 结构异常，一律降级为空库并给出
    警告文案，绝不把异常抛到调用方（任务书要求：不崩溃）。"""
    if not path.exists():
        return Store([], 1, None)
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Store([], 1, f"数据文件 {path.name} 不是合法的 UTF-8 文本，本次按空库处理。")
    except OSError as exc:
        return Store([], 1, f"无法读取数据文件 {path.name}（{exc.strerror}），本次按空库处理。")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return Store([], 1, f"数据文件 {path.name} 已损坏（JSON 解析失败），本次按空库处理；执行写操作后会重建。")

    raw_items = data.get("todos") if isinstance(data, dict) else data
    if not isinstance(raw_items, list):
        return Store([], 1, f"数据文件 {path.name} 结构不正确（todos 不是列表），本次按空库处理。")

    todos: list[dict] = []
    skipped = 0
    for item in raw_items:
        if (
            isinstance(item, dict)
            and isinstance(item.get("id"), int)
            and isinstance(item.get("title"), str)
        ):
            todos.append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "done": bool(item.get("done", False)),
                    "created_at": item.get("created_at") or "",
                }
            )
        else:
            skipped += 1

    warning = None
    if skipped:
        warning = f"数据文件中有 {skipped} 条记录格式不正确，已忽略。"
    if isinstance(data, dict) and not isinstance(data.get("next_id"), int):
        warning = (warning or "") + f"数据文件缺少合法的 next_id，已按现有记录重新推算。"

    highest = max((t["id"] for t in todos), default=0)
    stored_next = data.get("next_id") if isinstance(data, dict) else None
    next_id = max(highest + 1, 1)
    if isinstance(stored_next, int) and stored_next > next_id:
        next_id = stored_next
    return Store(todos, next_id, warning or None)


def save_store(path: Path, todos: list[dict], next_id: int) -> None:
    payload = {"next_id": next_id, "todos": sorted(todos, key=lambda t: t["id"])}
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=".todos-", suffix=".tmp", delete=False
    )
    try:
        with handle as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
        os.replace(handle.name, path)  # 原子替换：写一半断电也不会留下半截 JSON
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise


def data_file() -> Path:
    return Path.cwd() / DATA_FILE_NAME


def find_todo(todos: list[dict], todo_id: int) -> dict | None:
    for todo in todos:
        if todo["id"] == todo_id:
            return todo
    return None


# ------------------------------------------------------------------------- 输出层


def build_table(rows: list[tuple[int, str, str, str]], term_width: int) -> list[str]:
    id_width = max(2, max((len(str(r[0])) for r in rows), default=2))
    prefix = id_width + 3 + STATUS_WIDTH + 3 + CREATED_WIDTH + 3
    available = max(MIN_TITLE_WIDTH, term_width - prefix)
    widest_title = max([display_width("标题")] + [display_width(r[3]) for r in rows])
    title_width = max(4, min(available, widest_title))

    header = " | ".join(
        [
            pad("ID", id_width, "right"),
            pad("状态", STATUS_WIDTH),
            pad("创建时间", CREATED_WIDTH),
            pad("标题", title_width),
        ]
    )
    separator = "-+-".join(
        ["-" * id_width, "-" * STATUS_WIDTH, "-" * CREATED_WIDTH, "-" * title_width]
    )
    lines = [header, separator]
    for todo_id, status, created, title in rows:
        lines.append(
            " | ".join(
                [
                    pad(str(todo_id), id_width, "right"),
                    pad(status, STATUS_WIDTH),
                    pad(created, CREATED_WIDTH),
                    pad(truncate(title, title_width), title_width),
                ]
            )
        )
    return lines


def emit_store_warning(store: Store) -> None:
    if store.warning:
        print("警告：" + store.warning, file=sys.stderr)


# ------------------------------------------------------------------------- 命令层


def cmd_add(args: argparse.Namespace) -> int:
    title = sanitize_title(" ".join(args.title))
    if not title:
        print("错误：标题不能为空，也不能只有空白字符。", file=sys.stderr)
        return EXIT_ERROR

    path = data_file()
    store = load_store(path)
    emit_store_warning(store)
    todo = {
        "id": store.next_id,
        "title": title,
        "done": False,
        "created_at": datetime.now().strftime(TIME_FORMAT),
    }
    store.todos.append(todo)
    save_store(path, store.todos, store.next_id + 1)
    print(f"已添加 #{todo['id']}：{title}")
    return EXIT_OK


def cmd_done(args: argparse.Namespace) -> int:
    path = data_file()
    store = load_store(path)
    emit_store_warning(store)
    target = find_todo(store.todos, args.id)
    if target is None:
        print(f"错误：未找到 id={args.id} 的待办。", file=sys.stderr)
        return EXIT_ERROR
    if target["done"]:
        print(f"#{args.id} 已经是完成状态：{target['title']}")
        return EXIT_OK
    target["done"] = True
    save_store(path, store.todos, store.next_id)
    print(f"已完成 #{args.id}：{target['title']}")
    return EXIT_OK


def cmd_rm(args: argparse.Namespace) -> int:
    path = data_file()
    store = load_store(path)
    emit_store_warning(store)
    target = find_todo(store.todos, args.id)
    if target is None:
        print(f"错误：未找到 id={args.id} 的待办。", file=sys.stderr)
        return EXIT_ERROR
    store.todos.remove(target)
    save_store(path, store.todos, store.next_id)
    print(f"已删除 #{args.id}：{target['title']}")
    return EXIT_OK


def cmd_list(args: argparse.Namespace) -> int:
    path = data_file()
    store = load_store(path)
    emit_store_warning(store)
    todos = sorted(store.todos, key=lambda t: t["id"])

    if not todos:
        print('还没有任何待办。用 python todo.py add "标题" 添加第一条吧。')
        return EXIT_OK

    visible = todos if args.all else [t for t in todos if not t["done"]]
    if not visible:
        print(f"没有未完成的待办了（共 {len(todos)} 条已完成，用 --all 查看全部）。")
        return EXIT_OK

    width = shutil.get_terminal_size((80, 24)).columns
    rows = [
        (
            t["id"],
            DONE_LABEL if t["done"] else UNDONE_LABEL,
            t["created_at"] or "-",
            t["title"],
        )
        for t in visible
    ]
    for line in build_table(rows, width):
        print(line)

    undone = sum(1 for t in todos if not t["done"])
    if args.all:
        print(f"共 {len(todos)} 条，其中未完成 {undone} 条。")
    else:
        print(f"共 {undone} 条未完成（总计 {len(todos)} 条）。")
    return EXIT_OK


# --------------------------------------------------------------------------- CLI


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"id 必须是正整数，收到 {value!r}")
    if number <= 0:
        raise argparse.ArgumentTypeError(f"id 必须是正整数，收到 {value!r}")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo.py",
        description="命令行待办清单（单文件 / 零依赖，数据存于当前目录的 todos.json）",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="{add,done,list,rm}")

    add = subparsers.add_parser("add", help="新增一条待办")
    add.add_argument(
        "title",
        nargs="+",
        help="待办标题；含空格请加引号。换行/制表符会折算为空格，超长标题在列表中按终端宽度截断（原文完整保存）",
    )
    add.set_defaults(handler=cmd_add)

    done = subparsers.add_parser("done", help="把指定 id 标记为完成")
    done.add_argument("id", type=positive_int, help="待办 id（正整数）")
    done.set_defaults(handler=cmd_done)

    listing = subparsers.add_parser("list", help="列出待办（默认只列未完成）")
    listing.add_argument("-a", "--all", action="store_true", help="列出全部（含已完成）")
    listing.set_defaults(handler=cmd_list)

    remove = subparsers.add_parser("rm", help="删除指定 id 的待办")
    remove.add_argument("id", type=positive_int, help="待办 id（正整数）")
    remove.set_defaults(handler=cmd_rm)

    return parser


def main(argv: list[str] | None = None) -> int:
    force_utf8()
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except OSError as exc:
        # 读取失败已在 load_store 内降级；这里兜底写入失败（文件被占用 / 只读 等）
        print(f"错误：读写数据文件 {DATA_FILE_NAME} 失败（{exc.strerror}）。", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("已取消。", file=sys.stderr)
        sys.exit(130)
