#!/usr/bin/env python3
"""genpass.py 验证脚本（轻量配置·代码类核心验证：语法 + 边界 + 字符域覆盖 + 日志 + 评级 + --no-log）

输入域分段：
- 正常值（默认16 / 中间长度 / 选项任意顺序）
- 边界值（长度 8、64）
- 超界值（7、65、0、-5）
- 异常值（abc、16.5、多余长度参数、未知选项）
- 评级档位（弱：短/单类/双类；中：8位全类/16位单类；强：12+位3类/16位4类）
- --no-log（不追加日志 vs 对照组追加）
"""
import os
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # 不生成 __pycache__

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import genpass

PY = sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
results = []


def check(name, ok, detail=""):
    results.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def run_cli(*args):
    return subprocess.run([PY, str(ROOT / "genpass.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=ENV, cwd=str(ROOT))


def log_lines():
    log = ROOT / "passwords.log"
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def cats_ok(pw):
    return all(any(c in g for c in pw) for g in genpass.GROUPS)


# 1. 语法检查
r = subprocess.run([PY, "-m", "py_compile", str(ROOT / "genpass.py")], capture_output=True, text=True)
check("语法检查 py_compile", r.returncode == 0, r.stderr.strip() or "通过")

# 2. 正常值：默认 16，输出含评级两行
r = run_cli()
lines = r.stdout.strip().splitlines()
pw = lines[0].strip() if lines else ""
check("默认长度 16，退出码 0", r.returncode == 0 and len(pw) == 16 and cats_ok(pw), f"len={len(pw)}")
check("输出含强度评级与依据", len(lines) >= 3 and lines[1].startswith("强度评级：") and lines[2].startswith("评级依据："),
      " | ".join(lines[1:3]))

# 3. 边界值 8 与 64
for n in (8, 64):
    r = run_cli(str(n))
    pw = r.stdout.strip().splitlines()[0]
    check(f"边界长度 {n}", r.returncode == 0 and len(pw) == n and cats_ok(pw), f"len={len(pw)}, 四类字符={'全含' if cats_ok(pw) else '缺失'}")

# 4. 中间长度抽样
for n in (10, 33, 50):
    r = run_cli(str(n))
    pw = r.stdout.strip().splitlines()[0]
    check(f"中间长度 {n}", r.returncode == 0 and len(pw) == n and cats_ok(pw), f"len={len(pw)}")

# 5. 超界与异常输入 → 友好提示、退出码非 0、不写日志
before = len(log_lines())
for bad in ("7", "65", "0", "-5", "abc", "16.5"):
    r = run_cli(bad)
    msg = (r.stdout + r.stderr).strip()
    friendly = ("错误" in msg) and ("8-64" in msg)
    check(f"非法输入 {bad!r} 友好拒绝", r.returncode != 0 and friendly, msg.splitlines()[0][:70] if msg else "(无输出)")
check("非法输入未写日志", len(log_lines()) == before, f"日志行数 {before} -> {len(log_lines())}")

# 6. 新增参数处理：未知选项 / 两个长度 / 选项与长度任意顺序 / --no-log 幂等
r = run_cli("--foo")
msg = (r.stdout + r.stderr).strip()
check("未知选项 --foo 友好拒绝", r.returncode != 0 and "未知选项" in msg, msg.splitlines()[0][:70] if msg else "(无输出)")
r = run_cli("16", "24")
msg = (r.stdout + r.stderr).strip()
check("两个长度参数拒绝", r.returncode != 0 and "最多接受一个长度" in msg, msg.splitlines()[0][:70] if msg else "(无输出)")
for order in (("--no-log", "24"), ("24", "--no-log")):
    r = run_cli(*order)
    pw = r.stdout.strip().splitlines()[0]
    check(f"选项与长度任意顺序 {order}", r.returncode == 0 and len(pw) == 24, f"len={len(pw)}")

# 7. 评级单元测试：三档各有触达用例，依据文本与档位一致
rating_cases = [
    ("abc", "弱"),               # 长度<8 直接弱
    ("abcd1234", "弱"),          # 8位双类：1+1=2 弱
    ("abcdefgh", "弱"),          # 8位单类：1+0=1 弱
    ("Abcd1234", "中"),          # 8位三类：1+2=3 中
    ("Abcd1234!", "中"),         # 9位四类：1+3=4 中
    ("abcdefghijklmnop", "中"),  # 16位单类：3+0=3 中
    ("Abcdefghij12!", "强"),     # 13位四类：2+3=5 强
    ("Abcdefgh12345678!", "强"), # 18位四类：3+3=6 强
]
for pw_in, expect in rating_cases:
    level, score, reason = genpass.rate_password(pw_in)
    check(f"评级 {pw_in!r} → {expect}", level == expect and (0 <= score <= 6) and reason,
          f"实际={level} 得分={score} 依据={reason[:50]}")
# 依据文本含长度与类别信息
level, score, reason = genpass.rate_password("Abcd1234!")
check("评级依据含长度与类别明细", "长度 9" in reason and "字符类别 4/4" in reason and "符号" in reason, reason)

# 8. CLI 评级端到端：生成的默认密码应为强（16位四类=6分），8位生成密码应为中（1+3=4分）
r = run_cli()
lines = r.stdout.strip().splitlines()
check("CLI 默认16位生成密码评级为强", "强度评级：强" in lines[1], lines[1])
r = run_cli("8")
lines = r.stdout.strip().splitlines()
check("CLI 8位生成密码评级为中", "强度评级：中" in lines[1], lines[1])

# 9. --no-log 实测：运行前记录行数 → --no-log 后行数不变；对照组正常运行行数 +1
before = len(log_lines())
r = run_cli("--no-log")
after_nolog = len(log_lines())
check("--no-log 不追加日志", r.returncode == 0 and after_nolog == before,
      f"行数 {before} -> {after_nolog}")
r = run_cli("16")
after_normal = len(log_lines())
check("对照组：正常运行日志 +1", r.returncode == 0 and after_normal == after_nolog + 1,
      f"行数 {after_nolog} -> {after_normal}")

# 10. 日志含时间戳与密码（原功能回归）
lines = log_lines()
pat = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}  \S+$")
check("passwords.log 行格式 = ISO时间戳 + 密码", len(lines) >= 6 and all(pat.match(l) for l in lines), f"共 {len(lines)} 行")

# 11. 批量覆盖：200 次、长度扫描 8-64（单元级，原功能回归）
ok, fail_n = True, None
for i in range(200):
    n = 8 + (i % 57)
    pw = genpass.generate_password(n)
    if len(pw) != n or not cats_ok(pw):
        ok, fail_n = False, n
        break
check("批量 200 次：长度精确 + 四类字符齐备（8-64 全扫）", ok, "全部通过" if ok else f"失败于 n={fail_n}")

# 12. 随机性粗检：同一长度多次输出不重复（原功能回归）
pws = {genpass.generate_password(16) for _ in range(30)}
check("随机性粗检：30 次 16 位输出无重复", len(pws) == 30, f"去重后 {len(pws)} 个")

# 13. 评级函数对生成密码批量单调性粗检：输出评级三档合法
ok = all(genpass.rate_password(genpass.generate_password(16))[0] == "强" for _ in range(20))
check("批量 20 次 16 位生成密码评级均为强", ok, "全部通过" if ok else "存在非强评级")

failed = [n for n, ok in results if not ok]
print(f"\n=== 汇总：{len(results) - len(failed)}/{len(results)} PASS ===")
sys.exit(1 if failed else 0)
