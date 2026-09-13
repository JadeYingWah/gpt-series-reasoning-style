#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""todo.py —— 单文件、零依赖的命令行待办清单。

用法
    python todo.py add "标题"      新增待办（自增 id、默认未完成、记录创建时间）
    python todo.py done <id>       标记为已完成
    python todo.py list [--all]    列出未完成（默认）或全部（--all / -a）
    python todo.py list --full     长标题不截断（默认截断到 60 列 + …）
    python todo.py rm <id>         删除待办
    python todo.py --help          显示帮助

数据
    当前工作目录下的 todos.json，脚本自动创建（任何命令都会确保它存在）。
    结构：{"version": 1, "next_id": 3, "todos": [{"id":1,"title":"...",
          "done":false,"created_at":"2026-09-13T23:59:01"}]}

退出码
    0  成功
    1  操作失败（空标题、id 不存在、文件写入失败等）
    2  用法错误（未知命令/未知参数/缺少参数）

设计取舍（均为显式决定，便于第三方核验）
    * 标题保存前会 strip()：纯空白标题被拒绝，普通标题的首尾空白不入库。
    * list 显示时对标题中的控制字符做转义（\\n、\\t 等），保证表格不被换行
      拆行；磁盘上的 JSON 里保存的是原始标题，不做截断、不丢字符。
    * 列表里标题列默认按显示宽度截断到 60 列并加省略号（否则 500 字标题会把表格
      撑到不可读）；用 `list --full` 可查看未截断的标题。截断只影响显示。
    * 表格按“显示宽度”对齐：中文/全角/emoji 记 2 列宽，组合记号记 0。
    * 数据文件解析失败时不崩溃：打印警告、备份为 todos.json.corrupt、从空库开始。
"""

import json
import os
import shutil
import sys
import tempfile
import unicodedata
from datetime import datetime

STORE = "todos.json"
BACKUP = "todos.json.corrupt"
MAX_TITLE_WIDTH = 60  # 列表里标题列的最大显示宽度（只影响显示，磁盘数据不截断）

USAGE = """todo.py —— 命令行待办清单（数据保存在当前目录的 todos.json）

  python todo.py add "标题"      新增待办（自增 id、默认未完成、记录创建时间）
  python todo.py done <id>       标记为已完成
  python todo.py list [--all]    列出未完成（默认）或全部（-a / --all）
  python todo.py list --full     标题不截断（默认超长标题截断为 60 列 + …）
  python todo.py rm <id>         删除待办
  python todo.py --help          显示本帮助

退出码：0 成功 / 1 操作失败 / 2 用法错误"""

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


# --------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------
def _setup_stdio():
    """Windows 下重定向到管道时默认编码可能不是 UTF-8（如 GBK），
    遇到 emoji 会抛 UnicodeEncodeError。强制 UTF-8 + 替换兜底。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def char_width(ch):
    if unicodedata.category(ch) in ("Mn", "Me", "Cf"):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def display_width(text):
    """字符在等宽终端里占据的列数（中文/全角/emoji 记 2）。"""
    return sum(char_width(ch) for ch in text)


def pad(text, width):
    return text + " " * max(0, width - display_width(text))


def clip_display(text, max_width):
    """按显示宽度截断，末尾加省略号（不改变磁盘数据）。"""
    if display_width(text) <= max_width:
        return text
    out = []
    width = 0
    for ch in text:
        step = char_width(ch)
        if width + step > max_width - 1:
            break
        out.append(ch)
        width += step
    return "".join(out) + "…"


def escape_title(title):
    """把控制字符转成可见转义，避免换行把表格拆成两行。"""
    out = []
    for ch in title:
        if ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif unicodedata.category(ch) == "Cc":
            out.append("\\x%02x" % ord(ch))
        else:
            out.append(ch)
    return "".join(out)


def warn(message):
    sys.stderr.write("警告：%s\n" % message)


def error(message):
    sys.stderr.write("错误：%s\n" % message)


def now_iso():
    return datetime.now().replace(microsecond=0).isoformat()


def format_time(value):
    if not isinstance(value, str) or not value:
        return "-"
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"


