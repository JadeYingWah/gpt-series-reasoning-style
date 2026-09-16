# -*- coding: utf-8 -*-
"""branch / checkout 测试：创建列表删除、切换、脏区拒绝、隔离、空目录清理。"""
from tests.helpers import TempRepoTestCase, run_cli, run_cli_expect


class BranchTest(TempRepoTestCase):
    def _seed(self):
        self.write("a.txt", "A")
        run_cli_expect("add", "a.txt")
        run_cli_expect("commit", "-m", "seed")

    def test_list_shows_main_with_star(self):
        out = run_cli_expect("branch")
        self.assertEqual(out.strip(), "* main")

    def test_list_before_first_commit(self):
        # 新 init 仓库无提交也应列出 main
        import tempfile, os
        from tests.helpers import run_cli as rc

        with tempfile.TemporaryDirectory(prefix="glit-fresh-") as d:
            rc("init", cwd=d)
            out = rc("branch", cwd=d)[1]
            self.assertEqual(out.strip(), "* main")

    def test_create_and_list(self):
        self._seed()
        run_cli_expect("branch", "dev")
        out = run_cli_expect("branch")
        # 字典序：dev < main，当前分支带 * 标记（与 git 行为一致）
        # 注意用 rstrip 而非 strip：strip 会吞掉首行前导空格
        self.assertEqual(out.rstrip("\n").splitlines(), ["  dev", "* main"])

    def test_create_duplicate_rejected(self):
        self._seed()
        run_cli_expect("branch", "dev")
        code, _, err = run_cli("branch", "dev")
        self.assertEqual(code, 1)
        self.assertIn("already exists", err)

    def test_create_before_first_commit_rejected(self):
        code, _, err = run_cli("branch", "dev")
        self.assertEqual(code, 1)
        self.assertIn("no commits yet", err)

    def test_create_invalid_name_rejected(self):
        self._seed()
        for bad in ("a..b", "x.lock", ".h", "a//b"):
            code, _, err = run_cli("branch", bad)
            self.assertEqual(code, 1, bad)
            self.assertIn("invalid branch name", err)

    def test_delete_branch(self):
        self._seed()
        run_cli_expect("branch", "dev")
        out = run_cli_expect("branch", "-d", "dev")
        self.assertIn("Deleted branch dev", out)
        self.assertNotIn("dev", run_cli_expect("branch"))

    def test_delete_current_branch_rejected(self):
        self._seed()
        code, _, err = run_cli("branch", "-d", "main")
        self.assertEqual(code, 1)
        self.assertIn("cannot delete current branch", err)

    def test_delete_missing_branch_rejected(self):
        self._seed()
        code, _, err = run_cli("branch", "-d", "ghost")
        self.assertEqual(code, 1)
        self.assertIn("does not exist", err)


class CheckoutTest(TempRepoTestCase):
    def _seed(self):
        self.write("a.txt", "A")
        run_cli_expect("add", "a.txt")
        run_cli_expect("commit", "-m", "seed")

    def test_checkout_missing_branch_rejected(self):
        self._seed()
        code, _, err = run_cli("checkout", "ghost")
        self.assertEqual(code, 1)
        self.assertIn("does not exist", err)

    def test_checkout_same_branch_message(self):
        self._seed()
        out = run_cli_expect("checkout", "main")
        self.assertIn("Already on 'main'", out)

    def test_switch_updates_workdir_and_index(self):
        self._seed()
        run_cli_expect("branch", "dev")
        run_cli_expect("checkout", "dev")
        self.write("a.txt", "A")  # 未改动
        self.write("dev-only.txt", "D")
        run_cli_expect("add", "dev-only.txt")
        run_cli_expect("commit", "-m", "dev file")
        run_cli_expect("checkout", "main")
        self.assertFalse(self.exists("dev-only.txt"), "main 上不应有 dev-only.txt")
        code, out, _ = run_cli("diff")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        run_cli_expect("checkout", "dev")
        self.assertTrue(self.exists("dev-only.txt"))
        self.assertEqual(self.read("dev-only.txt"), b"D")

    def test_dirty_workdir_rejected(self):
        self._seed()
        run_cli_expect("branch", "dev")
        self.write("a.txt", "MODIFIED")  # 未提交修改
        code, _, err = run_cli("checkout", "dev")
        self.assertEqual(code, 1)
        self.assertIn("would be overwritten", err)
        # 状态未变：当前分支仍是 main（* 标记），修改仍在工作区
        out = run_cli_expect("branch")
        self.assertIn("* main", out)
        self.assertEqual(self.read("a.txt"), b"MODIFIED")

    def test_deleted_tracked_file_blocks_checkout(self):
        self._seed()
        run_cli_expect("branch", "dev")
        (self.tmp / "a.txt").unlink()
        code, _, err = run_cli("checkout", "dev")
        self.assertEqual(code, 1)
        self.assertIn("would be overwritten", err)

    def test_untracked_conflict_rejected(self):
        self._seed()
        run_cli_expect("branch", "dev")
        run_cli_expect("checkout", "dev")
        self.write("new.txt", "dev version")
        run_cli_expect("add", "new.txt")
        run_cli_expect("commit", "-m", "add new.txt on dev")
        run_cli_expect("checkout", "main")
        self.write("new.txt", "untracked on main")  # main 上是未跟踪文件
        code, _, err = run_cli("checkout", "dev")
        self.assertEqual(code, 1)
        self.assertIn("untracked working tree files would be overwritten", err)

    def test_branch_isolation_commits(self):
        self._seed()
        run_cli_expect("branch", "dev")
        run_cli_expect("checkout", "dev")
        self.write("b.txt", "B")
        run_cli_expect("add", "b.txt")
        run_cli_expect("commit", "-m", "dev commit")
        run_cli_expect("checkout", "main")
        # main 的 log 不应包含 dev commit
        out = run_cli_expect("log", "--oneline")
        self.assertNotIn("dev commit", out)
        self.assertIn("seed", out)
        run_cli_expect("checkout", "dev")
        out = run_cli_expect("log", "--oneline")
        self.assertIn("dev commit", out)

    def test_empty_dir_cleanup_after_switch(self):
        self._seed()
        self.write("sub/deep/x.txt", "X")
        run_cli_expect("add", ".")
        run_cli_expect("commit", "-m", "subtree")
        run_cli_expect("branch", "minimal")  # minimal 也基于同一提交，含 sub/
        # 在 main 上删除 sub 并提交
        (self.tmp / "sub" / "deep" / "x.txt").unlink()
        run_cli_expect("add", "sub/deep/x.txt")
        run_cli_expect("commit", "-m", "remove sub")
        self.assertFalse(self.exists("sub/deep/x.txt"))
        run_cli_expect("checkout", "minimal")
        self.assertTrue(self.exists("sub/deep/x.txt"))
        run_cli_expect("checkout", "main")
        self.assertFalse(self.exists("sub/deep/x.txt"))
        self.assertFalse((self.tmp / "sub" / "deep").exists(), "空目录应被清理")

    def test_checkout_preserves_history(self):
        self._seed()
        run_cli_expect("branch", "dev")
        run_cli_expect("checkout", "dev")
        # dev 上的历史包含 seed
        out = run_cli_expect("log", "--oneline")
        self.assertIn("seed", out)


if __name__ == "__main__":
    unittest.main()
