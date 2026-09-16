#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""todo.py 的验证电池（第三方可独立复算）。

用法:
    python verify.py [todo.py 的路径]        默认取上级目录的 todo.py
    python verify.py --no-mutation           只跑功能/边界电池，不做变异杀伤率测试

退出码:
    0 = 电池全绿 且 变异杀伤率达标；1 = 有失败项。

设计要点:
    1. 每个用例都在独立的临时目录里以子进程方式调用 todo.py（cwd = 临时目录，
       因此数据文件天然隔离，不会污染交付目录）。
    2. 结论用多条**独立路径**交叉验证：
       路径A 黑盒 CLI（退出码 + stdout/stderr 文本）
       路径B 直接读取 todos.json 断言内部状态（不依赖 CLI 文本）
       路径C 表格几何校验：按「显示宽度」重算列位置，检查列对齐与行宽
       路径D 变异测试：把 todo.py 人为改坏 N 处，检查电池是否会变红（鉴别力证明）
    3. 子进程环境固定 COLUMNS=80、PYTHONUTF8=0，保证结果可复现，并且**不靠**
       UTF-8 模式掩盖 emoji 编码问题（否则「不做 UTF-8 化」的变异体杀不掉）。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

DEFAULT_TODO = Path(__file__).resolve().parent.parent / "todo.py"
COLUMNS = 80
TIMEOUT = 60
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


# --------------------------------------------------------------------- 基础工具


def display_width(text: str) -> int:
    """按终端显示列数计宽（CJK/全角/emoji = 2，组合记号 = 0）。
    这里**独立重算**，不 import todo.py，避免「用被测代码验证被测代码」。"""
    total = 0
    for ch in text:
        if unicodedata.combining(ch):
            continue
        total += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return total


def decode(raw: bytes) -> str:
    return raw.decode("utf-8", "replace")


class Result:
    def __init__(self, code: int, out: bytes, err: bytes) -> None:
        self.code = code
        self.out = decode(out)
        self.err = decode(err)
        self.out_raw = out
        self.err_raw = err

    def ok(self, what: str = "") -> "Result":
        assert self.code == 0, f"{what} 期望退出码 0，实际 {self.code}；stderr={self.err!r}"
        assert "Traceback" not in self.err, f"{what} 抛出了异常栈：{self.err!r}"
        return self

    def fail(self, code: int = 1, what: str = "") -> "Result":
        assert self.code == code, f"{what} 期望退出码 {code}，实际 {self.code}；out={self.out!r} err={self.err!r}"
        assert "Traceback" not in self.err, f"{what} 抛出了异常栈：{self.err!r}"
        return self

    def out_has(self, needle: str) -> "Result":
        assert needle in self.out, f"stdout 缺少 {needle!r}，实际：{self.out!r}"
        return self

    def err_has(self, needle: str) -> "Result":
        assert needle in self.err, f"stderr 缺少 {needle!r}，实际：{self.err!r}"
        return self

    def out_lacks(self, needle: str) -> "Result":
        assert needle not in self.out, f"stdout 不应包含 {needle!r}，实际：{self.out!r}"
        return self


class Runner:
    def __init__(self, todo: Path) -> None:
        self.todo = todo

    def run(self, *args: str, cwd: Path) -> Result:
        env = os.environ.copy()
        env["COLUMNS"] = str(COLUMNS)
        env["LINES"] = "24"
        env["PYTHONUTF8"] = "0"          # 不借助 UTF-8 模式，逼出编码处理是否到位
        env.pop("PYTHONIOENCODING", None)
        proc = subprocess.run(
            [sys.executable, str(self.todo), *args],
            cwd=str(cwd),
            capture_output=True,
            env=env,
            timeout=TIMEOUT,
        )
        return Result(proc.returncode, proc.stdout, proc.stderr)


def read_store(directory: Path) -> dict:
    return json.loads((directory / "todos.json").read_text(encoding="utf-8"))


def table_lines(out: str) -> list[str]:
    return [ln for ln in out.splitlines() if ln.strip() and not ln.startswith("共 ")]


def column_positions(line: str) -> list[int]:
    """表头/数据行的列分隔是 '|'，分隔线行是 '+'，两者都算列位置。"""
    pos: list[int] = []
    col = 0
    for ch in line:
        if ch in "|+":
            pos.append(col)
        col += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return pos[:3]  # 只取三根列分隔（标题里可能还有别的竖线/加号）


