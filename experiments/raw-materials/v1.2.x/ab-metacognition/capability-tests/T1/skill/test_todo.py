"""todo.py 验证脚本 — 覆盖正常值 / 边界值 / 异常值 / 持久化 / 零依赖。"""
import json
import os
import subprocess
import sys

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.py")
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")

PASS = 0
FAIL = 0


def run(*args, expect_exit=0):
    """运行 todo.py，返回 (stdout, stderr, returncode)。"""
    r = subprocess.run(
        [sys.executable, SCRIPT] + list(args),
        capture_output=True, text=True, encoding="utf-8"
    )
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


def cleanup():
    for f in (DATA, DATA + ".tmp"):
        if os.path.exists(f):
            os.remove(f)


def main():
    print("=" * 60)
    print("todo.py 验证 — 输入域分段覆盖")
    print("=" * 60)

    # ── 分段 0：零依赖检查 ──
    print("\n[分段0] 零依赖检查")
    with open(SCRIPT, "r", encoding="utf-8") as f:
        src = f.read()
    imports = [l for l in src.splitlines() if l.startswith("import ") or l.startswith("from ")]
    stdlib = {"argparse", "json", "os", "sys", "datetime"}
    third_party = [imp for imp in imports if imp.split()[1].split(".")[0] not in stdlib]
    check("仅使用标准库", len(third_party) == 0, f"第三方导入: {third_party}")

    # ── 分段 1：正常值 ──
    print("\n[分段1] 正常值 — 完整 CRUD 流程")
    cleanup()
    out, _, rc = run("add", "买牛奶")
    check("add 返回 0", rc == 0, out)
    check("add 输出含 ID", "#1" in out, out)

    out, _, rc = run("add", "写代码")
    check("第二条 add 返回 0", rc == 0)
    check("第二条 ID 为 2", "#2" in out, out)

    out, _, rc = run("list")
    check("list 返回 0", rc == 0)
    check("list 包含两条", "#1" in out and "#2" in out, out)
    check("list 均为未完成", "[ ]" in out, out)

    out, _, rc = run("done", "1")
    check("done 返回 0", rc == 0)
    check("done 输出确认", "已完成" in out, out)

    out, _, rc = run("list")
    check("done 后 list 显示 [x]", "[x]" in out and "#1" in out, out)
    check("done 后另一条仍 [ ]", "[ ] #2" in out, out)

    out, _, rc = run("delete", "2")
    check("delete 返回 0", rc == 0)

    out, _, rc = run("list")
    check("delete 后只剩一条", "#2" not in out, out)
    check("delete 后 #1 仍在", "#1" in out, out)

    # ── 分段 2：边界值 ──
    print("\n[分段2] 边界值")
    cleanup()

    out, _, rc = run("list")
    check("空列表 list 不崩溃", rc == 0, out)
    check("空列表提示", "暂无" in out or "暂无待办" in out, out)

    out, err, rc = run("done", "999")
    check("done 不存在 ID 返回非 0", rc != 0, f"rc={rc}")
    check("done 不存在 ID 有错误提示", "未找到" in err, err)

    out, err, rc = run("delete", "999")
    check("delete 不存在 ID 返回非 0", rc != 0, f"rc={rc}")
    check("delete 不存在 ID 有错误提示", "未找到" in err, err)

    # 重复 done（幂等性）
    run("add", "测试幂等")
    run("done", "1")
    out, _, rc = run("done", "1")
    check("重复 done 不报错", rc == 0, out)
    check("重复 done 提示已完成", "已经" in out or "已完成" in out, out)

    # ID 自增不回收
    run("add", "A")
    run("add", "B")
    run("delete", "2")
    out, _, _ = run("add", "C")
    check("删除后新 ID 不回收（继续递增）", "#4" in out, out)

    # ── 分段 3：异常值 ──
    print("\n[分段3] 异常值")
    cleanup()

    out, err, rc = run("done", "abc")
    check("done 非数字参数报错", rc != 0, f"rc={rc}")

    out, err, rc = run("delete", "-1")
    check("delete 负 ID 返回非 0", rc != 0, f"rc={rc}")

    out, err, rc = run("add", "")
    check("add 空内容返回非 0", rc != 0, f"rc={rc}")

    out, err, rc = run("nonexistent_cmd")
    check("未知子命令报错", rc != 0, f"rc={rc}")

    # ── 分段 4：持久化 ──
    print("\n[分段4] JSON 持久化")
    cleanup()
    run("add", "持久化测试")
    check("todos.json 文件已创建", os.path.exists(DATA))

    with open(DATA, "r", encoding="utf-8") as f:
        data = json.load(f)
    check("JSON 可解析且为列表", isinstance(data, list))
    check("JSON 包含正确字段", all(k in data[0] for k in ("id", "text", "done", "created_at")))
    check("JSON 内容正确", data[0]["text"] == "持久化测试")
    check("JSON done 初始为 False", data[0]["done"] is False)

    # 损坏文件容错
    with open(DATA, "w", encoding="utf-8") as f:
        f.write("{corrupted json!!!")
    out, _, rc = run("list")
    check("损坏 JSON 不崩溃（容错为空列表）", rc == 0, out)

    # ── 分段 5：中文 / 特殊字符 ──
    print("\n[分段5] 中文与特殊字符")
    cleanup()
    run("add", "中文任务 测试！@#￥%")
    out, _, _ = run("list")
    check("中文内容正确显示", "中文任务" in out, out)

    run('add', 'quote"test')
    out, _, _ = run("list")
    check("含引号内容不崩溃", "quote" in out, out)

    # ── 汇总 ──
    cleanup()
    print("\n" + "=" * 60)
    total = PASS + FAIL
    print(f"结果: {PASS}/{total} PASS, {FAIL}/{total} FAIL")
    print("=" * 60)
    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    main()
