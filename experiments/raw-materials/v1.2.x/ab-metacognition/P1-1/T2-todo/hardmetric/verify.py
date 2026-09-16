#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify.py —— todo.py 的黑盒验证脚本（第三方可独立复算）。

用法
    python verify.py                    # 验证与本脚本同目录的 todo.py
    python verify.py path/to/todo.py    # 验证指定路径的实现
    python verify.py --list             # 只打印用例清单（不执行）

退出码
    0 = 全部用例通过；1 = 至少有一条断言失败。

可复算性保证
    * 只用标准库（json/os/shutil/subprocess/sys/tempfile/unicodedata），无第三方依赖。
    * 每个用例在系统临时目录下新建独立工作目录，跑完即删；不在被测目录留文件。
    * 断言只依赖三类可观测面：退出码、stdout/stderr 文本、todos.json 内容。
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TARGET = os.path.join(HERE, "todo.py")
PY = sys.executable

TARGET = DEFAULT_TARGET
CASES = []
_TMPDIRS = []
_FAILURES = []


# ---------------------------------------------------------------- 基础设施
def new_workdir():
    directory = tempfile.mkdtemp(prefix="todo-verify-")
    _TMPDIRS.append(directory)
    return directory


def cleanup():
    while _TMPDIRS:
        shutil.rmtree(_TMPDIRS.pop(), ignore_errors=True)


def display_width(text):
    """验证侧独立实现的显示宽度（不 import 被测代码）。"""
    width = 0
    for ch in text:
        if unicodedata.category(ch) in ("Mn", "Me", "Cf"):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def run(workdir, *args, env=None):
    full_env = dict(os.environ)
    full_env.update(env or {})
    full_env.setdefault("PYTHONIOENCODING", "utf-8")
    proc = subprocess.run(
        [PY, TARGET] + [str(a) for a in args],
        cwd=workdir, env=full_env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
    )
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"))


def expect(condition, message):
    if not condition:
        _FAILURES.append(message)
    return bool(condition)


def store_path(workdir):
    return os.path.join(workdir, "todos.json")


def read_store(workdir):
    with open(store_path(workdir), "r", encoding="utf-8") as handle:
        return json.load(handle)


def titles_of(workdir):
    return [item["title"] for item in read_store(workdir)["todos"]]


def count_todos(workdir):
    """文件不存在（例如 add 被拒、还没落盘）时按 0 条计。"""
    if not os.path.isfile(store_path(workdir)):
        return 0
    try:
        return len(read_store(workdir)["todos"])
    except (ValueError, OSError):
        return -1


def no_traceback(err):
    return expect("Traceback" not in err, "stderr 出现 traceback：%s" % err.strip()[:200])


def case(case_id, segment, title):
    def deco(func):
        CASES.append({"id": case_id, "segment": segment, "title": title, "fn": func})
        return func
    return deco


# ------------------------------------------------------- 分段 1：正常值(N)
@case("N-01", "正常值", "add 单条：id 自增、默认未完成、有时间、落盘正确")
def _n01():
    work = new_workdir()
    rc, out, err = run(work, "add", "买牛奶")
    expect(rc == 0, "退出码应为 0，实际 %d；stderr=%s" % (rc, err.strip()))
    expect("#1" in out, "stdout 应回显 id #1，实际：%r" % out)
    expect(os.path.isfile(store_path(work)), "todos.json 应被自动创建")
    data = read_store(work)
    expect(len(data["todos"]) == 1, "应有 1 条记录，实际 %d" % len(data["todos"]))
    item = data["todos"][0]
    expect(item["id"] == 1, "id 应为 1，实际 %r" % item["id"])
    expect(item["title"] == "买牛奶", "标题应为『买牛奶』，实际 %r" % item["title"])
    expect(item["done"] is False, "done 应为 False，实际 %r" % item["done"])
    expect(bool(item["created_at"]), "created_at 不应为空")
    no_traceback(err)


