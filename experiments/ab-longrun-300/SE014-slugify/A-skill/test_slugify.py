"""Tests for slugify — TDD RED first, then GREEN after fix.

Unicode strategy: NFKD normalize + drop combining marks, then lower.
  Café -> cafe  (not café)
"""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_collapse_runs(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a---b"), "a-b")
        self.assertEqual(slugify("a ,.; b"), "a-b")
        self.assertEqual(slugify("  multi   spaces  and---dashes  "), "multi-spaces-and-dashes")

    def test_strip_edges(self):
        self.assertEqual(slugify("---lead---"), "lead")
        self.assertEqual(slugify("trail---"), "trail")
        self.assertEqual(slugify("-a-"), "a")

    def test_lower(self):
        self.assertEqual(slugify("HELLO World"), "hello-world")
        self.assertEqual(slugify("MiXeD"), "mixed")

    def test_alnum_and_hyphen_only(self):
        self.assertEqual(slugify("Hello, World! @#$%"), "hello-world")
        self.assertEqual(slugify("a_b"), "a-b")  # underscore is non-alnum -> becomes -

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!...???"), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify(",,,"), "")

    def test_numbers(self):
        self.assertEqual(slugify("abc123"), "abc123")
        self.assertEqual(slugify("1 2 3"), "1-2-3")

    def test_unicode_nfkd(self):
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Ünïcödé"), "unicode")

    def test_unicode_mixed(self):
        self.assertEqual(slugify("Café au Lait!"), "cafe-au-lait")


if __name__ == "__main__":
    unittest.main()
