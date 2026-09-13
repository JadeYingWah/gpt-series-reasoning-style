#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_mutation.py —— 变异杀伤实验：证明 verify.py 真的有鉴别力。

做法（原产物只读，变异体是副本）：
    1. 先跑一遍未改动的 todo.py（对照组 m00），必须全绿；
    2. 对每个变异体：把 todo.py 复制到系统临时目录，替换一处源码（模拟一种真实缺陷），
       再跑同一套 verify.py 用例；只要有用例变红 = 该变异体被“杀死”；
    3. 报告每个变异体的生死 + 总杀伤率。

为什么必须有这一步：45/45 全绿只说明「被测实现没问题」，不说明「验证有效」。
只有注入缺陷后能变红，这套 45/45 才构成证据（对应 skill 的 F6 反例：
14/14 全过却分不出有缺陷版与已修正版）。

用法：
    python run_mutation.py
退出码：0 = 对照组全绿且所有变异体被杀死；1 = 有变异体存活（说明验证有盲区）。

补丁替换要求 old 片段在源码中**恰好出现 1 次**；出现 0 次或多次记为 PATCH-FAILED
并计入「未被杀死」，绝不允许静默跳过（零命中通则）。
"""

import io
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import verify  # noqa: E402

SOURCE = os.path.join(HERE, "todo.py")

# (编号, 模拟的缺陷描述, 原文片段, 替换后的片段)
MUTANTS = [
    ("m01", "取消空标题校验（允许 add \"\"）",
     '    if not title:\n        error(\'标题不能为空。用法：todo.py add "标题"\')',
     '    if False:\n        error(\'标题不能为空。用法：todo.py add "标题"\')'),

    ("m02", "只判断长度不 strip（放过纯空白标题）",
     '    title = " ".join(args).strip()',
     '    title = " ".join(args)'),

    ("m03", "done 不写状态（标记无效）",
     '    item["done"] = True',
     '    item["done"] = item["done"]'),

    ("m04", "id 不自增（所有条目 id 都是 1）",
     '    db["next_id"] += 1',
     '    db["next_id"] = db["next_id"]'),

    ("m05", "list 默认不过滤已完成项",
     'items = db["todos"] if show_all else [t for t in db["todos"] if not t["done"]]',
     'items = db["todos"] if show_all else [t for t in db["todos"]]'),

    ("m06", "损坏 JSON 不再兜底（直接抛异常）",
     "    except (ValueError, UnicodeDecodeError) as exc:\n",
     "    except (ValueError, UnicodeDecodeError) as exc:\n        raise\n"),

    ("m07", "rm 不存在的 id 静默返回成功",
     '        error("未找到 id 为 %d 的待办，未做任何删除。" % item_id)\n        return EXIT_FAIL',
     '        return EXIT_OK'),

    ("m08", "完成/未完成标记互换（对称盲检测）",
     '"[✓]" if item["done"] else "[ ]",',
     '"[ ]" if item["done"] else "[✓]",'),

    ("m09", "对齐宽度退化为 len()（中文算 1 列）",
     '        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1',
     '        width += 1'),

    ("m10", "标题换行不再转义（表格被拆行）",
     '        if ch == "\\n":\n            out.append("\\\\n")',
     '        if False:\n            out.append("\\\\n")'),

    ("m11", "标题截断到 20 字符（超长标题丢数据）",
     '    title = " ".join(args).strip()',
     '    title = " ".join(args).strip()[:20]'),

    ("m12", "时间列输出原始 ISO 串而非可读格式",
     '        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")',
     '        return value'),

    ("m13", "done 后跳过落盘",
     '    item["done"] = True\n    try:',
     '    item["done"] = True\n    return EXIT_OK\n    try:'),

    ("m14", "列表不再截断超长标题（显示被撑爆）",
     "            title = clip_display(title, MAX_TITLE_WIDTH)",
     "            title = title"),

    ("m15", "--full 参数被忽略",
     "    render_table(items, full=full)",
     "    render_table(items, full=False)"),
]


def build_mutant(source_text, old, new, workdir, name):
    count = source_text.count(old)
    if count != 1:
        return None, count
    path = os.path.join(workdir, name, "todo.py")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(source_text.replace(old, new))
    return path, 1


def main():
    if not os.path.isfile(SOURCE):
        sys.stderr.write("找不到源文件：%s\n" % SOURCE)
        return 1

    with io.open(SOURCE, "r", encoding="utf-8") as handle:
        source_text = handle.read()

    workdir = tempfile.mkdtemp(prefix="todo-mutation-")
    rows = []
    try:
        print("对照组 m00（未改动副本）...")
        control_results = verify.run_all(SOURCE)
        control_failed = sum(1 for _, failures in control_results if failures)
        print("  对照组失败用例数：%d / %d" % (control_failed, len(control_results)))

        for name, desc, old, new in MUTANTS:
            path, count = build_mutant(source_text, old, new, workdir, name)
            if path is None:
                rows.append((name, desc, "PATCH-FAILED(old 出现 %d 次)" % count, None))
                print("  %-4s %-34s -> PATCH-FAILED（old 命中 %d 次）" % (name, desc[:34], count))
                continue
            results = verify.run_all(path)
            failed_cases = [c for c, failures in results if failures]
            killed = len(failed_cases) > 0
            rows.append((name, desc, "KILLED" if killed else "SURVIVED",
                         [c["id"] for c in failed_cases]))
            print("  %-4s %-34s -> %-8s 变红用例：%s"
                  % (name, desc[:34], "KILLED" if killed else "SURVIVED",
                     ",".join(c["id"] for c in failed_cases) or "（无）"))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    killed = sum(1 for row in rows if row[2] == "KILLED")
    total = len(rows)
    rate = 100.0 * killed / total if total else 0.0
    print("-" * 72)
    print("变异体 %d 个，杀死 %d 个，杀伤率 %.1f%%" % (total, killed, rate))
    print("对照组 m00：%s" % ("全绿（GREEN）" if control_failed == 0 else "有 %d 条失败（异常）" % control_failed))

    os.makedirs(os.path.join(HERE, "evidence"), exist_ok=True)
    report = os.path.join(HERE, "evidence", "mutation-results.txt")
    with io.open(report, "w", encoding="utf-8") as handle:
        handle.write("变异杀伤实验结果（run_mutation.py 生成）\n")
        handle.write("源文件：%s\n" % SOURCE)
        handle.write("对照组 m00 失败用例数：%d / %d\n" % (control_failed, len(control_results)))
        handle.write("-" * 72 + "\n")
        for name, desc, status, cases in rows:
            handle.write("%-5s %-40s %-14s %s\n" % (name, desc, status, ",".join(cases or []) or "-"))
        handle.write("-" * 72 + "\n")
        handle.write("杀伤率：%d/%d = %.1f%%\n" % (killed, total, rate))
    print("结果已写入：%s" % report)

    return 0 if (killed == total and control_failed == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