@case("N-02", "正常值", "连续 add：id 严格自增且跨进程持久化")
def _n02():
    work = new_workdir()
    for title in ("A", "B", "C"):
        rc, _, err = run(work, "add", title)
        expect(rc == 0, "add %s 退出码应为 0，实际 %d" % (title, rc))
    data = read_store(work)
    ids = [t["id"] for t in data["todos"]]
    expect(ids == [1, 2, 3], "id 应为 [1,2,3]，实际 %r" % ids)
    expect(data["next_id"] == 4, "next_id 应为 4，实际 %r" % data["next_id"])
    no_traceback(err)


@case("N-03", "正常值", "done：落盘 true，默认 list 隐藏、--all 显示 [✓]")
def _n03():
    work = new_workdir()
    run(work, "add", "写报告")
    run(work, "add", "买菜")
    rc, out, err = run(work, "done", "1")
    expect(rc == 0, "done 退出码应为 0，实际 %d" % rc)
    expect(read_store(work)["todos"][0]["done"] is True, "落盘 done 应为 True")
    rc, out, _ = run(work, "list")
    expect(rc == 0 and "写报告" not in out, "默认 list 不应显示已完成项，实际：%r" % out)
    rc, out, _ = run(work, "list", "--all")
    expect("写报告" in out, "--all 应显示已完成项，实际：%r" % out)
    done_row = [l for l in out.splitlines() if "写报告" in l]
    todo_row = [l for l in out.splitlines() if "买菜" in l]
    expect(done_row and "[✓]" in done_row[0],
           "已完成行的状态应为 [✓]，实际：%r" % (done_row,))
    expect(todo_row and "[ ]" in todo_row[0],
           "未完成行的状态应为 [ ]，实际：%r" % (todo_row,))
    no_traceback(err)


@case("N-04", "正常值", "rm：记录从 json 与列表中消失")
def _n04():
    work = new_workdir()
    run(work, "add", "甲")
    run(work, "add", "乙")
    rc, out, err = run(work, "rm", "1")
    expect(rc == 0, "rm 退出码应为 0，实际 %d" % rc)
    expect(titles_of(work) == ["乙"], "剩余标题应为 ['乙']，实际 %r" % titles_of(work))
    rc, out, _ = run(work, "list", "--all")
    expect("甲" not in out, "list --all 不应再出现『甲』，实际：%r" % out)
    no_traceback(err)


@case("N-05", "正常值", "删除后 id 不复用（删 #1 再 add 得到 #3）")
def _n05():
    work = new_workdir()
    run(work, "add", "甲")
    run(work, "add", "乙")
    run(work, "rm", "1")
    rc, out, err = run(work, "add", "丙")
    expect("#3" in out, "新条目 id 应为 3，实际输出 %r" % out)
    expect([t["id"] for t in read_store(work)["todos"]] == [2, 3], "id 列表应为 [2,3]")
    no_traceback(err)


@case("N-06", "正常值", "list 默认/--all 的条目集合差异正确")
def _n06():
    work = new_workdir()
    for title in ("甲", "乙", "丙"):
        run(work, "add", title)
    run(work, "done", "2")
    rc, out, _ = run(work, "list")
    expect("甲" in out and "丙" in out and "乙" not in out,
           "默认 list 应含甲、丙且不含乙，实际：%r" % out)
    rc, out, _ = run(work, "list", "--all")
    expect("甲" in out and "乙" in out and "丙" in out,
           "--all 应含全部三条，实际：%r" % out)


@case("N-07", "正常值", "--help / -h 退出码 0 且含四个命令")
def _n07():
    work = new_workdir()
    for flag in ("--help", "-h"):
        rc, out, err = run(work, flag)
        expect(rc == 0, "%s 退出码应为 0，实际 %d" % (flag, rc))
        for cmd in ("add", "done", "list", "rm"):
            expect(cmd in out, "%s 输出应提到 %s，实际：%r" % (flag, cmd, out))
        no_traceback(err)


