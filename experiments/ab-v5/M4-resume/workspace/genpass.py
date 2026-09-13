#!/usr/bin/env python3
"""genpass.py — 命令行随机密码生成器（第二阶段：+强度评级 / --no-log）

用法：python genpass.py [长度] [--no-log]
- 长度默认 16，范围 8-64，越界或非法输入给友好提示
- 字符集含大小写字母 + 数字 + 符号，且保证每类至少出现 1 个
- 密码打印到终端并输出强度评级（弱/中/强）与评级依据
- 默认明文追加写入 passwords.log（演示用），每行含 ISO 时间戳；--no-log 时不写日志
"""
import secrets
import string
import sys
from datetime import datetime

MIN_LEN, MAX_LEN, DEFAULT_LEN = 8, 64, 16
LOG_FILE = "passwords.log"

LOWER = string.ascii_lowercase
UPPER = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = string.punctuation
GROUPS = (LOWER, UPPER, DIGITS, SYMBOLS)


def generate_password(length: int) -> str:
    """生成指定长度的密码，保证四类字符各至少 1 个。"""
    chars = [secrets.choice(g) for g in GROUPS]
    all_chars = "".join(GROUPS)
    chars += [secrets.choice(all_chars) for _ in range(length - len(chars))]
    # 用 secrets 做 Fisher-Yates 洗牌，避免前 4 位固定来自固定类别
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)


def log_password(password: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp}  {password}\n")


# 强度评级规则（确定性启发式，总分 0-6）：
#   长度分：8-11 → +1；12-15 → +2；≥16 → +3；<8 直接判弱
#   类别分：小写/大写/数字/符号，每含一类 +1（单类 +0，最多 +3）
#   评级：≤2 → 弱；3-4 → 中；≥5 → 强
CATEGORY_NAMES = ((LOWER, "小写"), (UPPER, "大写"), (DIGITS, "数字"), (SYMBOLS, "符号"))


def rate_password(pw: str) -> tuple[str, int, str]:
    """返回 (评级, 得分 0-6, 评级依据)。"""
    cats = [name for group, name in CATEGORY_NAMES if any(c in group for c in pw)]
    if len(pw) < 8:
        return "弱", 0, f"长度 {len(pw)}（<8，直接判弱）"
    length_pts = 1 + (len(pw) >= 12) + (len(pw) >= 16)
    cat_pts = len(cats) - 1
    score = length_pts + cat_pts
    level = "弱" if score <= 2 else ("中" if score <= 4 else "强")
    reason = (
        f"长度 {len(pw)}"
        f"（{'8-11' if length_pts == 1 else '12-15' if length_pts == 2 else '≥16'}，+{length_pts}）；"
        f"字符类别 {len(cats)}/4（+{cat_pts}）：{'/'.join(cats) if cats else '无'}"
    )
    return level, score, reason


def parse_args(args: list) -> tuple[int, bool]:
    """解析位置长度参数与 --no-log 选项，非法时抛 ValueError（消息已友好化）。

    返回 (长度, no_log)。选项与长度顺序不限；--no-log 可重复（幂等）；未知选项报错。
    """
    length = DEFAULT_LEN
    no_log = False
    seen_length = False
    for a in args[1:]:
        if a == "--no-log":
            no_log = True
        elif a.startswith("--"):
            raise ValueError(
                f"错误：未知选项「{a}」。用法：python genpass.py [长度] [--no-log]（默认 {DEFAULT_LEN}，范围 {MIN_LEN}-{MAX_LEN}）"
            )
        else:
            if seen_length:
                raise ValueError(
                    f"错误：最多接受一个长度参数。用法：python genpass.py [长度] [--no-log]（默认 {DEFAULT_LEN}，范围 {MIN_LEN}-{MAX_LEN}）"
                )
            try:
                length = int(a)
            except ValueError:
                raise ValueError(
                    f"错误：长度必须是 {MIN_LEN}-{MAX_LEN} 之间的整数，收到「{a}」。"
                    f"用法：python genpass.py [长度] [--no-log]（默认 {DEFAULT_LEN}，范围 {MIN_LEN}-{MAX_LEN}）"
                )
            seen_length = True
    if not (MIN_LEN <= length <= MAX_LEN):
        raise ValueError(
            f"错误：密码长度必须在 {MIN_LEN}-{MAX_LEN} 之间，收到 {length}。"
            f"用法：python genpass.py [长度] [--no-log]（默认 {DEFAULT_LEN}，范围 {MIN_LEN}-{MAX_LEN}）"
        )
    return length, no_log


def main() -> int:
    try:
        length, no_log = parse_args(sys.argv)
    except ValueError as e:
        print(e)
        return 1
    password = generate_password(length)
    if not no_log:
        log_password(password)
    print(password)
    level, score, reason = rate_password(password)
    print(f"强度评级：{level}（得分 {score}/6）")
    print(f"评级依据：{reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
