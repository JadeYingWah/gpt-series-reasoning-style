"""差异计算层 —— 手写 Myers O(ND) diff 与 unified hunk 生成。

不使用标准库 difflib：diff 是本工具的核心能力，由自己实现并测试。

  diff_opcodes(a, b)
      返回 a -> b 的最短编辑脚本，opcode 形如 (tag, i1, i2, j1, j2)，
      tag ∈ {"equal", "delete", "insert"}（replace 由相邻 delete+insert 表达）。

  unified_diff(a_lines, b_lines, from_label, to_label)
      生成 git 风格的 unified diff（---/+++ 头 + @@ hunk 头 + 行内容），
      返回不含换行符的行列表；两序列完全相同时返回空列表。
"""

from __future__ import annotations

from typing import Any, List, Sequence, Tuple

Opcode = Tuple[str, int, int, int, int]


class DiffError(Exception):
    """diff 计算内部错误。"""


# ----------------------------------------------------------------------
# Myers 最短编辑脚本
# ----------------------------------------------------------------------

def diff_opcodes(a: Sequence[Any], b: Sequence[Any]) -> List[Opcode]:
    """计算 a -> b 的编辑脚本。先裁剪公共前后缀，再对核心部分跑 Myers。"""
    n, m = len(a), len(b)
    pre = 0
    while pre < n and pre < m and a[pre] == b[pre]:
        pre += 1
    suf = 0
    while suf < n - pre and suf < m - pre and a[n - 1 - suf] == b[m - 1 - suf]:
        suf += 1

    ops: List[Opcode] = []
    if pre:
        ops.append(("equal", 0, pre, 0, pre))
    ops.extend(_myers_core(a[pre:n - suf], b[pre:m - suf], pre, pre))
    if suf:
        ops.append(("equal", n - suf, n, m - suf, m))
    return ops


def _myers_core(a: Sequence[Any], b: Sequence[Any], off_i: int, off_j: int) -> List[Opcode]:
    """对裁剪后的核心序列运行 Myers，坐标平移 (off_i, off_j) 回原坐标系。"""
    n, m = len(a), len(b)
    if n == 0 and m == 0:
        return []
    if n == 0:
        return [("insert", off_i, off_i, off_j, off_j + m)]
    if m == 0:
        return [("delete", off_i, off_i + n, off_j, off_j)]

    trace, d_final = _shortest_edit(a, b)
    steps = _backtrack(trace, d_final, n, m)
    # steps: 完整正向点列 [P0=(0,0), P1, ..., PD'=(n,m)]，
    # 相邻两点之差恰为一步（对角=equal / 右移=delete / 下移=insert）。

    ops: List[Opcode] = []
    i = j = 0
    for x, y in steps[1:]:
        if x == i + 1 and y == j:
            _append(ops, "delete", off_i + i, off_i + i + 1, off_j + j, off_j + j)
            i += 1
        elif x == i and y == j + 1:
            _append(ops, "insert", off_i + i, off_i + i, off_j + j, off_j + j + 1)
            j += 1
        elif x == i + 1 and y == j + 1:
            _append(ops, "equal", off_i + i, off_i + i + 1, off_j + j, off_j + j + 1)
            i += 1
            j += 1
        else:
            raise DiffError(f"invalid myers step: ({i},{j}) -> ({x},{y})")
    if (i, j) != (n, m):
        raise DiffError(f"myers path incomplete: ended at ({i},{j}), expected ({n},{m})")
    return ops


def _shortest_edit(a: Sequence[Any], b: Sequence[Any]):
    """Myers 前向阶段：返回 (trace, d)。trace[d] 是第 d 轮开始时的 v 快照。"""
    n, m = len(a), len(b)
    v = {1: 0}
    trace: List[dict] = []
    for d in range(n + m + 1):
        trace.append(dict(v))
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v[k - 1] < v[k + 1]):
                x = v[k + 1]
            else:
                x = v[k - 1] + 1
            y = x - k
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1
            v[k] = x
            if x >= n and y >= m:
                return trace, d
    raise DiffError("myers search exhausted without reaching the end")