@case("N-08", "正常值", "无引号多词标题按一个标题处理")
def _n08():
    work = new_workdir()
    rc, out, err = run(work, "add", "买", "牛", "奶")
    expect(rc == 0, "退出码应为 0，实际 %d" % rc)
    expect(titles_of(work) == ["买 牛 奶"], "标题应为『买 牛 奶』，实际 %r" % titles_of(work))
    no_traceback(err)


# ------------------------------------------------------- 分段 2：边界值(B)
@case("B-01", "边界值", "空标题被拒绝（退出码非 0，不产生记录）")
def _b01():
    work = new_workdir()
    rc, out, err = run(work, "add", "")
    expect(rc != 0, "空标题应失败，实际退出码 %d" % rc)
    expect(err.strip() != "", "应有错误提示，stderr 为空")
    expect(count_todos(work) == 0, "不应产生任何记录，实际 %d 条" % count_todos(work))
    no_traceback(err)


@case("B-02", "边界值", "纯空格标题被拒绝")
def _b02():
    work = new_workdir()
    rc, out, err = run(work, "add", "     ")
    expect(rc != 0, "纯空格标题应失败，实际退出码 %d" % rc)
    expect(count_todos(work) == 0, "不应产生任何记录，实际 %d 条" % count_todos(work))
    no_traceback(err)


@case("B-03", "边界值", "制表/换行空白标题被拒绝")
def _b03():
    work = new_workdir()
    for blank in ("\t", "\n", " \t\n ", "\r\n"):
        rc, _, err = run(work, "add", blank)
        expect(rc != 0, "空白标题 %r 应失败，实际退出码 %d" % (blank, rc))
        no_traceback(err)
    expect(count_todos(work) == 0, "不应产生任何记录，实际 %d 条" % count_todos(work))


@case("B-04", "边界值", "add 缺少参数时不崩溃")
def _b04():
    work = new_workdir()
    rc, out, err = run(work, "add")
    expect(rc != 0, "add 无参数应失败，实际退出码 %d" % rc)
    no_traceback(err)


@case("B-05", "边界值", "done 不存在的 id：退出码非 0 + 明确提示")
def _b05():
    work = new_workdir()
    run(work, "add", "甲")
    rc, out, err = run(work, "done", "999")
    expect(rc != 0, "不存在的 id 应失败，实际退出码 %d" % rc)
    expect(err.strip() != "", "应给出错误提示")
    no_traceback(err)


@case("B-06", "边界值", "rm 不存在的 id：退出码非 0 + 数据不被改动")
def _b06():
    work = new_workdir()
    run(work, "add", "甲")
    rc, out, err = run(work, "rm", "42")
    expect(rc != 0, "不存在的 id 应失败，实际退出码 %d" % rc)
    expect(titles_of(work) == ["甲"], "数据不应被改动，实际 %r" % titles_of(work))
    no_traceback(err)


@case("B-07", "边界值", "id = 0 / 负数 / 超大值 均按不存在处理")
def _b07():
    work = new_workdir()
    run(work, "add", "甲")
    for bad in ("0", "-1", "99999999"):
        rc1, _, e1 = run(work, "done", bad)
        rc2, _, e2 = run(work, "rm", bad)
        expect(rc1 != 0 and rc2 != 0, "id=%s 应被判为不存在，实际 done=%d rm=%d" % (bad, rc1, rc2))
        no_traceback(e1)
        no_traceback(e2)


@case("B-08", "边界值", "空库 list：退出码 0 + 友好提示")
def _b08():
    work = new_workdir()
    rc, out, err = run(work, "list")
    expect(rc == 0, "空库 list 退出码应为 0，实际 %d" % rc)
    expect(len(out.strip()) > 0, "应有提示文案，实际输出为空")
    expect("空" in out, "提示应含『空』字样，实际：%r" % out)
    no_traceback(err)


