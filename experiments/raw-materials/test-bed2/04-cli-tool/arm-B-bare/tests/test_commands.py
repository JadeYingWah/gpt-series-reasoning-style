"""命令层集成测试：直接调用 commands.cmd_*（不经子进程）。"""

import contextlib
import io
import os
import unittest

from gitlite import commands
from gitlite.objects import COMMIT, parse_commit
from gitlite.repository import RepositoryError

from .helpers import TempRepoTestCase


def run_quiet(fn, *args, **kwargs):
    """执行命令函数并吞掉 stdout，返回 (exit_code, 输出文本)。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn(*args, **kwargs)
    return code, buf.getvalue()


class InitTest(TempRepoTestCase):
    def test_creates_structure(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, ".gitlite")))
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, ".gitlite", "objects")))
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, ".gitlite", "refs", "heads")))
        with open(os.path.join(self.tmp, ".gitlite", "HEAD"), encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), "ref: refs/heads/main")

    def test_idempotent_reinit_keeps_head(self):
        # 提交一次后重新 init，HEAD 不应被重置
        self.w("a.txt", "1\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        run_quiet(commands.cmd_commit, self.repo, "c1")
        head_before = self.repo.read_head()
        run_quiet(commands.cmd_init, self.tmp)
        self.assertEqual(self.repo.read_head(), head_before)


class AddTest(TempRepoTestCase):
    def test_stage_file(self):
        self.w("a.txt", "hello\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        idx = self.repo.load_index()
        self.assertIn("a.txt", idx.entries)
        entry = idx.entries["a.txt"]
        self.assertEqual(entry["mode"], "100644")
        self.assertTrue(self.repo.objects.has(entry["oid"]))

    def test_stage_directory_recursive(self):
        self.w("src/main.py", "print(1)\n")
        self.w("src/util/help.py", "pass\n")
        run_quiet(commands.cmd_add, self.repo, ["src"])
        idx = self.repo.load_index()
        self.assertEqual(idx.paths(), ["src/main.py", "src/util/help.py"])

    def test_stage_dot_covers_all_and_skips_gitlite(self):
        self.w("a.txt", "1\n")
        self.w("sub/b.txt", "2\n")
        run_quiet(commands.cmd_add, self.repo, ["."])
        idx = self.repo.load_index()
        self.assertEqual(idx.paths(), ["a.txt", "sub/b.txt"])

    def test_stage_deleted_tracked_file_removes_from_index(self):
        self.w("a.txt", "1\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        os.remove(os.path.join(self.tmp, "a.txt"))
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        idx = self.repo.load_index()
        self.assertNotIn("a.txt", idx.entries)

    def test_rejects_path_outside_repo(self):
        with self.assertRaises(RepositoryError):
            run_quiet(commands.cmd_add, self.repo, ["../outside.txt"])

    def test_rejects_unknown_path(self):
        with self.assertRaises(RepositoryError):
            run_quiet(commands.cmd_add, self.repo, ["no-such-file.txt"])


class CommitTest(TempRepoTestCase):
    def _commit(self, msg):
        return run_quiet(commands.cmd_commit, self.repo, msg)

    def test_commit_updates_branch_ref(self):
        self.w("a.txt", "1\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        code, out = self._commit("first")
        self.assertEqual(code, 0)
        oid = self.repo.read_ref("refs/heads/main")
        self.assertIsNotNone(oid)
        self.assertIn("[main", out)
        self.assertIn("first", out)

    def test_commit_rejected_when_nothing_staged(self):
        code, out = self._commit("empty")
        self.assertEqual(code, 1)
        self.assertIn("nothing to commit", out)

    def test_commit_rejected_when_tree_unchanged(self):
        self.w("a.txt", "1\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        self._commit("c1")
        code, out = self._commit("c2")
        self.assertEqual(code, 1)
        self.assertIn("nothing to commit", out)

    def test_parent_chain(self):
        for i, msg in enumerate(["c1", "c2", "c3"]):
            self.w(f"f{i}.txt", f"{i}\n")
            run_quiet(commands.cmd_add, self.repo, [f"f{i}.txt"])
            self._commit(msg)
        oid = self.repo.read_ref("refs/heads/main")
        chain = []
        while oid:
            _t, payload = self.repo.objects.read(oid)
            info = parse_commit(payload)
            chain.append(info["message"].strip())
            oid = info["parents"][0] if info["parents"] else None
        self.assertEqual(chain, ["c3", "c2", "c1"])

    def test_detached_head_commit_does_not_move_branch(self):
        self.w("a.txt", "1\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        self._commit("c1")
        base_oid = self.repo.read_ref("refs/heads/main")
        run_quiet(commands.cmd_checkout, self.repo, [base_oid[:8]])
        self.assertTrue(self.repo.head_is_detached())
        self.w("b.txt", "2\n")
        run_quiet(commands.cmd_add, self.repo, ["b.txt"])
        code, out = self._commit("detached work")
        self.assertEqual(code, 0)
        self.assertIn("detached", out)
        self.assertIn("warning", out)
        # 分支引用未动
        self.assertEqual(self.repo.read_ref("refs/heads/main"), base_oid)
        # HEAD 指向新提交
        self.assertNotEqual(self.repo.read_head(), base_oid)


class LogTest(TempRepoTestCase):
    def test_log_order_and_format(self):
        self.w("a.txt", "1\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        run_quiet(commands.cmd_commit, self.repo, "first commit")
        self.w("b.txt", "2\n")
        run_quiet(commands.cmd_add, self.repo, ["b.txt"])
        run_quiet(commands.cmd_commit, self.repo, "second commit")
        code, out = run_quiet(commands.cmd_log, self.repo)
        self.assertEqual(code, 0)
        self.assertIn("commit ", out)
        self.assertIn("Author: Test Author <author@example.com>", out)
        self.assertIn("Date:", out)
        self.assertIn("    second commit", out)
        self.assertIn("    first commit", out)
        self.assertLess(out.index("second commit"), out.index("first commit"))

    def test_log_from_named_branch(self):
        self.w("a.txt", "1\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        run_quiet(commands.cmd_commit, self.repo, "on main")
        run_quiet(commands.cmd_branch, self.repo, "dev")
        run_quiet(commands.cmd_checkout, self.repo, ["dev"])
        self.w("b.txt", "2\n")
        run_quiet(commands.cmd_add, self.repo, ["b.txt"])
        run_quiet(commands.cmd_commit, self.repo, "on dev")
        _c, out_main = run_quiet(commands.cmd_log, self.repo, "main")
        _c, out_dev = run_quiet(commands.cmd_log, self.repo, "dev")
        self.assertIn("on main", out_main)
        self.assertNotIn("on dev", out_main)
        self.assertIn("on dev", out_dev)
        self.assertIn("on main", out_dev)

    def test_log_empty_repo_rejected(self):
        with self.assertRaises(RepositoryError):
            run_quiet(commands.cmd_log, self.repo)

    def test_log_unknown_revision_rejected(self):
        self.w("a.txt", "1\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        run_quiet(commands.cmd_commit, self.repo, "c1")
        with self.assertRaises(RepositoryError):
            run_quiet(commands.cmd_log, self.repo, "no-such-branch")


class DiffTest(TempRepoTestCase):
    def _seed(self):
        self.w("a.txt", "line1\nline2\nline3\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        run_quiet(commands.cmd_commit, self.repo, "c1")

    def test_diff_workdir_vs_index(self):
        self._seed()
        self.w("a.txt", "line1\nLINE2\nline3\n")
        code, out = run_quiet(commands.cmd_diff, self.repo)
        self.assertEqual(code, 1)  # 有差异
        self.assertIn("diff --gitlite a/a.txt b/a.txt", out)
        self.assertIn("-line2", out)
        self.assertIn("+LINE2", out)
        self.assertIn("@@ -1,3 +1,3 @@", out)

    def test_diff_clean_returns_zero(self):
        self._seed()
        code, out = run_quiet(commands.cmd_diff, self.repo)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_diff_staged_new_file(self):
        self._seed()
        self.w("new.txt", "fresh\n")
        run_quiet(commands.cmd_add, self.repo, ["new.txt"])
        code, out = run_quiet(commands.cmd_diff, self.repo, staged=True)
        self.assertEqual(code, 1)
        self.assertIn("--- /dev/null", out)
        self.assertIn("+++ b/new.txt", out)
        self.assertIn("+fresh", out)

    def test_diff_staged_modification(self):
        self._seed()
        self.w("a.txt", "changed\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        code, out = run_quiet(commands.cmd_diff, self.repo, staged=True)
        self.assertIn("-line1", out)
        self.assertIn("+changed", out)

    def test_diff_deleted_file(self):
        self._seed()
        os.remove(os.path.join(self.tmp, "a.txt"))
        code, out = run_quiet(commands.cmd_diff, self.repo)
        self.assertEqual(code, 1)
        self.assertIn("--- a/a.txt", out)
        self.assertIn("+++ /dev/null", out)
        self.assertIn("-line1", out)


class BranchTest(TempRepoTestCase):
    def _seed_commit(self, msg="base"):
        self.w("a.txt", "1\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        run_quiet(commands.cmd_commit, self.repo, msg)
        return self.repo.read_ref("refs/heads/main")

    def test_create_and_list(self):
        base = self._seed_commit()
        code, _ = run_quiet(commands.cmd_branch, self.repo, "dev")
        self.assertEqual(code, 0)
        code, out = run_quiet(commands.cmd_branch, self.repo)
        self.assertEqual(code, 0)
        self.assertIn("* main", out)
        self.assertIn("  dev", out)
        self.assertEqual(self.repo.read_ref("refs/heads/dev"), base)

    def test_create_requires_commit(self):
        with self.assertRaises(RepositoryError):
            run_quiet(commands.cmd_branch, self.repo, "early")

    def test_duplicate_rejected(self):
        self._seed_commit()
        run_quiet(commands.cmd_branch, self.repo, "dev")
        with self.assertRaises(RepositoryError):
            run_quiet(commands.cmd_branch, self.repo, "dev")

    def test_delete_merged(self):
        self._seed_commit()
        run_quiet(commands.cmd_branch, self.repo, "dev")
        code, out = run_quiet(commands.cmd_branch, self.repo, "dev", delete="-d")
        self.assertEqual(code, 0)
        self.assertIn("deleted branch dev", out)
        self.assertIsNone(self.repo.read_ref("refs/heads/dev"))

    def test_delete_unmerged_requires_D(self):
        self._seed_commit()
        run_quiet(commands.cmd_branch, self.repo, "dev")
        run_quiet(commands.cmd_checkout, self.repo, ["dev"])
        self.w("b.txt", "2\n")
        run_quiet(commands.cmd_add, self.repo, ["b.txt"])
        run_quiet(commands.cmd_commit, self.repo, "dev only")
        with self.assertRaises(RepositoryError):
            run_quiet(commands.cmd_branch, self.repo, "dev", delete="-d")
        # 切回 main 后 dev 仍未合并
        run_quiet(commands.cmd_checkout, self.repo, ["main"])
        code, out = run_quiet(commands.cmd_branch, self.repo, "dev", delete="-D")
        self.assertEqual(code, 0)

    def test_cannot_delete_current_branch(self):
        self._seed_commit()
        run_quiet(commands.cmd_branch, self.repo, "dev")
        run_quiet(commands.cmd_checkout, self.repo, ["dev"])
        with self.assertRaises(RepositoryError):
            run_quiet(commands.cmd_branch, self.repo, "dev", delete="-D")


class CheckoutTest(TempRepoTestCase):
    def _seed(self):
        self.w("a.txt", "v1\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        run_quiet(commands.cmd_commit, self.repo, "c1")
        run_quiet(commands.cmd_branch, self.repo, "dev")

    def test_switch_branch_file_states(self):
        self._seed()
        run_quiet(commands.cmd_checkout, self.repo, ["dev"])
        self.assertEqual(self.repo.current_branch(), "dev")
        self.w("b.txt", "dev file\n")
        run_quiet(commands.cmd_add, self.repo, ["b.txt"])
        run_quiet(commands.cmd_commit, self.repo, "dev commit")
        self.assertTrue(self.exists("b.txt"))
        run_quiet(commands.cmd_checkout, self.repo, ["main"])
        self.assertFalse(self.exists("b.txt"), "main 上不应出现 dev 独有文件")
        self.assertEqual(self.r("a.txt"), "v1\n")
        run_quiet(commands.cmd_checkout, self.repo, ["dev"])
        self.assertEqual(self.r("b.txt"), "dev file\n")
        self.assertEqual(self.r("a.txt"), "v1\n")

    def test_switch_resets_index_to_target(self):
        self._seed()
        run_quiet(commands.cmd_checkout, self.repo, ["dev"])
        self.w("b.txt", "dev file\n")
        run_quiet(commands.cmd_add, self.repo, ["b.txt"])
        run_quiet(commands.cmd_commit, self.repo, "dev commit")
        run_quiet(commands.cmd_checkout, self.repo, ["main"])
        idx = self.repo.load_index()
        self.assertNotIn("b.txt", idx.entries)

    def test_refuses_uncommitted_worktree_changes(self):
        self._seed()
        run_quiet(commands.cmd_checkout, self.repo, ["dev"])
        self.w("b.txt", "dev file\n")
        run_quiet(commands.cmd_add, self.repo, ["b.txt"])
        run_quiet(commands.cmd_commit, self.repo, "dev commit")
        run_quiet(commands.cmd_checkout, self.repo, ["main"])
        self.w("a.txt", "dirty\n")  # 未暂存修改
        with self.assertRaises(RepositoryError):
            run_quiet(commands.cmd_checkout, self.repo, ["dev"])
        # 恢复后可以切换
        run_quiet(commands.cmd_checkout, self.repo, ["--", "a.txt"])
        run_quiet(commands.cmd_checkout, self.repo, ["dev"])
        self.assertEqual(self.repo.current_branch(), "dev")

    def test_refuses_staged_but_uncommitted(self):
        self._seed()
        run_quiet(commands.cmd_checkout, self.repo, ["dev"])
        self.w("b.txt", "dev file\n")
        run_quiet(commands.cmd_add, self.repo, ["b.txt"])
        run_quiet(commands.cmd_commit, self.repo, "dev commit")
        run_quiet(commands.cmd_checkout, self.repo, ["main"])
        self.w("a.txt", "staged not committed\n")
        run_quiet(commands.cmd_add, self.repo, ["a.txt"])
        with self.assertRaises(RepositoryError):
            run_quiet(commands.cmd_checkout, self.repo, ["dev"])

    def test_restore_single_file(self):
        self._seed()
        self.w("a.txt", "modified\n")
        run_quiet(commands.cmd_checkout, self.repo, ["--", "a.txt"])
        self.assertEqual(self.r("a.txt"), "v1\n")

    def test_restore_requires_tracked(self):
        self._seed()
        self.w("untracked.txt", "?\n")
        with self.assertRaises(RepositoryError):
            run_quiet(commands.cmd_checkout, self.repo, ["--", "untracked.txt"])

    def test_detached_head(self):
        self._seed()
        oid = self.repo.read_ref("refs/heads/main")
        code, out = run_quiet(commands.cmd_checkout, self.repo, [oid[:8]])
        self.assertEqual(code, 0)
        self.assertTrue(self.repo.head_is_detached())
        self.assertIn("detached", out)
        # log 在分离状态下可用
        _c, out = run_quiet(commands.cmd_log, self.repo)
        self.assertIn("c1", out)
        # 切回分支
        run_quiet(commands.cmd_checkout, self.repo, ["main"])
        self.assertEqual(self.repo.current_branch(), "main")

    def test_checkout_unknown_name_is_error(self):
        self._seed()
        with self.assertRaises(RepositoryError):
            run_quiet(commands.cmd_checkout, self.repo, ["nope"])


class NestedTreeTest(TempRepoTestCase):
    def test_subdirectory_roundtrip(self):
        self.w("src/core/main.py", "print('main')\n")
        self.w("src/core/util/jsonx.py", "def dump(): pass\n")
        self.w("README.md", "# demo\n")
        run_quiet(commands.cmd_add, self.repo, ["."])
        run_quiet(commands.cmd_commit, self.repo, "nested")
        head = self.repo.head_commit_oid()
        files = self.repo.commit_tree_files(head)
        self.assertEqual(
            sorted(files),
            ["README.md", "src/core/main.py", "src/core/util/jsonx.py"],
        )
        # 修改子目录文件后再次提交
        self.w("src/core/main.py", "print('v2')\n")
        run_quiet(commands.cmd_add, self.repo, ["src"])
        run_quiet(commands.cmd_commit, self.repo, "nested v2")
        head2 = self.repo.head_commit_oid()
        _t, payload = self.repo.objects.read(head2)
        parent = parse_commit(payload)["parents"]
        self.assertEqual(parent, [head])


if __name__ == "__main__":
    unittest.main()
