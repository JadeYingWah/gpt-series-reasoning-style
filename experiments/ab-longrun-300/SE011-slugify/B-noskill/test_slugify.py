"""Tests for slugify. Written before the fix (RED → GREEN)."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!...???"), "")

    def test_consecutive_separators_collapse(self):
        self.assertEqual(slugify("a---b"), "a-b")
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a!!!b"), "a-b")
        self.assertEqual(slugify("a ,.; b"), "a-b")

    def test_strip_leading_trailing_symbols(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("!!Hello!!"), "hello")
        self.assertEqual(slugify("  spaced  "), "spaced")

    def test_non_alphanumeric_stripped(self):
        self.assertEqual(slugify("foo@bar#baz"), "foo-bar-baz")
        self.assertEqual(slugify("a_b"), "a-b")
        self.assertEqual(slugify("path/to/file"), "path-to-file")

    def test_unicode_nfkd_ascii_folding(self):
        # Policy: NFKD + strip combining marks → Café → cafe
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Über"), "uber")

    def test_already_slug(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_digits_preserved(self):
        self.assertEqual(slugify("Chapter 42"), "chapter-42")

    def test_mixed_case_lowered(self):
        self.assertEqual(slugify("MiXeD CaSe"), "mixed-case")


if __name__ == "__main__":
    unittest.main()