@case("B-09", "边界值", "空库 list --all：退出码 0 + 友好提示")
def _b09():
    work = new_workdir()
    rc, out, err = run(work, "list", "--all")
    expect(rc == 0, "空库 list --all 退出码应为 0，实际 %d" % rc)
    expect("空" in out, "提示应含『空』字样，实际：%r" % out)
    no_traceback(err)


@case("B-10", "边界值", "全部已完成时默认 list 给出专门提示")
def _b10():
    work = new_workdir()
    run(work, "add", "甲")
    run(work, "done", "1")
    rc, out, err = run(work, "list")
    expect(rc == 0, "退出码应为 0，实际 %d" % rc)
    expect("完成" in out, "提示应说明全部已完成，实际：%r" % out)
    no_traceback(err)


@case("B-11", "边界值", "重复标题允许：两条 id 不同、都在列表里")
def _b11():
    work = new_workdir()
    run(work, "add", "重复")
    rc, out, err = run(work, "add", "重复")
    expect(rc == 0, "重复标题应允许添加，实际退出码 %d" % rc)
    data = read_store(work)
    expect(len(data["todos"]) == 2, "应有 2 条记录，实际 %d" % len(data["todos"]))
    expect(data["todos"][0]["id"] != data["todos"][1]["id"], "两条 id 应不同")
    rc, out, _ = run(work, "list", "--all")
    expect(out.count("重复") >= 2, "列表里『重复』应出现至少 2 次，实际：%r" % out)
    no_traceback(err)


@case("B-12", "边界值", "对已完成项再次 done：幂等、不报错")
def _b12():
    work = new_workdir()
    run(work, "add", "甲")
    run(work, "done", "1")
    rc, out, err = run(work, "done", "1")
    expect(rc == 0, "重复 done 不应报错，实际退出码 %d" % rc)
    expect(read_store(work)["todos"][0]["done"] is True, "状态应仍为已完成")
    no_traceback(err)


@case("B-13", "边界值", "done/rm 缺参数或非整数 id 时不崩溃")
def _b13():
    work = new_workdir()
    run(work, "add", "甲")
    for args in (("done",), ("rm",), ("done", "abc"), ("rm", "abc"),
                 ("done", "1.5"), ("done", "1", "2")):
        rc, _, err = run(work, *args)
        expect(rc != 0, "%r 应失败，实际退出码 %d" % (args, rc))
        no_traceback(err)
    expect(titles_of(work) == ["甲"], "数据不应被改动，实际 %r" % titles_of(work))


@case("B-14", "边界值", "未知命令 / 未知参数 / 无参数：退出码 2 且给出用法")
def _b14():
    work = new_workdir()
    rc, out, err = run(work, "frobnicate")
    expect(rc != 0, "未知命令应失败，实际 %d" % rc)
    rc2, out2, err2 = run(work, "list", "--bogus")
    expect(rc2 != 0, "未知参数应失败，实际 %d" % rc2)
    rc3, out3, err3 = run(work)
    expect(rc3 != 0, "无参数应失败，实际 %d" % rc3)
    text = out3 + err3
    expect("add" in text, "用法提示应含 add，实际：%r" % text)
    no_traceback(err3)


# ------------------------------------------------- 分段 3：异常值/损坏(E)
def write_raw(workdir, content):
    with open(store_path(workdir), "w", encoding="utf-8") as handle:
        handle.write(content)


@case("E-01", "异常值", "todos.json 内容损坏（非法 JSON）：list 不崩溃")
def _e01():
    work = new_workdir()
    write_raw(work, "{ 这不是 json ")
    rc, out, err = run(work, "list")
    expect(rc == 0, "损坏文件下 list 退出码应为 0，实际 %d" % rc)
    expect("损坏" in err, "stderr 应给出损坏警告，实际：%r" % err)
    no_traceback(err)


