# -*- coding: utf-8 -*-
"""diff 测试：工作区 vs index、index vs HEAD、新增/删除/二进制/退出码。"""
from tests.helpers import TempRepoTestCase, run_cli, run_cli_expect


class DiffWorkdirTest(TempRepoTestCase):
    def _seed(self):
        self.write("a.txt", "line1\nline2\n")
        run_cli_expect("add", "a.txt")
        run_cli_expect("commit", "-m", "seed")

    def test_no_diff_exit_0_empty_output(self):
        self._seed()
        code, out, _ = run_cli("diff")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_modified_file_shows_unified_diff_exit_1(self):
        self._seed()
        self.write("a.txt", "line1\nCHANGED\n")
        code, out, _ = run_cli("diff")
        self.assertEqual(code, 1)
        self.assertIn("--- a/a.txt", out)
        self.assertIn("+++ b/a.txt", out)
        self.assertIn("-line2", out)
        self.assertIn("+CHANGED", out)

    def test_staged_change_not_shown_by_default(self):
        self._seed()
        self.write("a.txt", "changed but not staged\n")
        run_cli_expect("add", "a.txt")
        code, out, _ = run_cli("diff")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_untracked_file_not_shown(self):
        self._seed()
        self.write("new.txt", "untracked\n")
        code, out, _ = run_cli("diff")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_deleted_tracked_file_shows_deletion(self):
        self._seed()
        (self.tmp / "a.txt").unlink()
        code, out, _ = run_cli("diff")
        self.assertEqual(code, 1)
        self.assertIn("--- a/a.txt", out)
        self.assertIn("-line1", out)
        self.assertIn("-line2", out)

    def test_binary_file_diff_placeholder(self):
        self.write("bin.dat", b"\x00\x01\x02abc")
        run_cli_expect("add", "bin.dat")
        self.write("bin.dat", b"\x00\x01\x02xyz")
        code, out, _ = run_cli("diff")
        self.assertEqual(code, 1)
        self.assertIn("Binary files a/bin.dat and b/bin.dat differ", out)

    def test_no_trailing_newline_marker(self):
        self.write("a.txt", "no newline at end")
        run_cli_expect("add", "a.txt")
        self.write("a.txt", "no newline at end!")
        code, out, _ = run_cli("diff")
        self.assertEqual(code, 1)
        self.assertIn("\\ No newline at end of file", out)


class DiffStagedTest(TempRepoTestCase):
    def _seed(self):
        self.write("a.txt", "v1\n")
        run_cli_expect("add", "a.txt")
        run_cli_expect("commit", "-m", "seed")

    def test_staged_new_file_vs_head(self):
        self._seed()
        self.write("new.txt", "brand new\n")
        run_cli_expect("add", "new.txt")
        code, out, _ = run_cli("diff", "--staged")
        self.assertEqual(code, 1)
        self.assertIn("+++ b/new.txt", out)
        self.assertIn("+brand new", out)
        # 默认（工作区 vs index）应为空
        code2, out2, _ = run_cli("diff")
        self.assertEqual(code2, 0)
        self.assertEqual(out2, "")

    def test_staged_deletion_vs_head(self):
        self._seed()
        (self.tmp / "a.txt").unlink()
        run_cli_expect("add", "a.txt")
        code, out, _ = run_cli("diff", "--staged")
        self.assertEqual(code, 1)
        self.assertIn("--- a/a.txt", out)
        self.assertIn("-v1", out)

    def test_staged_modify_vs_head(self):
        self._seed()
        self.write("a.txt", "v2\n")
        run_cli_expect("add", "a.txt")
        code, out, _ = run_cli("diff", "--staged")
        self.assertEqual(code, 1)
        self.assertIn("-v1", out)
        self.assertIn("+v2", out)

    def test_no_staged_change_exit_0(self):
        self._seed()
        code, out, _ = run_cli("diff", "--staged")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