# --------------------------------------------------------------------------
# 数据读写（任何情况下都不抛异常到顶层）
# --------------------------------------------------------------------------
def empty_db():
    return {"version": 1, "next_id": 1, "todos": []}


def normalize(data):
    """把任意解析结果整理成合法 db；返回 (db, 错误信息)。"""
    db = empty_db()
    if isinstance(data, dict):
        items = data.get("todos", [])
        raw_next = data.get("next_id")
        if isinstance(raw_next, int) and not isinstance(raw_next, bool) and raw_next >= 1:
            db["next_id"] = raw_next
    elif isinstance(data, list):
        items = data  # 兼容“纯数组”格式的旧文件
    else:
        return db, "顶层结构不是对象或数组，已按空库处理"

    if not isinstance(items, list):
        return db, "todos 字段不是数组，已按空库处理"

    for item in items:
        if not isinstance(item, dict):
            continue
        tid = item.get("id")
        title = item.get("title")
        if isinstance(tid, bool) or not isinstance(tid, int):
            continue
        if not isinstance(title, str):
            continue
        db["todos"].append({
            "id": tid,
            "title": title,
            "done": bool(item.get("done", False)),
            "created_at": item.get("created_at") if isinstance(item.get("created_at"), str) else "",
        })

    max_id = max([t["id"] for t in db["todos"]] + [0])
    if db["next_id"] <= max_id:
        db["next_id"] = max_id + 1
    return db, None


def read_db(path=STORE):
    """返回 (db, 错误信息, 是否损坏)。文件缺失/损坏/不可读都返回空库。"""
    if not os.path.exists(path):
        return empty_db(), None, False
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except OSError as exc:
        return empty_db(), "无法读取数据文件 %s（%s），已按空库处理" % (path, exc), True
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        return empty_db(), "数据文件 %s 内容损坏（%s），已备份为 %s" % (path, exc, BACKUP), True
    db, err = normalize(data)
    if err:
        return db, "数据文件 %s 格式异常：%s" % (path, err), False
    return db, None, False


def write_db(db, path=STORE):
    """原子写入：先写临时文件再 os.replace，避免半截文件。"""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".todo-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(db, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def backup_corrupt(path=STORE):
    """覆盖损坏文件前先留一份副本，避免用户数据被静默丢弃。"""
    try:
        if os.path.isfile(path):
            shutil.copyfile(path, BACKUP)
    except OSError as exc:
        warn("无法备份损坏的数据文件（%s）" % exc)


def ensure_store(path=STORE):
    """文件不存在时自动创建一个空库文件。"""
    if not os.path.exists(path):
        try:
            write_db(empty_db(), path)
        except OSError as exc:
            warn("无法创建数据文件 %s（%s）" % (path, exc))


# --------------------------------------------------------------------------
# 命令实现
# --------------------------------------------------------------------------
def find_item(db, item_id):
    for item in db["todos"]:
        if item["id"] == item_id:
            return item
    return None


def cmd_add(args):
    title = " ".join(args).strip()
    if not title:
        error('标题不能为空。用法：todo.py add "标题"')
        return EXIT_FAIL

    ensure_store()
    db, err, corrupt = read_db()
    if err:
        warn(err)
    if corrupt:
        backup_corrupt()

    item = {"id": db["next_id"], "title": title, "done": False, "created_at": now_iso()}
    db["todos"].append(item)
    db["next_id"] += 1
    try:
        write_db(db)
    except OSError as exc:
        error("写入数据文件失败（%s），本次修改未保存" % exc)
        return EXIT_FAIL

    print("已添加 #%d：%s" % (item["id"], escape_title(title)))
    return EXIT_OK


def parse_id(args, command):
    """返回 (id, 退出码)。出错时 id 为 None。"""
    if len(args) != 1:
        error("`%s` 需要且只需要一个 id 参数。用法：todo.py %s <id>" % (command, command))
        return None, EXIT_USAGE
    try:
        return int(args[0].strip()), EXIT_OK
    except (ValueError, TypeError):
        error("id 必须是整数，收到的是：%r" % (args[0],))
        return None, EXIT_FAIL


