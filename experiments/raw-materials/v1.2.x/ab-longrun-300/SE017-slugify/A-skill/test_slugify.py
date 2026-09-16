"""Tests for slugify — must fail on seed, pass after fix."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_lowercase(self):
        self.assertEqual(slugify("HELLO"), "hello")
        self.assertEqual(slugify("MiXeD"), "mixed")

    def test_collapse_whitespace_and_punctuation(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a...b"), "a-b")
        self.assertEqual(slugify("a ,. b"), "a-b")
        self.assertEqual(slugify("a--b"), "a-b")

    def test_strip_leading_trailing_separators(self):
        self.assertEqual(slugify("-hello-"), "hello")
        self.assertEqual(slugify("  hello  "), "hello")
        self.assertEqual(slugify("!!!hello!!!"), "hello")
        self.assertEqual(slugify("-- hello --"), "hello")

    def test_non_alnum_stripped(self):
        self.assertEqual(slugify("a@b#c"), "a-b-c")
        self.assertEqual(slugify("foo/bar\\baz"), "foo-bar-baz")
        self.assertEqual(slugify("100% legit"), "100-legit")

    def test_empty_input(self):
        self.assertEqual(slugify(""), "")

    def test_pure_punctuation_or_whitespace(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify(" - - - "), "")
        self.assertEqual(slugify(".,;:!?"), "")

    def test_unicode_nfkd_fold(self):
        # Strategy: NFKD + strip combining marks (ASCII-fold accents)
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Über"), "uber")
        self.assertEqual(slugify("Ångström"), "angstrom")
        self.assertEqual(slugify("crème brûlée"), "creme-brulee")

    def test_unicode_letters_without_decomposable_accent(self):
        # Letters that survive NFKD stay (lowercased), non-ASCII allowed via lower
        self.assertEqual(slugify("你好"), "你好")
        self.assertEqual(slugify("ПРИВЕТ"), "привет")

    def test_digits_preserved(self):
        self.assertEqual(slugify("Chapter 12"), "chapter-12")
        self.assertEqual(slugify("2024-01-01"), "2024-01-01")

    def test_mixed_edge(self):
        self.assertEqual(slugify("  --Hello,   World!!  -- "), "hello-world")
        self.assertEqual(slugify("a1_b2"), "a1-b2")


if __name__ == "__main__":
    unittest.main()
