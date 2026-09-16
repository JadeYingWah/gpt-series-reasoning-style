# -*- coding: utf-8 -*-
"""add / commit 行为测试：正常、边界、异常全覆盖。"""
import json

from glit import index as index_mod
from glit import objects, treebuild
from glit.commit import read_commit
from tests.helpers import TempRepoTestCase, run_cli, run_cli_expect


class AddTest(TempRepoTestCase):
    def test_add_single_file(self):
        self.write("a.txt", "hello\n")
        run_cli_expect("add", "a.txt")
        entries = index_mod.read_index(self.tmp)
        self.assertIn("a.txt", entries)
        _, payload = objects.read_object(self.tmp, entries["a.txt"])
        self.assertEqual(payload, b"hello\n")

    def test_add_directory_recursive_and_excludes(self):
        self.write("src/deep/x.py", "print(1)\n")
        self.write("src/y.py", "print(2)\n")
        (self.tmp / ".glit" / "objects").touch() if False else None
        self.write("__pycache__/junk.pyc", "binary")
        run_cli_expect("add", ".")
        entries = index_mod.read_index(self.tmp)
        self.assertIn("src/deep/x.py", entries)
        self.assertIn("src/y.py", entries)
        self.assertNotIn("__pycache__/junk.pyc", entries)

    def test_add_update_changes_sha(self):
        self.write("a.txt", "v1")
        run_cli_expect("add", "a.txt")
        sha1 = index_mod.read_index(self.tmp)["a.txt"]
        self.write("a.txt", "v2")
        run_cli_expect("add", "a.txt")
        sha2 = index_mod.read_index(self.tmp)["a.txt"]
        self.assertNotEqual(sha1, sha2)

    def test_add_missing_path_errors(self):
        code, _, err = run_cli("add", "ghost.txt")
        self.assertEqual(code, 1)
        self.assertIn("did not match", err)

    def test_add_stages_deletion_of_tracked_file(self):
        self.write("a.txt", "bye")
        run_cli_expect("add", "a.txt")
        (self.tmp / "a.txt").unlink()
        run_cli_expect("add", "a.txt")
        self.assertNotIn("a.txt", index_mod.read_index(self.tmp))

    def test_add_nested_path_normalization(self):
        self.write("src/deep/x.py", "1\n")
        run_cli_expect("add", "src/deep/x.py")
        self.assertIn("src/deep/x.py", index_mod.read_index(self.tmp))