def cmd_done(args):
    item_id, code = parse_id(args, "done")
    if item_id is None:
        return code

    ensure_store()
    db, err, corrupt = read_db()
    if err:
        warn(err)
    if corrupt:
        backup_corrupt()

    item = find_item(db, item_id)
    if item is None:
        error("未找到 id 为 %d 的待办。用 `todo.py list --all` 查看现有待办。" % item_id)
        return EXIT_FAIL
    if item["done"]:
        print("#%d 已经是完成状态：%s" % (item_id, escape_title(item["title"])))
        return EXIT_OK

    item["done"] = True
    try:
        write_db(db)
    except OSError as exc:
        error("写入数据文件失败（%s），本次修改未保存" % exc)
        return EXIT_FAIL
    print("已完成 #%d：%s" % (item_id, escape_title(item["title"])))
    return EXIT_OK


def cmd_rm(args):
    item_id, code = parse_id(args, "rm")
    if item_id is None:
        return code

    ensure_store()
    db, err, corrupt = read_db()
    if err:
        warn(err)
    if corrupt:
        backup_corrupt()

    item = find_item(db, item_id)
    if item is None:
        error("未找到 id 为 %d 的待办，未做任何删除。" % item_id)
        return EXIT_FAIL

    db["todos"] = [t for t in db["todos"] if t["id"] != item_id]
    try:
        write_db(db)
    except OSError as exc:
        error("写入数据文件失败（%s），本次修改未保存" % exc)
        return EXIT_FAIL
    print("已删除 #%d：%s" % (item_id, escape_title(item["title"])))
    return EXIT_OK


def render_table(items, full=False):
    headers = ["ID", "状态", "标题", "创建时间"]
    rows = []
    for item in items:
        title = escape_title(item["title"])
        if not full and display_width(title) > MAX_TITLE_WIDTH:
            title = clip_display(title, MAX_TITLE_WIDTH)
        rows.append([
            str(item["id"]),
            "[✓]" if item["done"] else "[ ]",
            title,
            format_time(item.get("created_at")),
        ])

    widths = [display_width(headers[i]) for i in range(len(headers))]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], display_width(cell))

    print("  ".join(pad(headers[i], widths[i]) for i in range(len(headers))).rstrip())
    for row in rows:
        print("  ".join(pad(row[i], widths[i]) for i in range(len(row))).rstrip())


def cmd_list(args):
    show_all = False
    full = False
    for arg in args:
        if arg in ("--all", "-a"):
            show_all = True
        elif arg in ("--full", "-f"):
            full = True
        else:
            error("无法识别的参数：%r。用法：todo.py list [--all] [--full]" % arg)
            return EXIT_USAGE

    ensure_store()
    db, err, corrupt = read_db()
    if err:
        warn(err)

    if not db["todos"]:
        print("列表为空 —— 用 `todo.py add \"标题\"` 添加第一条待办。")
        return EXIT_OK

    items = db["todos"] if show_all else [t for t in db["todos"] if not t["done"]]
    if not items:
        print("全部 %d 条待办都已完成 —— 用 `todo.py list --all` 查看全部。" % len(db["todos"]))
        return EXIT_OK

    render_table(items, full=full)
    done_count = sum(1 for t in items if t["done"])
    if show_all and done_count:
        print("共 %d 条（%d 条已完成）" % (len(items), done_count))
    elif show_all:
        print("共 %d 条" % len(items))
    else:
        print("共 %d 条未完成" % len(items))
    return EXIT_OK


COMMANDS = {"add": cmd_add, "done": cmd_done, "rm": cmd_rm, "list": cmd_list}


def main(argv):
    _setup_stdio()
    if not argv:
        sys.stderr.write(USAGE + "\n")
        return EXIT_USAGE

    command, rest = argv[0], argv[1:]
    if command in ("-h", "--help", "help"):
        print(USAGE)
        return EXIT_OK
    if command not in COMMANDS:
        error("未知命令：%r" % command)
        sys.stderr.write(USAGE + "\n")
        return EXIT_USAGE
    return COMMANDS[command](rest)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:  # 兜底：任何未预期异常都不向用户抛 traceback
        _setup_stdio()
        sys.stderr.write("未预期的错误：%s: %s\n" % (type(exc).__name__, exc))
        sys.exit(EXIT_FAIL)