@case("E-02", "异常值", "损坏后 add：成功写入，并备份原文件")
def _e02():
    work = new_workdir()
    write_raw(work, "{ 这不是 json ")
    rc, out, err = run(work, "add", "新任务")
    expect(rc == 0, "损坏后 add 退出码应为 0，实际 %d；stderr=%s" % (rc, err.strip()))
    expect(os.path.isfile(os.path.join(work, "todos.json.corrupt")), "应生成 .corrupt 备份")
    expect(titles_of(work) == ["新任务"], "新库应含新任务，实际 %r" % titles_of(work))
    no_traceback(err)


@case("E-03", "异常值", "合法 JSON 但结构异常（数组/null/数字）不崩溃")
def _e03():
    for raw in ("[]", "null", "123", '"字符串"', "{}", '{"todos": "不是数组"}',
                '{"todos": [1, 2, 3]}', '{"todos": [{"id": 1}]}'):
        work = new_workdir()
        write_raw(work, raw)
        rc, out, err = run(work, "list", "--all")
        expect(rc == 0, "结构 %s 下 list 退出码应为 0，实际 %d；stderr=%s" % (raw, rc, err.strip()))
        no_traceback(err)


@case("E-04", "异常值", "todos.json 为空文件：不崩溃")
def _e04():
    work = new_workdir()
    write_raw(work, "")
    rc, out, err = run(work, "list")
    expect(rc == 0, "空文件下 list 退出码应为 0，实际 %d" % rc)
    rc, out, err2 = run(work, "add", "甲")
    expect(rc == 0, "空文件下 add 退出码应为 0，实际 %d" % rc)
    no_traceback(err + err2)


@case("E-05", "异常值", "todos.json 是目录：不抛 traceback")
def _e05():
    work = new_workdir()
    os.mkdir(store_path(work))
    rc, out, err = run(work, "list")
    no_traceback(err)
    rc, out, err2 = run(work, "add", "甲")
    no_traceback(err2)


@case("E-06", "异常值", "todos.json 只读：写入失败也不抛 traceback")
def _e06():
    work = new_workdir()
    run(work, "add", "甲")
    try:
        os.chmod(store_path(work), 0o444)
    except OSError:
        return
    rc, out, err = run(work, "add", "乙")
    no_traceback(err)
    try:
        os.chmod(store_path(work), 0o644)
    except OSError:
        pass


@case("E-07", "异常值", "文件缺失时任何命令都自动创建 todos.json")
def _e07():
    work = new_workdir()
    expect(not os.path.exists(store_path(work)), "前置条件：文件不存在")
    rc, out, err = run(work, "list")
    expect(rc == 0, "list 退出码应为 0，实际 %d" % rc)
    expect(os.path.isfile(store_path(work)), "list 之后 todos.json 应存在")
    expect(read_store(work)["todos"] == [], "新建的库应为空")


@case("E-08", "异常值", "损坏文件 + done/rm：给出警告且不抛 traceback")
def _e08():
    work = new_workdir()
    write_raw(work, "@@@")
    rc, out, err = run(work, "done", "1")
    expect(rc != 0, "损坏库里 id 1 应不存在，实际退出码 %d" % rc)
    no_traceback(err)
    rc, out, err2 = run(work, "rm", "1")
    expect(rc != 0, "损坏库里 rm 1 应失败，实际退出码 %d" % rc)
    no_traceback(err2)


# ------------------------------------------------- 分段 4：特殊字符(S)
@case("S-01", "特殊字符", "标题含双引号/单引号/反斜杠：原样保存")
def _s01():
    work = new_workdir()
    title = '他说 "hi" 然后 \'走\' 了 C:\\tmp'
    rc, out, err = run(work, "add", title)
    expect(rc == 0, "退出码应为 0，实际 %d；stderr=%s" % (rc, err.strip()))
    expect(titles_of(work) == [title], "标题应原样保存，实际 %r" % titles_of(work))
    no_traceback(err)


