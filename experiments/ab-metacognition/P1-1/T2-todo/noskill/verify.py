#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""verify.py —— todo.py 的独立验证脚本（零依赖，可被第三方原样复算）

运行方式（任意工作目录均可）：
    python verify.py            # 或  python3 verify.py

脚本会：
  1. 定位同目录下的 todo.py，通过环境变量 TODO_FILE 把数据文件重定向到临时目录，
     因此不会污染（也不依赖）任何既有数据；
  2. 以子进程方式真实调用 todo.py，逐条断言「功能 + 边界」行为；
  3. 逐条打印 PASS / FAIL，全部通过退出码 0，任一失败退出码 1。

判定所需工具函数在本文件内独立实现（不 import todo.py），避免自证循环。
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
TODO_PY = os.path.join(HERE, "todo.py")

RESULTS = []


# --------------------------------------------------------------------------
# 独立实现的判定工具
# --------------------------------------------------------------------------
def cw(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def dwidth(text: str) -> int:
    return sum(cw(ch) for ch in text)


def run(args, datafile=None, cwd=None, drop_env=False, script=None):
    """调用 todo.py，返回 (退出码, stdout, stderr)。"""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if drop_env:
        env.pop("TODO_FILE", None)
    else:
        env["TODO_FILE"] = datafile
    proc = subprocess.run(
        [sys.executable, script or TODO_PY] + list(args),
        env=env,
        cwd=cwd or HERE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout, proc.stderr


def check(name: str, condition: bool, detail: str = "") -> bool:
    ok = bool(condition)
    RESULTS.append((ok, name, detail))
    print("[%s] %s%s" % ("PASS" if ok else "FAIL", name, ("  —— " + detail) if detail else ""))
    return ok


def read_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_raw(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def new_case_dir(label: str) -> str:
    """每个用例一个干净的临时目录，互不干扰。"""
    d = tempfile.mkdtemp(prefix="todo_case_%s_" % label)
    return d


def db(directory: str) -> str:
    return os.path.join(directory, "todos.json")


# --------------------------------------------------------------------------
# 用例
# --------------------------------------------------------------------------
def case_empty_library():
    d = new_case_dir("empty")
    code, out, err = run(["list"], db(d))
    check("边界-空库 list 友好提示", code == 0 and "空" in out, "code=%d out=%r" % (code, out.strip()))
    check("边界-空库 list 不创建数据文件", not os.path.exists(db(d)), "文件应不存在")
    code, out, _ = run(["list", "--all"], db(d))
    check("边界-空库 list --all 友好提示", code == 0 and "空" in out, "out=%r" % out.strip())


def case_add_basic():
    d = new_case_dir("add")
    code, out, err = run(["add", "买牛奶"], db(d))
    check("功能-add 成功且自动创建数据文件",
          code == 0 and os.path.exists(db(d)) and "#1" in out,
          "code=%d out=%r" % (code, out.strip()))
    items = read_json(db(d))
    check("功能-add 写入字段正确（id/标题/done/创建时间）",
          len(items) == 1 and items[0]["id"] == 1 and items[0]["title"] == "买牛奶"
          and items[0]["done"] is False and bool(items[0].get("created_at")),
          "记录=%r" % (items,))
    code, out, _ = run(["add", "写周报"], db(d))
    items = read_json(db(d))
    check("功能-add 自增 id", code == 0 and [i["id"] for i in items] == [1, 2],
          "ids=%r" % [i["id"] for i in items])
    # 中文未被转义为 \uXXXX
    raw = open(db(d), "r", encoding="utf-8").read()
    check("功能-JSON 以 UTF-8 原样保存中文", "买牛奶" in raw, "含 \\u 转义则为失败")


def case_blank_title():
    d = new_case_dir("blank")
    run(["add", "有效条目"], db(d))
    before = read_json(db(d))
    code, out, err = run(["add", ""], db(d))
    check("边界-空标题被拒绝", code == 2 and len(read_json(db(d))) == len(before),
          "code=%d err=%r" % (code, err.strip()))
    code, out, err = run(["add", "   \t  "], db(d))
    check("边界-纯空白标题被拒绝", code == 2 and len(read_json(db(d))) == len(before),
          "code=%d err=%r" % (code, err.strip()))


def case_duplicate_title():
    d = new_case_dir("dup")
    run(["add", "重复标题"], db(d))
    code, _, _ = run(["add", "重复标题"], db(d))
    items = read_json(db(d))
    check("边界-重复标题允许新增且 id 不同",
          code == 0 and len(items) == 2 and items[0]["title"] == items[1]["title"]
          and items[0]["id"] != items[1]["id"],
          "ids=%r titles=%r" % ([i["id"] for i in items], [i["title"] for i in items]))


def case_special_titles():
    d = new_case_dir("special")
    tricky = '含"双引号"与\'单引号\'与\\反斜杠'
    code, _, _ = run(["add", tricky], db(d))
    items = read_json(db(d))
    check("边界-标题含引号/反斜杠 完整存取", code == 0 and items[0]["title"] == tricky,
          "存储=%r" % items[0]["title"])

    d2 = new_case_dir("newline")
    with_nl = "第一行\n第二行\t带制表符"
    code, _, _ = run(["add", with_nl], db(d2))
    items = read_json(db(d2))
    check("边界-标题含换行/制表符 完整存取",
          code == 0 and items[0]["title"] == with_nl, "存储=%r" % items[0]["title"])
    code, out, _ = run(["list"], db(d2))
    body = [ln for ln in out.splitlines() if ln.strip()]
    check("边界-含换行标题在表格中只占一行",
          code == 0 and len(body) == 3 and "\\n" in out,
          "行数=%d" % len(body))

    d3 = new_case_dir("emoji")
    emoji_title = "买咖啡 ☕ 开会 📅 上线 🚀"
    code, _, _ = run(["add", emoji_title], db(d3))
    items = read_json(db(d3))
    check("边界-emoji 标题完整存取且不崩溃",
          code == 0 and items[0]["title"] == emoji_title, "存储=%r" % items[0]["title"])

    d4 = new_case_dir("long")
    long_title = "测" * 250 + "a" * 250  # 500 字符（250 中文 + 250 英文）
    code, _, _ = run(["add", long_title], db(d4))
    items = read_json(db(d4))
    check("边界-500 字符超长标题完整存储（不截断数据）",
          code == 0 and items[0]["title"] == long_title and len(long_title) == 500,
          "存储长度=%d" % len(items[0]["title"]))
    code, out, _ = run(["list"], db(d4))
    tail = out.splitlines()[-1] if out.strip() else ""
    check("边界-超长标题在表格中被显示截断（含 …）",
          code == 0 and "…" in out and dwidth(tail) <= 200,
          "末行显示宽度=%d" % dwidth(tail))


def case_alignment():
    d = new_case_dir("align")
    for t in ["买牛奶", "写季度总结报告并发送给全组", "开会 📅 讨论 🚀 路线图", "a"]:
        run(["add", t], db(d))
    code, out, _ = run(["list", "--all"], db(d))
    lines = [ln for ln in out.splitlines() if ln.strip()]
    # 对齐判定：每行各列分隔符 "|" 必须落在相同的显示列位置（CJK/emoji 记 2 列宽）。
    # 不用「整行等宽」判定，因为末列尾随空格会被 rstrip 掉。
    def bar_positions(line):
        pos, acc = [], 0
        for ch in line:
            if ch == "|":
                pos.append(acc)
            acc += cw(ch)
        return tuple(pos)


    separators = [ln for ln in lines if set(ln) <= set("-| ")]
    check("功能-表格含分隔行", len(separators) == 1, "分隔行数=%d" % len(separators))

    positions = {bar_positions(ln) for ln in lines}
    check("功能-表格列对齐（CJK/emoji 按 2 列宽计算，各行列位置一致）",
          code == 0 and len(lines) == 6 and len(positions) == 1 and len(next(iter(positions))) == 3,
          "行数=%d 各行列分隔位置集合=%r" % (len(lines), sorted(positions)))


def case_done_rm():
    d = new_case_dir("donerm")
    run(["add", "任务A"], db(d))
    run(["add", "任务B"], db(d))
    code, out, _ = run(["done", "1"], db(d))
    items = read_json(db(d))
    check("功能-done 标记完成", code == 0 and items[0]["done"] is True and items[1]["done"] is False,
          "done 状态=%r" % [i["done"] for i in items])
    code, out, _ = run(["done", "1"], db(d))
    check("边界-重复 done 同一 id 幂等不报错", code == 0, "code=%d" % code)

    code, out, err = run(["done", "999"], db(d))
    check("边界-done 不存在的 id 报错退出码 1",
          code == 1 and "999" in err, "code=%d err=%r" % (code, err.strip()))
    code, out, err = run(["done", "abc"], db(d))
    check("边界-done 非整数 id 退出码 2", code == 2, "code=%d" % code)

    code, out, _ = run(["list"], db(d))
    check("功能-list 默认只列未完成", code == 0 and "任务A" not in out and "任务B" in out,
          "out=%r" % out.strip().replace("\n", " | "))
    code, out, _ = run(["list", "--all"], db(d))
    check("功能-list --all 列出全部", code == 0 and "任务A" in out and "任务B" in out,
          "out=%r" % out.strip().replace("\n", " | "))

    code, out, err = run(["rm", "999"], db(d))
    check("边界-rm 不存在的 id 报错退出码 1", code == 1 and "999" in err, "code=%d" % code)
    code, out, _ = run(["rm", "2"], db(d))
    items = read_json(db(d))
    check("功能-rm 删除指定 id", code == 0 and [i["id"] for i in items] == [1],
          "剩余 ids=%r" % [i["id"] for i in items])
    code, out, _ = run(["add", "任务C"], db(d))
    items = read_json(db(d))
    check("边界-删除后新增不复用旧 id", [i["id"] for i in items] == [1, 2] and items[1]["title"] == "任务C",
          "ids=%r" % [i["id"] for i in items])


def case_all_done_message():
    d = new_case_dir("alldone")
    run(["add", "唯一任务"], db(d))
    run(["done", "1"], db(d))
    code, out, _ = run(["list"], db(d))
    check("边界-全部完成时 list 给出已完成数量提示",
          code == 0 and "已完成" in out and "1" in out and "唯一任务" not in out,
          "out=%r" % out.strip())


def case_corrupt_and_missing():
    # 1) 文件缺失
    d = new_case_dir("missing")
    code, out, _ = run(["list"], db(d))
    check("边界-数据文件缺失不崩溃", code == 0, "code=%d" % code)

    # 2) 截断的 JSON
    d = new_case_dir("truncated")
    write_raw(db(d), '{"broken":')
    code, out, err = run(["list"], db(d))
    check("边界-损坏 JSON（截断）list 不崩溃",
          code == 0 and "空" in out, "code=%d out=%r" % (code, out.strip()))
    check("边界-损坏 JSON 已备份为 .bak",
          os.path.exists(db(d) + ".bak")
          and open(db(d) + ".bak", "r", encoding="utf-8").read() == '{"broken":',
          "备份存在=%s" % os.path.exists(db(d) + ".bak"))
    code, out, _ = run(["add", "重建"], db(d))
    items = read_json(db(d))
    check("边界-损坏后 add 可重建数据文件",
          code == 0 and len(items) == 1 and items[0]["title"] == "重建", "记录=%r" % items)

    # 3) 空文件
    d = new_case_dir("zerobyte")
    write_raw(db(d), "")
    code, out, _ = run(["list"], db(d))
    check("边界-0 字节数据文件不崩溃", code == 0, "code=%d" % code)

    # 4) JSON 顶层不是数组
    d = new_case_dir("noarray")
    write_raw(db(d), '{"todos": []}')
    code, out, _ = run(["list", "--all"], db(d))
    check("边界-JSON 顶层非数组不崩溃", code == 0 and "空" in out, "code=%d" % code)

    # 5) 数组内混入非法条目
    d = new_case_dir("badentry")
    write_raw(db(d), json.dumps(
        [{"id": 1, "title": "合法条目", "done": False, "created_at": "2026-01-01T00:00:00"},
         "不是对象", {"id": "x", "title": "id 非法"}, {"title": "缺 id"}],
        ensure_ascii=False))
    code, out, err = run(["list", "--all"], db(d))
    check("边界-非法条目被忽略且合法条目保留",
          code == 0 and "合法条目" in out and out.count("\n") >= 2 and "警告" in err,
          "code=%d err=%r" % (code, err.strip()))

    # 6) 无任何参数 / 未知命令
    d = new_case_dir("usagerr")
    code, out, err = run([], db(d))
    check("边界-无参数退出码 2", code == 2, "code=%d" % code)
    code, out, err = run(["nosuchcmd"], db(d))
    check("边界-未知命令退出码 2", code == 2, "code=%d" % code)


def case_default_datafile_path():
    """不带 TODO_FILE 时，todos.json 应创建在 todo.py 同目录。"""
    d = new_case_dir("defaultpath")
    copied = os.path.join(d, "todo.py")
    shutil.copy2(TODO_PY, copied)
    code, out, err = run(["add", "默认路径条目"], cwd=d, drop_env=True, script=copied)
    created = os.path.join(d, "todos.json")
    check("功能-默认在脚本同目录自动创建 todos.json",
          code == 0 and os.path.exists(created)
          and read_json(created)[0]["title"] == "默认路径条目",
          "code=%d 文件存在=%s" % (code, os.path.exists(created)))


def case_idempotent_roundtrip():
    """同一批操作重放两次（除自增 id 外）结果稳定。"""
    def build(d):
        run(["add", "A"], db(d))
        run(["add", "B"], db(d))
        run(["done", "1"], db(d))
        return [(i["title"], i["done"]) for i in read_json(db(d))]

    d1, d2 = new_case_dir("rt1"), new_case_dir("rt2")
    check("功能-操作序列可重复复算（状态一致）", build(d1) == build(d2),
          "结果=%r" % (build(d1),))


# --------------------------------------------------------------------------
def main() -> int:
    if not os.path.exists(TODO_PY):
        print("找不到 todo.py：%s" % TODO_PY)
        return 1
    digest = hashlib.sha256(open(TODO_PY, "rb").read()).hexdigest()

    print("=" * 72)
    print("todo.py 独立验证")
    print("=" * 72)
    print("时间(本地) : %s" % __import__("datetime").datetime.now().isoformat(timespec="seconds"))
    print("Python     : %s (%s)" % (sys.version.split()[0], sys.executable))
    print("平台       : %s %s" % (platform.platform(), platform.machine()))
    print("todo.py    : %s" % TODO_PY)
    print("sha256     : %s" % digest)
    print("-" * 72)

    case_empty_library()
    case_add_basic()
    case_blank_title()
    case_duplicate_title()
    case_special_titles()
    case_alignment()
    case_done_rm()
    case_all_done_message()
    case_corrupt_and_missing()
    case_default_datafile_path()
    case_idempotent_roundtrip()

    total = len(RESULTS)
    passed = sum(1 for ok, _, _ in RESULTS if ok)
    failed = [n for ok, n, _ in RESULTS if not ok]
    print("-" * 72)
    print("合计 %d 项：通过 %d，失败 %d" % (total, passed, total - passed))
    if failed:
        for name in failed:
            print("  FAILED: %s" % name)
    print("=" * 72)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