def assert_aligned(lines: list[str], what: str = "") -> None:
    """路径C：按显示宽度重算列分隔位置，验证表格真的对齐。"""
    assert len(lines) >= 3, f"{what} 表格行数不足（{len(lines)} 行）：{lines!r}"
    base = column_positions(lines[1])  # 以分隔线为基准
    assert len(base) == 3, f"{what} 分隔线列数异常：{lines[1]!r}"
    widths = []
    for line in lines:
        widths.append(display_width(line))
        assert column_positions(line) == base, (
            f"{what} 列位置错位：基准 {base} vs 实际 {column_positions(line)}；行={line!r}"
        )
    assert len(set(widths)) == 1, f"{what} 各行显示宽度不一致：{widths}"


# ----------------------------------------------------------------------- 用例集

CASES: list[tuple[str, object]] = []


def case(name: str):
    def deco(fn):
        CASES.append((name, fn))
        return fn

    return deco


# --- 段位1：正常值 ------------------------------------------------------------


@case("A1-add-基本新增与落盘")
def _(r: Runner, d: Path):
    r.run("add", "买牛奶", cwd=d).ok("add").out_has("已添加 #1")
    store = read_store(d)
    item = store["todos"][0]
    assert item["id"] == 1, item
    assert item["title"] == "买牛奶", item
    assert item["done"] is False, item
    assert TIMESTAMP_RE.match(item["created_at"]), item
    assert store["next_id"] == 2, store


@case("A2-list-默认列出未完成且表格对齐")
def _(r: Runner, d: Path):
    for title in ("买牛奶", "写周报", "预约体检"):
        r.run("add", title, cwd=d).ok("add")
    out = r.run("list", cwd=d).ok("list").out
    lines = table_lines(out)
    assert len(lines) == 5, f"期望表头+分隔线+3 行，实际 {len(lines)}：{out!r}"
    assert_aligned(lines, "中文表格")
    body = "\n".join(lines)  # 排除末尾汇总行，避免汇总文字里的「未完成」被计入
    assert body.count("未完成") == 3, body


@case("A3-done-标记完成与 list 过滤")
def _(r: Runner, d: Path):
    r.run("add", "aaa", cwd=d).ok()
    r.run("add", "bbb", cwd=d).ok()
    r.run("done", "1", cwd=d).ok("done").out_has("已完成 #1")
    store = read_store(d)
    assert store["todos"][0]["done"] is True, store
    assert store["todos"][1]["done"] is False, store
    pending = r.run("list", cwd=d).ok("list").out
    body = "\n".join(table_lines(pending)[2:])
    assert "aaa" not in body and "bbb" in body, pending
    everything = r.run("list", "--all", cwd=d).ok("list --all").out
    assert_aligned(table_lines(everything), "--all 表格")
    assert everything.count("已完成") >= 1, everything
    assert everything.count("未完成") >= 1, everything


@case("A4-rm-精确删除与重复删除报错")
def _(r: Runner, d: Path):
    r.run("add", "aaa", cwd=d).ok()
    r.run("add", "bbb", cwd=d).ok()
    r.run("rm", "1", cwd=d).ok("rm").out_has("已删除 #1")
    assert [t["id"] for t in read_store(d)["todos"]] == [2]
    r.run("rm", "1", cwd=d).fail(1, "删除不存在 id").err_has("未找到 id=1")
    assert [t["id"] for t in read_store(d)["todos"]] == [2]


@case("A5-id-删除后不回退复用")
def _(r: Runner, d: Path):
    r.run("add", "aaa", cwd=d).ok()
    r.run("rm", "1", cwd=d).ok()
    r.run("add", "bbb", cwd=d).ok().out_has("已添加 #2")
    store = read_store(d)
    assert [t["id"] for t in store["todos"]] == [2], store
    assert store["next_id"] == 3, store


@case("A6-done-重复标记幂等")
def _(r: Runner, d: Path):
    r.run("add", "aaa", cwd=d).ok()
    r.run("done", "1", cwd=d).ok()
    r.run("done", "1", cwd=d).ok("重复 done").out_has("已经是完成状态")
    assert len(read_store(d)["todos"]) == 1