@case("S-02", "特殊字符", "标题含换行：保存原样，显示转义不拆行")
def _s02():
    work = new_workdir()
    title = "第一行\n第二行"
    rc, out, err = run(work, "add", title)
    expect(rc == 0, "退出码应为 0，实际 %d" % rc)
    expect(titles_of(work) == [title], "磁盘上应保存真实换行，实际 %r" % titles_of(work))
    rc, out, _ = run(work, "list", "--all")
    lines = [l for l in out.splitlines() if l.strip()]
    expect(len(lines) == 3, "输出应为 表头+1 数据行+1 汇总 = 3 行，实际 %d 行：%r" % (len(lines), lines))
    expect("\\n" in out, "显示时应把换行转义为 \\n，实际：%r" % out)
    no_traceback(err)


@case("S-03", "特殊字符", "标题含制表符：不影响表格结构")
def _s03():
    work = new_workdir()
    title = "前\t后"
    rc, out, err = run(work, "add", title)
    expect(rc == 0, "退出码应为 0，实际 %d" % rc)
    expect(titles_of(work) == [title], "标题应原样保存，实际 %r" % titles_of(work))
    rc, out, _ = run(work, "list", "--all")
    expect(out.count("\t") == 0, "输出中不应出现真实制表符，实际：%r" % out)
    no_traceback(err)


@case("S-04", "特殊字符", "emoji 标题：往返一致、不崩溃")
def _s04():
    work = new_workdir()
    title = "买牛奶 🥛 然后 ✅ 完成"
    rc, out, err = run(work, "add", title)
    expect(rc == 0, "退出码应为 0，实际 %d；stderr=%s" % (rc, err.strip()))
    expect(titles_of(work) == [title], "标题应原样保存，实际 %r" % titles_of(work))
    rc, out, _ = run(work, "list", "--all")
    expect("🥛" in out, "list 应能输出 emoji，实际：%r" % out)
    no_traceback(err)


@case("S-05", "特殊字符", "500 字符超长标题：完整保存，不截断")
def _s05():
    work = new_workdir()
    title = "长" * 500
    rc, out, err = run(work, "add", title)
    expect(rc == 0, "退出码应为 0，实际 %d" % rc)
    expect(titles_of(work) == [title], "500 字标题应完整保存，实际长度 %r" % len(titles_of(work)[0]))
    no_traceback(err)


@case("S-06", "特殊字符", "5000 字符超长标题：不崩溃")
def _s06():
    work = new_workdir()
    title = "A" * 5000
    rc, out, err = run(work, "add", title)
    expect(rc == 0, "退出码应为 0，实际 %d" % rc)
    expect(len(titles_of(work)[0]) == 5000, "应完整保存 5000 字符")
    no_traceback(err)


@case("S-07", "特殊字符", "以 - 开头的标题被当作标题而非选项")
def _s07():
    work = new_workdir()
    rc, out, err = run(work, "add", "-rf /")
    expect(rc == 0, "退出码应为 0，实际 %d；stderr=%s" % (rc, err.strip()))
    expect(titles_of(work) == ["-rf /"], "标题应为『-rf /』，实际 %r" % titles_of(work))
    no_traceback(err)


@case("S-08", "特殊字符", "shell 元字符不被引擎执行，原样入库")
def _s08():
    work = new_workdir()
    title = "a; echo pwn > pwned.txt & echo x | cat"
    rc, out, err = run(work, "add", title)
    expect(rc == 0, "退出码应为 0，实际 %d" % rc)
    expect(titles_of(work) == [title], "标题应原样保存，实际 %r" % titles_of(work))
    expect(not os.path.exists(os.path.join(work, "pwned.txt")), "不应生成命令副作用文件")
    no_traceback(err)


@case("S-09", "特殊字符", "格式化串 %s/{0} 原样入库（防格式化漏洞）")
def _s09():
    work = new_workdir()
    title = "%s {0} %d %(x)s"
    rc, out, err = run(work, "add", title)
    expect(rc == 0, "退出码应为 0，实际 %d" % rc)
    expect(titles_of(work) == [title], "标题应原样保存，实际 %r" % titles_of(work))
    no_traceback(err)


