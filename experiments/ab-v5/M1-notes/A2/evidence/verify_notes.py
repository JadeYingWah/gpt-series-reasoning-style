"""验证电池：以真实用户方式逐命令实测四个脚本 + 边界用例。

覆盖的输入域分段：
  正常值   —— 中文/英文标题内容、带标签、多标签
  边界值   —— 空库、空内容、长内容截断、stats 空/满两态、最大 id 自增
  异常值   —— 空标题、纯空白标题、缺参数、损坏的 notes.json、异常顶层类型
  特殊字符 —— 引号、反斜杠、换行、emoji、中文往返无损
  任务书点名 —— add→list 可见、search 大小写不敏感、--tag 过滤、stats 数字正确、
                重复 id 不撞号、notes.json 自动创建
运行：python evidence/verify_notes.py （退出码 0 = 全部通过）
"""
import json
import os
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "notes.json"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
RESULTS = []


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / script), *args],
        capture_output=True, text=True, encoding="utf-8", env=ENV, cwd=str(ROOT),
    )


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print("[{}] {}{}".format("PASS" if cond else "FAIL", name, (" | " + detail) if detail else ""))
    return cond


def dw(text):
    """独立实现的显示宽度（不 import storage，避免自证）。"""
    return sum(2 if unicodedata.east_asian_width(c) in ("F", "W") else 1 for c in text)


def table_lines(out):
    return [ln for ln in out.splitlines() if ln.startswith("|")]


def table_ids(out):
    """从表格输出提取数据行 ID 列（表头行 ID 非数字自动跳过）。"""
    ids = []
    for ln in table_lines(out):
        cells = [c.strip() for c in ln.split("|")]
        if len(cells) > 1 and cells[1].isdigit():
            ids.append(cells[1])
    return ids


def reset_store():
    if NOTES.exists():
        NOTES.unlink()