@case("A8-rm-删除非首条且保留其余")
def _(r: Runner, d: Path):
    for title in ("aaa", "bbb", "ccc"):
        r.run("add", title, cwd=d).ok()
    r.run("rm", "2", cwd=d).ok("rm 中间项").out_has("已删除 #2：bbb")
    assert [t["id"] for t in read_store(d)["todos"]] == [1, 3]
    out = r.run("list", cwd=d).ok().out
    body = "\n".join(table_lines(out)[2:])
    assert "aaa" in body and "ccc" in body and "bbb" not in body, out


@case("A9-list-乱序数据按 id 升序输出")
def _(r: Runner, d: Path):
    (d / "todos.json").write_text(
        json.dumps(
            {
                "next_id": 4,
                "todos": [
                    {"id": 3, "title": "third", "done": False, "created_at": "2026-01-03 00:00:00"},
                    {"id": 1, "title": "first", "done": False, "created_at": "2026-01-01 00:00:00"},
                    {"id": 2, "title": "second", "done": False, "created_at": "2026-01-02 00:00:00"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    body = "\n".join(table_lines(r.run("list", cwd=d).ok().out)[2:])
    order = [body.find(name) for name in ("first", "second", "third")]
    assert all(i >= 0 for i in order), body
    assert order == sorted(order), f"输出顺序不是按 id 升序：{body!r}"


@case("A7-多次调用结果稳定")
def _(r: Runner, d: Path):
    for title in ("aaa", "bbb", "ccc"):
        r.run("add", title, cwd=d).ok()
    r.run("done", "2", cwd=d).ok()
    first = r.run("list", "--all", cwd=d).ok().out
    second = r.run("list", "--all", cwd=d).ok().out
    assert first == second, "同样命令两次调用输出应一致"


# --- 段位2：边界值（任务书点名）----------------------------------------------


@case("B1-add-空标题被拒绝")
def _(r: Runner, d: Path):
    r.run("add", "", cwd=d).fail(1, "空标题").err_has("标题不能为空")
    assert not (d / "todos.json").exists(), "空标题不应创建数据文件"


@case("B2-add-纯空白标题被拒绝")
def _(r: Runner, d: Path):
    r.run("add", "   \t  ", cwd=d).fail(1, "空白标题").err_has("标题不能为空")
    assert not (d / "todos.json").exists(), "空白标题不应创建数据文件"


@case("B3-done/rm-不存在的 id")
def _(r: Runner, d: Path):
    r.run("add", "aaa", cwd=d).ok()
    r.run("done", "999", cwd=d).fail(1, "done 999").err_has("未找到 id=999")
    r.run("rm", "999", cwd=d).fail(1, "rm 999").err_has("未找到 id=999")
    assert len(read_store(d)["todos"]) == 1


@case("B4-add-重复标题允许且 id 不同")
def _(r: Runner, d: Path):
    r.run("add", "买牛奶", cwd=d).ok().out_has("已添加 #1")
    r.run("add", "买牛奶", cwd=d).ok().out_has("已添加 #2")
    store = read_store(d)
    assert [t["id"] for t in store["todos"]] == [1, 2], store
    assert [t["title"] for t in store["todos"]] == ["买牛奶", "买牛奶"], store


@case("B5-add-含引号与反斜杠的标题原样保存")
def _(r: Runner, d: Path):
    title = 'He said "hi" \'ok\' \\ end %s {}'
    r.run("add", title, cwd=d).ok("引号标题")
    assert read_store(d)["todos"][0]["title"] == title
    out = r.run("list", cwd=d).ok().out
    assert_aligned(table_lines(out), "引号标题表格")
    assert "hi" in out


@case("B6-add-含换行的标题被折算为空格")
def _(r: Runner, d: Path):
    r.run("add", "line1\nline2", cwd=d).ok("换行标题")
    stored = read_store(d)["todos"][0]["title"]
    assert "\n" not in stored and "\r" not in stored, f"标题不应残留换行：{stored!r}"
    assert stored == "line1 line2", stored
    out = r.run("list", cwd=d).ok().out
    lines = table_lines(out)
    assert len(lines) == 3, f"换行不应把表格拆成多行：{out!r}"


@case("B7-add-emoji 标题不崩溃且对齐")
def _(r: Runner, d: Path):
    title = "买牛奶 🎉 done ✅"
    r.run("add", title, cwd=d).ok("emoji 标题")
    assert read_store(d)["todos"][0]["title"] == title
    out = r.run("list", cwd=d).ok("list emoji").out
    assert "🎉" in out, f"emoji 未正确输出（可能发生了编码崩溃或替换）：{out!r}"
    assert_aligned(table_lines(out), "emoji 表格")


@case("B8-add-500 字符超长标题")
def _(r: Runner, d: Path):
    title = "A" * 300 + "你好" * 100          # 500 个字符 / 700 个显示列
    r.run("add", title, cwd=d).ok("超长标题")
    assert len(read_store(d)["todos"][0]["title"]) == 500, "原文长度应完整保存为 500"
    out = r.run("list", cwd=d).ok("list 超长").out
    lines = table_lines(out)
    assert_aligned(lines, "超长标题表格")
    for line in lines:
        assert display_width(line) <= COLUMNS, f"行宽 {display_width(line)} 超过终端宽度 {COLUMNS}：{line!r}"
    assert "…" in out, "超长标题应截断显示"


@case("B9-list-空库友好提示")
def _(r: Runner, d: Path):
    r.run("list", cwd=d).ok("空库 list").out_has("还没有任何待办")
    r.run("list", "--all", cwd=d).ok("空库 list --all").out_has("还没有任何待办")


@case("B10-list-全部完成时的提示")
def _(r: Runner, d: Path):
    r.run("add", "aaa", cwd=d).ok()
    r.run("done", "1", cwd=d).ok()
    r.run("list", cwd=d).ok("全部完成").out_has("没有未完成的待办了")
    everything = r.run("list", "--all", cwd=d).ok().out
    assert "aaa" in everything, everything


# --- 段位3：异常值 / 数据文件损坏 --------------------------------------------


@case("C1-数据文件缺失时自动创建")
def _(r: Runner, d: Path):
    assert not (d / "todos.json").exists()
    r.run("list", cwd=d).ok("缺失文件 list").out_has("还没有任何待办")
    r.run("add", "aaa", cwd=d).ok("缺失文件 add")
    assert (d / "todos.json").exists(), "首次 add 应自动创建 todos.json"
    assert read_store(d)["todos"][0]["id"] == 1


@case("C2-JSON 损坏时不崩溃并可重建")
def _(r: Runner, d: Path):
    (d / "todos.json").write_text("{not json at all", encoding="utf-8")
    res = r.run("list", cwd=d).ok("损坏文件 list")
    res.err_has("损坏")
    r.run("done", "1", cwd=d).fail(1, "损坏文件 done").err_has("未找到 id=1")
    r.run("rm", "1", cwd=d).fail(1, "损坏文件 rm").err_has("未找到 id=1")
    r.run("add", "rebuild", cwd=d).ok("损坏文件 add")
    store = read_store(d)
    assert [t["title"] for t in store["todos"]] == ["rebuild"], store


@case("C3-非 UTF-8 内容不崩溃")
def _(r: Runner, d: Path):
    (d / "todos.json").write_bytes(b"\xff\xfe\x00\x01\x02broken")
    r.run("list", cwd=d).ok("非 UTF-8 list").err_has("UTF-8")
    r.run("add", "aaa", cwd=d).ok("非 UTF-8 add")
    assert read_store(d)["todos"][0]["title"] == "aaa"


@case("C4-结构类型错误不崩溃")
def _(r: Runner, d: Path):
    (d / "todos.json").write_text('{"todos": "oops"}', encoding="utf-8")
    r.run("list", cwd=d).ok("结构错误 list").err_has("结构不正确")
    r.run("add", "aaa", cwd=d).ok("结构错误 add")
    assert read_store(d)["todos"][0]["id"] == 1


@case("C5-空对象缺 todos 键不崩溃")
def _(r: Runner, d: Path):
    (d / "todos.json").write_text("{}", encoding="utf-8")
    r.run("list", cwd=d).ok("空对象 list")
    r.run("add", "aaa", cwd=d).ok("空对象 add")
    assert read_store(d)["todos"][0]["id"] == 1


@case("C6-兼容裸列表格式并忽略坏记录")
def _(r: Runner, d: Path):
    (d / "todos.json").write_text(
        '{"next_id": 5, "todos": [{"id": 1, "title": "ok"}, {"id": "bad"}, "junk"]}',
        encoding="utf-8",
    )
    out = r.run("list", "--all", cwd=d).ok("坏记录 list").out
    res_err = out
    assert "ok" in res_err
    body = "\n".join(table_lines(out)[2:])
    assert "bad" not in body and "junk" not in body, out
    r.run("add", "new", cwd=d).ok("坏记录 add").out_has("已添加 #5")
    assert [t["id"] for t in read_store(d)["todos"]] == [1, 5]


@case("C8-数据文件被目录占位时不崩溃")
def _(r: Runner, d: Path):
    (d / "todos.json").mkdir()  # 模拟「路径存在但不可读写」的异常场景
    r.run("list", cwd=d).ok("目录占位 list").err_has("数据文件")
    r.run("add", "aaa", cwd=d).fail(1, "目录占位 add").err_has("数据文件")
    r.run("done", "1", cwd=d).fail(1, "目录占位 done").err_has("数据文件")


@case("C7-列表形态的历史数据可读")
def _(r: Runner, d: Path):
    (d / "todos.json").write_text('[{"id": 3, "title": "old", "done": true}]', encoding="utf-8")
    out = r.run("list", "--all", cwd=d).ok("裸列表 list").out
    assert "old" in out and "已完成" in out, out
    r.run("add", "new", cwd=d).ok().out_has("已添加 #4")


# --- 段位4：安全注入（标题只当数据，绝不执行/绝不越权）------------------------


@case("D1-shell 元字符标题不执行")
def _(r: Runner, d: Path):
    title = "$(whoami) && rm -rf / ; ls `id` | echo > pwned.txt"
    r.run("add", title, cwd=d).ok("注入标题")
    assert read_store(d)["todos"][0]["title"] == title
    files = sorted(p.name for p in d.iterdir())
    assert files == ["todos.json"], f"目录中出现了预期外的文件：{files}"


@case("D2-路径穿越标题不写文件")
def _(r: Runner, d: Path):
    work = d / "work"
    work.mkdir()
    r.run("add", "../../evil.txt", cwd=work).ok("路径穿越标题")
    assert read_store(work)["todos"][0]["title"] == "../../evil.txt"
    assert not (d / "evil.txt").exists(), "标题不应被当作路径写出"


@case("D3-ANSI 转义序列被清除")
def _(r: Runner, d: Path):
    title = "\x1b[31mRED\x1b[0m"
    r.run("add", title, cwd=d).ok("ANSI 标题")
    stored = read_store(d)["todos"][0]["title"]
    assert "\x1b" not in stored, f"存储中残留控制字符：{stored!r}"
    out = r.run("list", cwd=d).ok()
    assert b"\x1b" not in out.out_raw, "输出中残留 ANSI 转义序列"


# --- 段位5：命令行契约 --------------------------------------------------------


@case("E1-无参数返回用法错误")
def _(r: Runner, d: Path):
    r.run(cwd=d).fail(2, "无参数").err_has("usage")


@case("E2-未知命令返回用法错误")
def _(r: Runner, d: Path):
    r.run("frobnicate", cwd=d).fail(2, "未知命令").err_has("usage")


@case("E3-非法 id 返回用法错误")
def _(r: Runner, d: Path):
    r.run("done", "abc", cwd=d).fail(2, "done abc").err_has("正整数")
    r.run("done", "0", cwd=d).fail(2, "done 0").err_has("正整数")
    r.run("done", "-1", cwd=d).fail(2, "done -1")
    r.run("rm", "abc", cwd=d).fail(2, "rm abc").err_has("正整数")


@case("E4-help 可用")
def _(r: Runner, d: Path):
    r.run("--help", cwd=d).ok("--help").out_has("add")
    r.run("add", "--help", cwd=d).ok("add --help").out_has("title")


@case("E5-混合宽度标题的表格对齐")
def _(r: Runner, d: Path):
    for title in ("中文标题", "a", "🎉🎉🎉", "中文abc", "🎉"):
        r.run("add", title, cwd=d).ok()
    out = r.run("list", cwd=d).ok().out
    assert_aligned(table_lines(out), "混合宽度表格")
    for title in ("中文标题", "🎉🎉🎉"):
        assert title in out, f"{title!r} 未出现在输出中：{out!r}"


# ------------------------------------------------------------------- 变异测试集

MUTANTS: list[tuple[str, str, str, str]] = [
    (
        "M01 不校验空标题",
        "    if not title:",
        "    if False:",
    ),
    (
        "M02 不 strip 标题",
        "    return text.strip()",
        "    return text",
    ),
    (
        "M03 不清理换行",
        '    text = text.replace("\\n", " ").replace("\\t", " ")',
        '    text = text.replace("\\t", " ")',
    ),
    (
        "M04 不剔除控制字符",
        '    text = CONTROL_CHARS_RE.sub("", text)',
        "    text = text",
    ),
    (
        "M05 id 不自增",
        "    next_id = max(highest + 1, 1)",
        "    next_id = 1",
    ),
    (
        "M06 done 不查 id 是否存在",
        '    if target is None:\n        print(f"错误：未找到 id={args.id} 的待办。", file=sys.stderr)\n        return EXIT_ERROR\n    if target["done"]:',
        '    if False:\n        print(f"错误：未找到 id={args.id} 的待办。", file=sys.stderr)\n        return EXIT_ERROR\n    if target["done"]:',
    ),
    (
        "M07 rm 删错条目（总删第一条）",
        "    store.todos.remove(target)",
        "    store.todos.remove(store.todos[0])",
    ),
    (
        "M08 损坏 JSON 不降级",
        "    except json.JSONDecodeError:",
        "    except ZeroDivisionError:",
    ),
    (
        "M09 文件缺失不降级",
        "        return Store([], 1, None)",
        '        raise RuntimeError("boom")',
    ),
    (
        "M10 --all 失效（默认全列）",
        '    visible = todos if args.all else [t for t in todos if not t["done"]]',
        "    visible = todos",
    ),
    (
        "M11 空库无友好提示",
        '    if not todos:\n        print(\'还没有任何待办。用 python todo.py add "标题" 添加第一条吧。\')\n        return EXIT_OK',
        "    if not todos:\n        return EXIT_OK",
    ),
    (
        "M12 全部完成时无提示",
        '    if not visible:\n        print(f"没有未完成的待办了（共 {len(todos)} 条已完成，用 --all 查看全部）。")\n        return EXIT_OK',
        "    if not visible:\n        return EXIT_OK",
    ),
    (
        "M13 done 不落盘",
        '    save_store(path, store.todos, store.next_id)\n    print(f"已完成 #{args.id}：{target[\'title\']}")',
        '    print(f"已完成 #{args.id}：{target[\'title\']}")',
    ),
    (
        "M14 rm 不落盘",
        '    save_store(path, store.todos, store.next_id)\n    print(f"已删除 #{args.id}：{target[\'title\']}")',
        '    print(f"已删除 #{args.id}：{target[\'title\']}")',
    ),
    (
        "M15 表格按字符数而非显示宽度填充",
        '    filling = " " * max(0, width - display_width(text))',
        '    filling = " " * max(0, width - len(text))',
    ),
    (
        "M16 不做 UTF-8 化",
        "    force_utf8()",
        "    pass",
    ),
    (
        "M17 不截断超长标题",
        "                    pad(truncate(title, title_width), title_width),",
        "                    pad(title, title_width),",
    ),
    (
        "M18 状态标签写反",
        '            DONE_LABEL if t["done"] else UNDONE_LABEL,',
        '            UNDONE_LABEL if t["done"] else DONE_LABEL,',
    ),
    (
        "M19 不记录创建时间",
        '        "created_at": datetime.now().strftime(TIME_FORMAT),',
        '        "created_at": "",',
    ),
    (
        "M20 next_id 不递增",
        "    save_store(path, store.todos, store.next_id + 1)",
        "    save_store(path, store.todos, store.next_id)",
    ),
    (
        "M21 写入失败不兜底（直接抛栈）",
        '    except OSError as exc:\n        # 读取失败已在 load_store 内降级；这里兜底写入失败（文件被占用 / 只读 等）\n        print(f"错误：读写数据文件 {DATA_FILE_NAME} 失败（{exc.strerror}）。", file=sys.stderr)\n        return EXIT_ERROR',
        "    except OSError:\n        raise",
    ),
    (
        "M22 list 不按 id 排序",
        '    todos = sorted(store.todos, key=lambda t: t["id"])',
        "    todos = list(store.todos)",
    ),
]


def apply_mutant(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"目标片段出现 {count} 次（应为 1 次），无法生成变异体")
    return source.replace(old, new)


# ------------------------------------------------------------------------- 主流程


def run_battery(runner: Runner, stop_on_first_fail: bool = False) -> list[tuple[str, str | None]]:
    """返回 [(用例名, 失败原因 or None)]。"""
    outcomes: list[tuple[str, str | None]] = []
    for name, fn in CASES:
        with tempfile.TemporaryDirectory(prefix="todo-case-") as tmp:
            try:
                fn(runner, Path(tmp))
                outcomes.append((name, None))
            except AssertionError as exc:
                outcomes.append((name, str(exc) or "断言失败"))
                if stop_on_first_fail:
                    return outcomes
            except Exception as exc:  # 崩溃/超时也算失败
                outcomes.append((name, f"{type(exc).__name__}: {exc}"))
                if stop_on_first_fail:
                    return outcomes
    return outcomes


def run_mutation(source_path: Path) -> list[tuple[str, str, str]]:
    """对每个变异体：生成改坏的代码 → 跑电池 → 是否被杀。返回 [(编号名, 结果, 说明)]。"""
    source = source_path.read_text(encoding="utf-8")
    rows: list[tuple[str, str, str]] = []
    for name, old, new in MUTANTS:
        with tempfile.TemporaryDirectory(prefix="todo-mutant-") as tmp:
            mutant_dir = Path(tmp)
            try:
                mutated = apply_mutant(source, old, new)
            except ValueError as exc:
                rows.append((name, "SKIP", str(exc)))
                continue
            mutant_file = mutant_dir / "todo.py"
            mutant_file.write_text(mutated, encoding="utf-8")
            outcomes = run_battery(Runner(mutant_file), stop_on_first_fail=True)
            killed = [n for n, reason in outcomes if reason]
            if killed:
                rows.append((name, "KILLED", f"首个红灯用例：{killed[0]}"))
            else:
                rows.append((name, "SURVIVED", "电池全绿 —— 该处缺乏鉴别力"))
    return rows


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    args = [a for a in argv[1:]]
    no_mutation = "--no-mutation" in args
    args = [a for a in args if a != "--no-mutation"]
    todo = Path(args[0]).resolve() if args else DEFAULT_TODO

    print("=" * 78)
    print(f"验证对象: {todo}")
    print(f"解释器  : {sys.executable}  Python {sys.version.split()[0]}")
    print(f"终端宽度: COLUMNS={COLUMNS}（固定，保证可复算）")
    print("=" * 78)

    if not todo.exists():
        print(f"FATAL: 找不到待验证文件 {todo}")
        return 1

    print(f"\n[电池] 共 {len(CASES)} 个用例\n" + "-" * 78)
    outcomes = run_battery(Runner(todo))
    failed = [(n, r) for n, r in outcomes if r]
    for name, reason in outcomes:
        print(f"{'PASS' if reason is None else 'FAIL'}  {name}")
        if reason:
            print(f"      -> {reason}")
    print("-" * 78)
    print(f"电池结果: {len(outcomes) - len(failed)}/{len(outcomes)} 通过")

    kill_rate_line = ""
    survived: list[tuple[str, str, str]] = []
    if not no_mutation:
        print(f"\n[变异测试] 共 {len(MUTANTS)} 个变异体（证明电池有鉴别力）\n" + "-" * 78)
        rows = run_mutation(todo)
        for name, state, note in rows:
            print(f"{state:<9} {name}  —— {note}")
        applicable = [r for r in rows if r[1] != "SKIP"]
        survived = [r for r in rows if r[1] == "SURVIVED"]
        killed = [r for r in rows if r[1] == "KILLED"]
        rate = len(killed) / len(applicable) if applicable else 0.0
        kill_rate_line = f"变异杀伤率: {len(killed)}/{len(applicable)} = {rate:.0%}（跳过 {len(rows) - len(applicable)} 个失效变异体）"
        print("-" * 78)
        print(kill_rate_line)

    print("\n" + "=" * 78)
    ok = not failed and not survived
    if failed:
        print(f"结论: FAIL —— {len(failed)} 个用例未通过")
    elif survived:
        print(f"结论: FAIL —— {len(survived)} 个变异体存活（电池鉴别力不足）")
    else:
        print("结论: PASS —— 电池全绿，且全部变异体被杀（电池具备鉴别力）")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