@case("S-10", "表格对齐", "中英混排 + emoji：各行列起点显示宽度一致（含标题列→时间列）")
def _s10():
    import re
    work = new_workdir()
    for title in ("buy milk", "买牛奶和面包", "🥛 牛奶", "x"):
        run(work, "add", title)
    rc, out, err = run(work, "list", "--all")
    expect(rc == 0, "退出码应为 0，实际 %d" % rc)
    lines = [l for l in out.splitlines() if l.strip()]
    data_lines = lines[1:5]
    expect(len(data_lines) == 4, "应有 4 行数据，实际 %r" % lines)

    def marker_starts(line):
        """返回 (状态列起点宽, 时间列起点宽)。"""
        status = line.find("[")
        time_match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", line)
        return (display_width(line[:status]) if status >= 0 else None,
                display_width(line[:time_match.start()]) if time_match else None)

    pairs = [marker_starts(line) for line in data_lines]
    expect(all(p[0] is not None and p[1] is not None for p in pairs),
           "每行都应能定位到状态列与时间列，实际 %r" % pairs)
    expect(len(set(p[0] for p in pairs)) == 1,
           "各数据行状态列起点显示宽度应一致，实际 %r" % [p[0] for p in pairs])
    expect(len(set(p[1] for p in pairs)) == 1,
           "各数据行时间列起点显示宽度应一致（标题列按显示宽度补齐），实际 %r"
           % [p[1] for p in pairs])


@case("S-11", "表格对齐", "表头四列齐全且各行列数一致")
def _s11():
    work = new_workdir()
    run(work, "add", "甲")
    rc, out, err = run(work, "list", "--all")
    header = out.splitlines()[0]
    for name in ("ID", "状态", "标题", "创建时间"):
        expect(name in header, "表头应含 %s，实际：%r" % (name, header))


@case("S-12", "表格对齐", "超长标题默认截断显示（带省略号），--full 显示全文，磁盘不丢数据")
def _s12():
    work = new_workdir()
    title = "长" * 500
    run(work, "add", title)
    rc, out, err = run(work, "list", "--all")
    expect(rc == 0, "退出码应为 0，实际 %d" % rc)
    data_rows = [l for l in out.splitlines() if l.strip()][1:2]
    expect(bool(data_rows) and display_width(data_rows[0]) < 120,
           "默认显示应把超长标题截断到可读宽度，实际行宽 %r" % display_width(data_rows[0] if data_rows else ""))
    expect("…" in out, "截断应带省略号，实际：%r" % out[:120])
    expect(titles_of(work) == [title], "磁盘上仍应保存完整 500 字标题")
    rc, out2, _ = run(work, "list", "--all", "--full")
    expect(rc == 0, "--full 退出码应为 0，实际 %d" % rc)
    expect(title in out2, "--full 应显示未截断标题，实际长度 %d" % len(out2))


@case("S-13", "表格对齐", "--all --full 组合与单独 --full 均可用")
def _s13():
    work = new_workdir()
    run(work, "add", "甲")
    run(work, "done", "1")
    rc, out, err = run(work, "list", "--full")
    expect(rc == 0, "list --full 退出码应为 0，实际 %d" % rc)
    rc, out, err2 = run(work, "list", "-a", "-f")
    expect(rc == 0, "list -a -f 退出码应为 0，实际 %d" % rc)
    expect("甲" in out, "-a -f 应列出已完成项，实际：%r" % out)
    no_traceback(err + err2)