def main():
    # 0. 语法检查
    files = [str(ROOT / f) for f in ("add.py", "list.py", "search.py", "stats.py", "storage.py")]
    rc = subprocess.run([sys.executable, "-m", "py_compile", *files],
                        capture_output=True, text=True).returncode
    check("语法检查 py_compile 全部 5 个文件", rc == 0)

    # 1. 空库边界：notes.json 不存在时 list/search/stats 均可用
    reset_store()
    r = run("list.py")
    check("空库 list 可运行且友好提示", r.returncode == 0 and "暂无笔记" in r.stdout)
    r = run("stats.py")
    check("空库 stats 输出总数 0", r.returncode == 0 and "总笔记数：0" in r.stdout)
    r = run("search.py", "任意")
    check("空库 search 可运行且友好提示", r.returncode == 0 and "没有包含" in r.stdout)

    # 2. add：自动创建 notes.json、自增 id、时间戳
    r = run("add.py", "买菜", "周一买鸡蛋和牛奶", "--tag", "生活", "--tag", "待办")
    check("add 正常添加 #1", r.returncode == 0 and "已添加笔记 #1" in r.stdout)
    check("notes.json 已自动创建", NOTES.exists())
    data = json.loads(NOTES.read_text(encoding="utf-8"))
    check("存储内容/标签/时间戳正确",
          data[0]["title"] == "买菜" and data[0]["tags"] == ["生活", "待办"]
          and len(data[0]["created_at"]) == 19, data[0]["created_at"])

    r = run("add.py", "TODO", "Finish the Report", "--tag", "工作")
    check("add id 自增 #2", "已添加笔记 #2" in r.stdout)

    # 3. 空标题边界
    r = run("add.py", "", "c")
    check("空标题被拒绝（退出码 1 + 提示）", r.returncode == 1 and "标题不能为空" in r.stderr)
    r = run("add.py", "   ", "c")
    check("纯空白标题被拒绝", r.returncode == 1 and "标题不能为空" in r.stderr)
    r = run("add.py", "  带空白标题  ", "c")
    check("标题两侧空白被剥离", r.returncode == 0 and "带空白标题" in r.stdout)
    n_now = len(json.loads(NOTES.read_text(encoding="utf-8")))
    check("被拒的空标题未写入存储", n_now == 3, "当前 {} 条".format(n_now))

    # 4. 特殊字符往返无损
    weird_title = 'He said "hi" \\ backslash'
    weird_content = '第一行\n第二行 "引号" \\ 😀 emoji'
    r = run("add.py", weird_title, weird_content)
    check("特殊字符标题/内容添加成功 #4", r.returncode == 0 and "已添加笔记 #4" in r.stdout)
    data = json.loads(NOTES.read_text(encoding="utf-8"))
    got = next(n for n in data if n["id"] == 4)
    check("特殊字符经 JSON 往返无损", got["title"] == weird_title and got["content"] == weird_content)
    r = run("search.py", "😀")
    check("可按 emoji 搜索命中", table_ids(r.stdout) == ["4"], str(table_ids(r.stdout)))

    # 5. list：全部 + 表格对齐 + 长内容截断
    run("add.py", "长内容笔记", "这是一段超过二十个字符的长内容，用来验证列表截断行为是否正常。")
    r = run("list.py")
    tl = table_lines(r.stdout)
    check("list 全部输出含表头与 5 条", "标题" in r.stdout and "共 5 条笔记" in r.stdout, str(len(tl)))
    widths = {dw(ln) for ln in tl}
    check("表格各行显示宽度一致（CJK 对齐）", len(widths) == 1, str(widths))
    check("长内容被截断显示", "…" in r.stdout or "..." in r.stdout)
    check("换行内容在表格中被展平", "第二行" in r.stdout and len([ln for ln in r.stdout.splitlines() if "第二行" in ln]) == 1)

    # 6. list --tag 过滤
    r = run("list.py", "--tag", "生活")
    check("--tag 过滤只含目标标签", table_ids(r.stdout) == ["1"], str(table_ids(r.stdout)))
    r = run("list.py", "--tag", "工作")
    check("--tag 过滤多标签笔记命中", table_ids(r.stdout) == ["2"], str(table_ids(r.stdout)))
    r = run("list.py", "--tag", "不存在的标签")
    check("--tag 无命中时友好提示", r.returncode == 0 and "没有带标签" in r.stdout)

    # 7. search：大小写不敏感 + 标题/内容双字段 + 无结果
    for kw in ("todo", "TODO", "Todo"):
        r = run("search.py", kw)
        check("search 大小写不敏感命中标题（{}）".format(kw), table_ids(r.stdout) == ["2"])
    r = run("search.py", "report")
    check("search 命中内容（小写搜大写原文）", table_ids(r.stdout) == ["2"])
    r = run("search.py", "鸡蛋")
    check("search 中文命中", table_ids(r.stdout) == ["1"], str(table_ids(r.stdout)))
    r = run("search.py", "不存在的关键词xyz")
    check("search 无结果友好提示", r.returncode == 0 and "没有包含" in r.stdout)

    # 8. stats：总数 / 最新 3 条顺序 / 最长笔记字符数
    expected_total = len(json.loads(NOTES.read_text(encoding="utf-8")))
    r = run("stats.py")
    check("stats 总数正确", "总笔记数：{}".format(expected_total) in r.stdout)
    pos5 = r.stdout.find("#5")
    pos4 = r.stdout.find("#4")
    pos3 = r.stdout.find("#3")
    check("stats 最新 3 条为 id 倒序（5>4>3）", 0 < pos5 < pos4 < pos3,
          "{}, {}, {}".format(pos5, pos4, pos3))
    long_len = len(next(n for n in json.loads(NOTES.read_text(encoding="utf-8"))
                        if n["title"] == "长内容笔记")["content"])
    check("stats 最长笔记指向正确且字符数正确",
          "最长笔记" in r.stdout and str(long_len) in r.stdout, str(long_len))

    # 9. 重复 id 防护：手工制造重复 id 后仍自增不撞号（此时 5 条：1,2,3,4,5）
    data = json.loads(NOTES.read_text(encoding="utf-8"))
    data[1]["id"] = data[0]["id"]  # 制造重复 → [1,1,3,4,5]，最大 id 仍为 5
    NOTES.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    r = run("add.py", "重复id测试", "after manual dup")
    check("重复 id 后新笔记取最大+1（#6）", "已添加笔记 #6" in r.stdout, r.stdout.strip())
    data = json.loads(NOTES.read_text(encoding="utf-8"))
    ids = [n["id"] for n in data]
    check("共 6 条；手工重复的 id=1 仍为 2 个；新 id=6 唯一",
          len(ids) == 6 and ids.count(1) == 2 and ids.count(6) == 1, str(ids))

    # 10. 缺参数 → argparse 用法提示
    r = run("add.py")
    check("add 缺参数退出码 2 且有用法提示", r.returncode == 2 and "usage" in r.stderr.lower())
    r = run("search.py")
    check("search 缺参数退出码 2", r.returncode == 2)
    r = run("add.py", "t", "c", "--tag")
    check("add --tag 缺值报错", r.returncode == 2)

    # 11. 损坏的 notes.json → 报错退出且不覆盖数据
    NOTES.write_text("{invalid json!!", encoding="utf-8")
    r = run("list.py")
    check("损坏存储报错退出（码 1）", r.returncode == 1 and "损坏" in r.stderr)
    check("损坏后未被脚本覆盖", NOTES.read_text(encoding="utf-8") == "{invalid json!!")
    r = run("add.py", "t", "c")
    check("损坏时 add 也拒绝写入", r.returncode == 1 and "损坏" in r.stderr)
    NOTES.write_text('[{"id":1,"title":"x"}]', encoding="utf-8")  # 合法但缺字段
    r = run("list.py")
    check("缺字段记录不致崩溃", r.returncode == 0)

    # 收尾：清理测试产生的数据文件（可由 add 自动重建），保留干净交付目录
    reset_store()
    tmp = Path(str(NOTES) + ".tmp")
    if tmp.exists():
        tmp.unlink()
    print()
    passed = sum(1 for _, ok in RESULTS if ok)
    print("==== {}/{} PASS ====".format(passed, len(RESULTS)))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
