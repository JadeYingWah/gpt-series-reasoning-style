# -*- coding: utf-8 -*-
"""仓库层测试：init 结构、重复 init、向上定位、仓库外报错、分支名校验。"""
import os
import tempfile
import unittest
from pathlib import Path

from glit import GlitError
from glit.repo import Repo, validate_branch_name
from tests.helpers import TempRepoTestCase, run_cli, run_cli_expect


class InitTest(TempRepoTestCase):
    def test_init_creates_structure(self):
        self.assertTrue((self.tmp / ".glit").is_dir())
        self.assertTrue((self.tmp / ".glit" / "objects").is_dir())
        self.assertTrue((self.tmp / ".glit" / "refs" / "heads").is_dir())
        self.assertTrue((self.tmp / ".glit" / "HEAD").is_file())
        self.assertTrue((self.tmp / ".glit" / "index.json").is_file())
        self.assertEqual(
            (self.tmp / ".glit" / "HEAD").read_text(encoding="utf-8").strip(),
            "ref: refs/heads/main",
        )

    def test_init_output_message(self):
        # setUp 已建仓库，这里用独立目录验证首次 init 的输出
        import tempfile

        with tempfile.TemporaryDirectory(prefix="glit-msg-") as d:
            out = run_cli_expect("init", d.replace("\\", "/"))
            self.assertTrue(out.strip().startswith("Initialized empty glit repository"))

    def test_reinit_rejected(self):
        code, _, err = run_cli("init")
        self.assertEqual(code, 1)
        self.assertIn("already exists", err)

    def test_init_explicit_path(self):
        import tempfile

        with tempfile.TemporaryDirectory(prefix="glit-other-") as d:
            out = run_cli_expect("init", d.replace("\\", "/"))
            self.assertIn("Initialized", out)
            self.assertTrue((Path(d) / ".glit" / "HEAD").is_file())


class FindRepoTest(TempRepoTestCase):
    def test_find_from_subdirectory(self):
        sub = self.tmp / "a" / "b"
        sub.mkdir(parents=True)
        repo = Repo.find(sub)
        self.assertEqual(repo.root, self.tmp.resolve())

    def test_find_outside_repo_raises(self):
        import tempfile

        with tempfile.TemporaryDirectory(prefix="no-repo-") as d:
            with self.assertRaises(GlitError):
                Repo.find(Path(d))

    def test_command_outside_repo_fails_with_exit_1(self):
        import tempfile

        with tempfile.TemporaryDirectory(prefix="no-repo-") as d:
            code, _, err = run_cli("log", cwd=Path(d))
            self.assertEqual(code, 1)
            self.assertIn("not a glit repository", err)


class BranchNameValidationTest(unittest.TestCase):
    def test_valid_names(self):
        for name in ("main", "dev", "feature/x", "v1.0", "a-b_c", "rel-1.2/fix"):
            self.assertEqual(validate_branch_name(name), name)

    def test_invalid_names(self):
        # 注："-x" 由 argparse 层处理（见 test_unknown_option_is_argparse_error），
        # 不属于业务名校验范畴。
        for bad in ("", "a..b", "a/b..c", "a//b", "x.lock", ".hidden", "a/.b",
                    "a b", "a\tb", "a\\b", "/abs", "rel/", "中文分支"):
            with self.assertRaises(GlitError, msg=bad):
                validate_branch_name(bad)

    def test_unknown_option_is_argparse_error(self):
        # "-x" 是未知选项 -> argparse 抛 SystemExit(2)（参数错误，非业务错误）
        with self.assertRaises(SystemExit) as cm:
            run_cli("branch", "-x")
        self.assertEqual(cm.exception.code, 2)


class RefOperationsTest(TempRepoTestCase):
    def test_update_read_delete_branch(self):
        self.repo.update_branch("dev", "a" * 40)
        self.assertEqual(self.repo.read_branch("dev"), "a" * 40)
        self.assertIn("dev", self.repo.list_branches())
        self.repo.delete_branch("dev")
        self.assertIsNone(self.repo.read_branch("dev"))

    def test_delete_missing_branch_raises(self):
        with self.assertRaises(GlitError):
            self.repo.delete_branch("ghost")

    def test_head_commit_none_before_first_commit(self):
        self.assertIsNone(self.repo.head_commit())

    def test_subdirectory_branch_ref(self):
        self.repo.update_branch("feature/one", "b" * 40)
        self.assertIn("feature/one", self.repo.list_branches())


if __name__ == "__main__":
    unittest.main()