def _backtrack(trace: List[dict], d_final: int, n: int, m: int) -> List[Tuple[int, int]]:
    """Myers 回溯：返回完整正向点列 [P0=(0,0), P1, ..., (n,m)]。

    点列中相邻两点之差恰为一步：
      (+1,+1) 对角 equal；(+1,0) delete；(0,+1) insert。
    生成顺序为逆序（从 (n,m) 回溯到 (0,0)），最后统一反转。
    """
    steps: List[Tuple[int, int]] = [(n, m)]
    x, y = n, m
    for d in range(d_final, 0, -1):
        v = trace[d]
        k = x - y
        if k == -d or (k != d and v[k - 1] < v[k + 1]):
            prev_k = k + 1
        else:
            prev_k = k - 1
        prev_x = v[prev_k]
        prev_y = prev_x - prev_k
        # 该层非对角步的终点 q：insert 时 x 不变 y+1；delete 时 x+1 y 不变
        if prev_k == k + 1:
            q = (prev_x, prev_y + 1)
        else:
            q = (prev_x + 1, prev_y)
        # 回退该层末尾的对角蛇形（到 q 为止，含 q）
        while (x, y) != q:
            x -= 1
            y -= 1
            steps.append((x, y))
        # 落到该层非对角步的起点
        steps.append((prev_x, prev_y))
        x, y = prev_x, prev_y
    # d=0 层：剩余前缀是纯对角蛇形，回退到 (0,0)
    while (x, y) != (0, 0):
        x -= 1
        y -= 1
        steps.append((x, y))
    if steps[-1] != (0, 0):
        steps.append((0, 0))
    steps.reverse()
    return steps


def _append(ops: List[Opcode], tag: str, i1: int, i2: int, j1: int, j2: int) -> None:
    """追加 opcode，相邻同 tag 段合并。"""
    if ops and ops[-1][0] == tag:
        t, pi1, _pi2, pj1, _pj2 = ops[-1]
        ops[-1] = (t, pi1, i2, pj1, j2)
    else:
        ops.append((tag, i1, i2, j1, j2))


# ----------------------------------------------------------------------
# unified diff 生成
# ----------------------------------------------------------------------

def _split_lines(text: str) -> List[str]:
    """按 \\n 拆分并保留行尾（只认 \\n，不认 unicode 换行，与 git 行为一致）。"""
    if not text:
        return []
    parts = text.split("\n")
    out = [p + "\n" for p in parts[:-1]]
    if parts[-1] != "":
        out.append(parts[-1])
    return out


def unified_diff(
    a_lines: Sequence[str],
    b_lines: Sequence[str],
    from_label: str,
    to_label: str,
    context: int = 3,
) -> List[str]:
    """生成 unified diff 行列表（不含尾部换行符）。完全相同时返回 []。"""
    ops = diff_opcodes(a_lines, b_lines)
    if len(ops) == 1 and ops[0][0] == "equal":
        return []

    # 编辑脚本：每项 (tag, a_no, b_no, a_before, b_before, text)
    #   a_no/b_no     该行在 a/b 中的 1-based 行号（无对应则为 None）
    #   a_before/b_before 处理该行之前 a/b 已消费的行数（用于空侧行号推导）
    script: List[Tuple[str, Any, Any, int, int, str]] = []
    a_no = b_no = 0
    for tag, i1, i2, j1, j2 in ops:
        if tag == "equal":
            for k in range(i2 - i1):
                a_no += 1
                b_no += 1
                script.append((" ", a_no, b_no, a_no - 1, b_no - 1, a_lines[i1 + k]))
        elif tag == "delete":
            for k in range(i2 - i1):
                a_no += 1
                script.append(("-", a_no, None, a_no - 1, b_no, a_lines[i1 + k]))
        elif tag == "insert":
            for k in range(j2 - j1):
                b_no += 1
                script.append(("+", None, b_no, a_no, b_no - 1, b_lines[j1 + k]))
        else:  # pragma: no cover - diff_opcodes 只产生三种 tag
            raise DiffError(f"unexpected opcode tag: {tag}")

    # 变更行向外扩 context 行 -> 合并重叠窗口 -> hunk
    windows: List[List[int]] = []
    for idx, item in enumerate(script):
        if item[0] == " ":
            continue
        lo = max(0, idx - context)
        hi = min(len(script), idx + context + 1)
        if windows and lo <= windows[-1][1]:
            windows[-1][1] = max(windows[-1][1], hi)
        else:
            windows.append([lo, hi])

    lines_out = [f"--- {from_label}", f"+++ {to_label}"]
    for lo, hi in windows:
        seg = script[lo:hi]
        a_nos = [item[1] for item in seg if item[1] is not None]
        b_nos = [item[2] for item in seg if item[2] is not None]
        a_count = len(a_nos)
        b_count = len(b_nos)
        a_start = a_nos[0] if a_nos else seg[0][3]
        b_start = b_nos[0] if b_nos else seg[0][4]
        lines_out.append(
            f"@@ -{_fmt_range(a_start, a_count)} +{_fmt_range(b_start, b_count)} @@"
        )
        for tag, _a, _b, _ab, _bb, text in seg:
            body = text[:-1] if text.endswith("\n") else text
            lines_out.append(tag + body)
            if not text.endswith("\n"):
                lines_out.append("\\ No newline at end of file")
    return lines_out


def _fmt_range(start: int, count: int) -> str:
    """unified hunk 范围: count==1 省略 ",1"；count==0 时行号为间隙位置。"""
    if count == 1:
        return str(start)
    return f"{start},{count}"
