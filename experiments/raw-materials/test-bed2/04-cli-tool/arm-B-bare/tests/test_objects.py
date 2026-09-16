"""对象存储层单元测试。"""

import os
import unittest

from gitlite.objects import (
    BLOB,
    COMMIT,
    MODE_DIR,
    MODE_FILE,
    TREE,
    ObjectError,
    ObjectStore,
    blob_oid,
    build_tree_payload,
    deserialize,
    format_commit_payload,
    parse_commit,
    parse_tree,
    serialize,
)


class SerializeTest(unittest.TestCase):
    def test_roundtrip(self):
        raw = serialize(BLOB, "hello\n".encode())
        otype, payload = deserialize(raw)
        self.assertEqual(otype, BLOB)
        self.assertEqual(payload, b"hello\n")

    def test_header_format(self):
        raw = serialize(TREE, b"\x00\x01")
        self.assertEqual(raw, b"tree 2\n\x00\x01")

    def test_rejects_unknown_type(self):
        with self.assertRaises(ObjectError):
            serialize("tag", b"x")

    def test_rejects_non_bytes_payload(self):
        with self.assertRaises(ObjectError):
            serialize(BLOB, "str not bytes")

    def test_rejects_corrupted(self):
        with self.assertRaises(ObjectError):
            deserialize(b"no header here")
        raw = serialize(BLOB, b"abc")
        with self.assertRaises(ObjectError):
            deserialize(raw[:-1])  # 截断载荷

    def test_blob_oid_deterministic(self):
        self.assertEqual(blob_oid(b"x"), blob_oid(b"x"))
        self.assertNotEqual(blob_oid(b"x"), blob_oid(b"y"))


class ObjectStoreTest(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp = tempfile.mkdtemp(prefix="gitlite-obj-")
        self.store = ObjectStore(os.path.join(self.tmp, "objects"))

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_store_and_read_roundtrip(self):
        oid = self.store.store(BLOB, b"payload-bytes")
        otype, payload = self.store.read(oid)
        self.assertEqual(otype, BLOB)
        self.assertEqual(payload, b"payload-bytes")

    def test_layout_sharding(self):
        oid = self.store.store(BLOB, b"abc")
        p = os.path.join(self.tmp, "objects", oid[:2], oid[2:])
        self.assertTrue(os.path.isfile(p))

    def test_dedup_identical_content(self):
        oid1 = self.store.store(BLOB, b"same")
        oid2 = self.store.store(BLOB, b"same")
        self.assertEqual(oid1, oid2)

    def test_prefix_lookup(self):
        oid = self.store.store(BLOB, b"prefix-test")
        matches = self.store.prefixes(oid[:5])
        self.assertEqual(matches, [oid])
        self.assertEqual(self.store.prefixes(oid[:2] + "zz"), [])

    def test_missing_object_raises(self):
        with self.assertRaises(ObjectError):
            self.store.read("00" * 32)

    def test_corruption_detected(self):
        oid = self.store.store(BLOB, b"integrity")
        p = os.path.join(self.tmp, "objects", oid[:2], oid[2:])
        import zlib

        with open(p, "wb") as f:
            f.write(zlib.compress(serialize(BLOB, b"tampered!!")))
        with self.assertRaises(ObjectError):
            self.store.read(oid)


class TreeTest(unittest.TestCase):
    def test_build_and_parse_roundtrip(self):
        payload = build_tree_payload(
            [(MODE_FILE, "aa" * 32, "b.txt"), (MODE_DIR, "bb" * 32, "sub")]
        )
        entries = parse_tree(payload)
        self.assertEqual(
            entries,
            [(MODE_FILE, "aa" * 32, "b.txt"), (MODE_DIR, "bb" * 32, "sub")],
        )

    def test_sorted_deterministic(self):
        p1 = build_tree_payload([(MODE_FILE, "a" * 32, "z.txt"), (MODE_FILE, "b" * 32, "a.txt")])
        p2 = build_tree_payload([(MODE_FILE, "b" * 32, "a.txt"), (MODE_FILE, "a" * 32, "z.txt")])
        self.assertEqual(p1, p2)

    def test_name_with_spaces(self):
        payload = build_tree_payload([(MODE_FILE, "a" * 32, "my file.txt")])
        entries = parse_tree(payload)
        self.assertEqual(entries[0][2], "my file.txt")


class CommitTest(unittest.TestCase):
    def test_format_parse_roundtrip(self):
        payload = format_commit_payload(
            tree_oid="ab" * 32,
            parents=["cd" * 32],
            author="Alice <a@x.com> 1700000000 +0800",
            committer="Alice <a@x.com> 1700000000 +0800",
            message="subject line\n\nbody text\n",
        )
        info = parse_commit(payload)
        self.assertEqual(info["tree"], "ab" * 32)
        self.assertEqual(info["parents"], ["cd" * 32])
        self.assertEqual(info["author"], "Alice <a@x.com> 1700000000 +0800")
        self.assertEqual(info["message"], "subject line\n\nbody text\n")

    def test_root_commit_no_parents(self):
        payload = format_commit_payload("ab" * 32, [], "A <a@x> 1 +0000", "A <a@x> 1 +0000", "root")
        info = parse_commit(payload)
        self.assertEqual(info["parents"], [])
        self.assertEqual(info["message"].strip(), "root")

    def test_missing_tree_rejected(self):
        with self.assertRaises(ObjectError):
            parse_commit(b"author X\n\nmsg\n")


if __name__ == "__main__":
    unittest.main()
