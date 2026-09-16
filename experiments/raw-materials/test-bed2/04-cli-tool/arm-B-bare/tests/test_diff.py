"""diff 层单元测试：Myers opcodes 与 unified hunk 生成。"""

import unittest
from unittest import TestCase

from gitlite.diff import diff_opcodes, unified_diff
from gitlite.diff import _split_lines as split_lines


def verify_opcodes(case, a, b):
    """性质校验: opcode 衔接无缝隙、equal 段内容一致、坐标覆盖完整。"""
    ops = diff_opcodes(a, b)
    last_i = last_j = 0
    for tag, i1, i2, j1, j2 in ops:
        case.assertEqual((i1, j1), (last_i, last_j), f"gap before {tag} opcode")
        if tag == "equal":
            case.assertEqual(a[i1:i2], b[j1:j2])
        elif tag == "delete":
            case.assertEqual(j1, j2)
        elif tag == "insert":
            case.assertEqual(i1, i2)
        else:
            case.fail(f"unexpected tag {tag}")
        last_i, last_j = i2, j2
    case.assertEqual((last_i, last_j), (len(a), len(b)))
    return ops


class SplitLinesTest(TestCase):
    def test_basic(self):
        self.assertEqual(split_lines("a\nb\n"), ["a\n", "b\n"])
        self.assertEqual(split_lines("a\nb"), ["a\n", "b"])
        self.assertEqual(split_lines("\n"), ["\n"])
        self.assertEqual(split_lines(""), [])


class OpcodesTest(TestCase):
    def test_identical(self):
        ops = diff_opcodes([1, 2, 3], [1, 2, 3])
        self.assertEqual(ops, [("equal", 0, 3, 0, 3)])

    def test_empty_to_content(self):
        ops = diff_opcodes([], ["x", "y"])
        self.assertEqual(ops, [("insert", 0, 0, 0, 2)])

    def test_content_to_empty(self):
        ops = diff_opcodes(["x", "y"], [])
        self.assertEqual(ops, [("delete", 0, 2, 0, 0)])

    def test_middle_change(self):
        a = ["l1\n", "l2\n", "l3\n"]
        b = ["l1\n", "L2\n", "l3\n"]
        ops = diff_opcodes(a, b)
        self.assertEqual(ops[0], ("equal", 0, 1, 0, 1))
        self.assertEqual(ops[-1], ("equal", 2, 3, 2, 3))

    def test_property_reconstruct(self):
        # 用重建式性质校验覆盖多种形状
        cases = [
            ([1, 2, 3], [1, 2, 3, 4]),
            ([1, 2, 3], [1, 3]),
            ([1, 2, 3, 4, 5], [5, 1, 2, 3, 4]),
            ([1, 2, 3], [3, 2, 1]),
            ([], [1, 2]),
            ([1, 2], []),
            ([1] * 5, [2] * 5),
            (list(range(20)), list(range(10)) + [99] + list(range(10, 20))),
        ]
        for a, b in cases:
            verify_opcodes(self, a, b)

    def test_long_common_prefix_trim(self):
        a = list(range(100)) + ["X"]
        b = list(range(100)) + ["Y"]
        ops = diff_opcodes(a, b)
        verify_opcodes(self, a, b)
        # 前后缀裁剪后核心只应有 1 delete + 1 insert
        self.assertEqual(len(ops), 3)

    def test_append_merge_same_tag(self):
        # 相邻同类 opcode 必须被合并（每个 tag 只出现一次连续段）
        a = ["a\n", "b\n", "c\n"]
        b = ["a\n"]
        ops = diff_opcodes(a, b)
        tags = [t for t, *_ in ops]
        self.assertEqual(tags, ["equal", "delete"])


class UnifiedDiffTest(TestCase):
    def test_no_diff_returns_empty(self):
        self.assertEqual(unified_diff(["a\n"], ["a\n"], "a", "b"), [])

    def test_header_lines(self):
        out = unified_diff(["a\n", "b\n"], ["a\n", "B\n"], "a/f", "b/f")
        self.assertEqual(out[0], "--- a/f")
        self.assertEqual(out[1], "+++ b/f")
        self.assertIn("@@ -1,2 +1,2 @@", out)
        self.assertIn("-b\n".strip(), out)
        self.assertIn("+B", out)
        self.assertIn(" a", out)

    def test_single_line_range_omits_count(self):
        out = unified_diff(["x\n"], ["y\n"], "a", "b")
        self.assertIn("@@ -1 +1 @@", out)

    def test_new_file_zero_start(self):
        out = unified_diff([], ["n1\n", "n2\n"], "/dev/null", "b/new")
        self.assertIn("@@ -0,0 +1,2 @@", out)

    def test_deleted_file(self):
        out = unified_diff(["d1\n", "d2\n"], [], "a/old", "/dev/null")
        self.assertIn("@@ -1,2 +0,0 @@", out)
        self.assertIn("-d1", out)
        self.assertIn("-d2", out)

    def test_context_lines(self):
        a = [f"l{i}\n" for i in range(1, 11)]
        b = list(a)
        b[4] = "CHANGED\n"
        out = unified_diff(a, b, "a", "b", context=2)
        # hunk 头应从第 3 行开始（4-2），到第 7 行结束
        self.assertIn("@@ -3,5 +3,5 @@", out)

    def test_no_trailing_newline_marker(self):
        out = unified_diff(["abc"], ["xyz"], "a", "b")
        self.assertIn("\\ No newline at end of file", out)

    def test_two_hunks_far_apart(self):
        a = [f"l{i}\n" for i in range(1, 21)]
        b = list(a)
        b[0] = "A\n"
        b[19] = "B\n"
        out = unified_diff(a, b, "a", "b", context=1)
        hunks = [l for l in out if l.startswith("@@")]
        self.assertEqual(len(hunks), 2)


if __name__ == "__main__":
    unittest.main()
