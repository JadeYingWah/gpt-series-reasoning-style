"""T2 床4 判分脚本：跑 next_date.py 协议用例，逐例红/绿。"""
import subprocess, sys

CASES = [
    ("2024-02-28", "2024-02-29"),  # 闰年 2 月（主 RED 例）
    ("2000-02-28", "2000-02-29"),  # 400 年规则闰年（第二 RED 例）
    ("2023-02-28", "2023-03-01"),  # 平年 2 月（原版即绿）
    ("2024-12-31", "2025-01-01"),  # 年末进位
    ("2024-04-30", "2024-05-01"),  # 月末进位
]
ok = 0
for inp, want in CASES:
    got = subprocess.run(
        [sys.executable, "next_date.py", inp], capture_output=True, text=True
    ).stdout.strip()
    mark = "GREEN" if got == want else "RED"
    ok += got == want
    print(f"{inp} -> {got} (期望 {want}) [{mark}]")
print(f"{ok}/{len(CASES)}")