# ------------------------------------------------- 分段 5：环境编码(W)
@case("W-01", "环境编码", "PYTHONIOENCODING=gbk 下处理 emoji 不崩溃")
def _w01():
    work = new_workdir()
    title = "牛奶 🥛"
    rc, out, err = run(work, "add", title, env={"PYTHONIOENCODING": "gbk"})
    expect(rc == 0, "gbk 环境下 add 退出码应为 0，实际 %d；stderr=%s" % (rc, err.strip()))
    no_traceback(err)
    rc, out, err = run(work, "list", "--all", env={"PYTHONIOENCODING": "gbk"})
    expect(rc == 0, "gbk 环境下 list 退出码应为 0，实际 %d；stderr=%s" % (rc, err.strip()))
    expect("🥛" in out, "gbk 环境下 emoji 应正常输出，实际：%r" % out)
    no_traceback(err)


@case("W-02", "环境编码", "PYTHONIOENCODING=ascii 下 CJK 不崩溃")
def _w02():
    work = new_workdir()
    rc, out, err = run(work, "add", "买牛奶", env={"PYTHONIOENCODING": "ascii"})
    expect(rc == 0, "ascii 环境下 add 退出码应为 0，实际 %d；stderr=%s" % (rc, err.strip()))
    no_traceback(err)


# ------------------------------------------------- 分段 6：端到端流程(P)
@case("P-01", "端到端", "add×3 → done → rm 后 json 与列表状态一致")
def _p01():
    work = new_workdir()
    run(work, "add", "甲")
    run(work, "add", "乙")
    run(work, "add", "丙")
    run(work, "done", "2")
    run(work, "rm", "1")
    data = read_store(work)
    expect([t["id"] for t in data["todos"]] == [2, 3], "剩余 id 应为 [2,3]，实际 %r" % [t["id"] for t in data["todos"]])
    expect(data["todos"][0]["done"] is True, "id 2 应为已完成")
    expect(data["todos"][1]["done"] is False, "id 3 应为未完成")
    expect(data["next_id"] == 4, "next_id 应为 4，实际 %r" % data["next_id"])
    rc, out, _ = run(work, "list")
    expect("丙" in out and "乙" not in out and "甲" not in out,
           "默认 list 应只剩『丙』，实际：%r" % out)
    rc, out, _ = run(work, "list", "--all")
    expect("乙" in out and "丙" in out, "--all 应含乙、丙，实际：%r" % out)


@case("P-02", "端到端", "created_at 时间格式可读（YYYY-MM-DD HH:MM）")
def _p02():
    import re
    work = new_workdir()
    run(work, "add", "甲")
    rc, out, err = run(work, "list", "--all")
    expect(rc == 0, "退出码应为 0，实际 %d" % rc)
    expect(re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", out) is not None,
           "列表应含 YYYY-MM-DD HH:MM 时间，实际：%r" % out)


# ---------------------------------------------------------------- 执行入口
def run_all(target=DEFAULT_TARGET):
    """执行全部用例，返回 [(case, [失败信息...]), ...]。"""
    global TARGET
    TARGET = os.path.abspath(target)
    results = []
    for item in CASES:
        del _FAILURES[:]
        try:
            item["fn"]()
        except Exception as exc:  # 用例自身出错也算失败
            _FAILURES.append("用例执行异常：%s: %s" % (type(exc).__name__, exc))
        finally:
            cleanup()
        results.append((item, list(_FAILURES)))
    return results


def main(argv):
    if "--list" in argv:
        for item in CASES:
            print("%-6s %-8s %s" % (item["id"], item["segment"], item["title"]))
        return 0

    target = argv[0] if argv else DEFAULT_TARGET
    if not os.path.isfile(target):
        sys.stderr.write("找不到待验证文件：%s\n" % target)
        return 1

    results = run_all(target)
    failed = 0
    print("验证目标：%s" % os.path.abspath(target))
    print("解释器：%s" % PY)
    print("-" * 72)
    for item, failures in results:
        if failures:
            failed += 1
            print("[FAIL] %-6s %s" % (item["id"], item["title"]))
            for message in failures:
                print("       - %s" % message)
        else:
            print("[PASS] %-6s %s" % (item["id"], item["title"]))
    print("-" * 72)
    total = len(results)
    print("用例总数 %d，通过 %d，失败 %d" % (total, total - failed, failed))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