class CommitTest(TempRepoTestCase):
    def _commit(self, msg="msg"):
        return run_cli_expect("commit", "-m", msg)

    def test_first_commit_basic(self):
        self.write("a.txt", "A")
        run_cli_expect("add", "a.txt")
        out = self._commit("first")
        self.assertIn("[main ", out)
        self.assertIn("first", out)
        head = self.repo.head_commit()
        self.assertIsNotNone(head)
        commit = read_commit(self.tmp, head)
        self.assertEqual(commit["parents"], [])
        self.assertEqual(commit["message"], "first")
        self.assertTrue(commit["author"])
        self.assertTrue(commit["timestamp"])

    def test_empty_initial_commit_rejected(self):
        code, _, err = run_cli("commit", "-m", "empty")
        self.assertEqual(code, 1)
        self.assertIn("nothing to commit", err)

    def test_duplicate_commit_rejected(self):
        self.write("a.txt", "A")
        run_cli_expect("add", "a.txt")
        self._commit("c1")
        code, _, err = run_cli("commit", "-m", "c2")
        self.assertEqual(code, 1)
        self.assertIn("nothing to commit", err)

    def test_second_commit_links_parent(self):
        self.write("a.txt", "A")
        run_cli_expect("add", "a.txt")
        self._commit("c1")
        self.write("b.txt", "B")
        run_cli_expect("add", "b.txt")
        self._commit("c2")
        head = self.repo.head_commit()
        commit2 = read_commit(self.tmp, head)
        self.assertEqual(len(commit2["parents"]), 1)
        c1 = read_commit(self.tmp, commit2["parents"][0])
        self.assertEqual(c1["message"], "c1")
        self.assertEqual(c1["parents"], [])  # 链条根

    def test_multiline_message(self):
        self.write("a.txt", "A")
        run_cli_expect("add", "a.txt")
        self._commit("line1\nline2\n")
        commit = read_commit(self.tmp, self.repo.head_commit())
        self.assertEqual(commit["message"], "line1\nline2\n")

    def test_empty_message_rejected(self):
        self.write("a.txt", "A")
        run_cli_expect("add", "a.txt")
        code, _, err = run_cli("commit", "-m", "   ")
        self.assertEqual(code, 1)
        self.assertIn("empty", err)

    def test_commit_updates_branch_ref_not_head(self):
        self.write("a.txt", "A")
        run_cli_expect("add", "a.txt")
        self._commit("c1")
        self.assertEqual(
            (self.tmp / ".glit" / "HEAD").read_text(encoding="utf-8").strip(),
            "ref: refs/heads/main",
        )
        self.assertEqual(self.repo.read_branch("main"), self.repo.head_commit())

    def test_deleted_file_disappears_from_tree(self):
        self.write("a.txt", "A")
        self.write("b.txt", "B")
        run_cli_expect("add", ".")
        self._commit("both")
        (self.tmp / "b.txt").unlink()
        run_cli_expect("add", "b.txt")
        self._commit("remove b")
        flat = treebuild.flatten_commit(self.tmp, self.repo.head_commit())
        self.assertEqual(set(flat), {"a.txt"})


class TreeBuildTest(TempRepoTestCase):
    def test_nested_tree_structure(self):
        self.write("a.txt", "A")
        self.write("src/deep/x.py", "X")
        self.write("src/y.py", "Y")
        run_cli_expect("add", ".")
        run_cli_expect("commit", "-m", "tree")
        flat = treebuild.flatten_commit(self.tmp, self.repo.head_commit())
        self.assertEqual(
            flat,
            {
                "a.txt": flat["a.txt"],
                "src/deep/x.py": flat["src/deep/x.py"],
                "src/y.py": flat["src/y.py"],
            },
        )
        # tree 对象可独立按路径访问
        root = read_commit(self.tmp, self.repo.head_commit())["tree"]
        entries = {e["name"]: e for e in treebuild.read_tree_payload(self.tmp, root)}
        self.assertEqual(entries["src"]["type"], "tree")
        src_sha = entries["src"]["sha"]
        sub = {e["name"]: e for e in treebuild.read_tree_payload(self.tmp, src_sha)}
        self.assertEqual(sub["deep"]["type"], "tree")
        self.assertEqual(sub["y.py"]["type"], "blob")

    def test_identical_tree_content_dedup(self):
        # 相同内容的子树自动去重（内容寻址）
        self.write("d1/f.txt", "same")
        self.write("d2/f.txt", "same")
        run_cli_expect("add", ".")
        run_cli_expect("commit", "-m", "dedup")
        root = read_commit(self.tmp, self.repo.head_commit())["tree"]
        entries = {e["name"]: e for e in treebuild.read_tree_payload(self.tmp, root)}
        self.assertEqual(entries["d1"]["sha"], entries["d2"]["sha"])

    def test_tree_is_deterministic(self):
        self.write("b.txt", "B")
        self.write("a.txt", "A")
        run_cli_expect("add", ".")
        run_cli_expect("commit", "-m", "t1")
        t1 = read_commit(self.tmp, self.repo.head_commit())["tree"]
        entries = [e["name"] for e in treebuild.read_tree_payload(self.tmp, t1)]
        self.assertEqual(entries, sorted(entries, key=lambda n: n.encode("utf-8")))


if __name__ == "__main__":
    unittest.main()
