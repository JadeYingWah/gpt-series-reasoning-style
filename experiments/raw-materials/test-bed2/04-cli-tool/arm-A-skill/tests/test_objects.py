# -*- coding: utf-8 -*-
"""对象存储层测试：roundtrip、幂等、损坏检测、边界。"""
import unittest

from glit import objects
from tests.helpers import TempRepoTestCase


class ObjectRoundtripTest(TempRepoTestCase):
    def test_blob_roundtrip_small(self):
        sha = objects.write_object(self.tmp, objects.TYPE_BLOB, b"hello\n")
        obj_type, payload = objects.read_object(self.tmp, sha)
        self.assertEqual(obj_type, objects.TYPE_BLOB)
        self.assertEqual(payload, b"hello\n")

    def test_object_lands_at_expected_path(self):
        sha = objects.write_object(self.tmp, objects.TYPE_BLOB, b"x")
        self.assertTrue((self.tmp / ".glit" / "objects" / sha[:2] / sha[2:]).is_file())

    def test_same_content_idempotent_single_copy(self):
        sha1 = objects.write_object(self.tmp, objects.TYPE_BLOB, b"same")
        sha2 = objects.write_object(self.tmp, objects.TYPE_BLOB, b"same")
        self.assertEqual(sha1, sha2)
        objs = list((self.tmp / ".glit" / "objects").rglob("*"))
        files = [p for p in objs if p.is_file()]
        self.assertEqual(len(files), 1)

    def test_different_types_same_payload_distinct_sha(self):
        # 头部参与哈希：同 payload 不同 type 必须得到不同对象名
        sb = objects.write_object(self.tmp, objects.TYPE_BLOB, b"abc")
        st = objects.write_object(self.tmp, objects.TYPE_TREE, b"abc")
        self.assertNotEqual(sb, st)

    def test_large_binary_roundtrip(self):
        import os as _os

        data = _os.urandom(1_000_000)  # 1MB 随机二进制
        sha = objects.write_object(self.tmp, objects.TYPE_BLOB, data)
        _, payload = objects.read_object(self.tmp, sha)
        self.assertEqual(payload, data)

    def test_empty_payload_roundtrip(self):
        sha = objects.write_object(self.tmp, objects.TYPE_BLOB, b"")
        _, payload = objects.read_object(self.tmp, sha)
        self.assertEqual(payload, b"")


class ObjectCorruptionTest(TempRepoTestCase):
    def _write_raw(self, data: bytes, sha: str) -> None:
        d = self.tmp / ".glit" / "objects" / sha[:2]
        d.mkdir(parents=True, exist_ok=True)
        (d / sha[2:]).write_bytes(data)

    def test_bad_magic_detected(self):
        sha = objects.write_object(self.tmp, objects.TYPE_BLOB, b"ok")
        path = self.tmp / ".glit" / "objects" / sha[:2] / sha[2:]
        raw = path.read_bytes()
        path.write_bytes(b"XXXX" + raw[4:])  # 破坏 magic
        with self.assertRaises(objects.ObjectCorrupted):
            objects.read_object(self.tmp, sha)

    def test_payload_tamper_detected_by_hash(self):
        sha = objects.write_object(self.tmp, objects.TYPE_BLOB, b"trust me")
        path = self.tmp / ".glit" / "objects" / sha[:2] / sha[2:]
        import zlib

        full = zlib.decompress(path.read_bytes())
        tampered = full[:-1] + bytes([full[-1] ^ 0xFF])  # 翻转最后一字节
        path.write_bytes(zlib.compress(tampered))
        with self.assertRaises(objects.ObjectCorrupted):
            objects.read_object(self.tmp, sha)

    def test_length_mismatch_detected(self):
        sha = objects.write_object(self.tmp, objects.TYPE_BLOB, b"12345")
        path = self.tmp / ".glit" / "objects" / sha[:2] / sha[2:]
        import struct
        import zlib

        full = bytearray(zlib.decompress(path.read_bytes()))
        # payload_len 字段位于 header 尾部 4B（offset 6..10），改大但不改内容
        struct.pack_into(">I", full, 6, 999)
        path.write_bytes(zlib.compress(bytes(full)))
        with self.assertRaises(objects.ObjectCorrupted):
            objects.read_object(self.tmp, sha)

    def test_missing_object_raises(self):
        with self.assertRaises(objects.ObjectCorrupted):
            objects.read_object(self.tmp, "0" * 40)

    def test_invalid_name_raises(self):
        for bad in ("", "xyz", "a" * 39, "G" * 40):
            with self.assertRaises(objects.ObjectCorrupted):
                objects.read_object(self.tmp, bad)


if __name__ == "__main__":
    unittest.main()
