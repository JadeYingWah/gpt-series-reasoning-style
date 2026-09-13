"""Tests for slugify (RED first, then GREEN)."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_collapse_whitespace_and_punct(self):
        self.assertEqual(slugify("a   b---c  d"), "a-b-c-d")
        self.assertEqual(slugify("foo,,,bar;;baz"), "foo-bar-baz")

    def test_strip_leading_trailing_hyphens(self):
        self.assertEqual(slugify("!!!Hello!!!"), "hello")
        self.assertEqual(slugify("  -hello-  "), "hello")
        self.assertEqual(slugify("--foo--bar--"), "foo-bar")

    def test_non_alnum_stripped_except_hyphen(self):
        self.assertEqual(slugify("a_b.c/d"), "a-b-c-d")
        self.assertEqual(slugify("user@name.com"), "user-name-com")

    def test_empty_and_whitespace_only(self):
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify("!!!"), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("..."), "")
        self.assertEqual(slugify("!!!???..."), "")

    def test_leading_trailing_symbols(self):
        self.assertEqual(slugify("***abc***"), "abc")
        self.assertEqual(slugify("___abc___"), "abc")

    def test_multiple_separators_collapse_to_one(self):
        self.assertEqual(slugify("a - - - b"), "a-b")
        self.assertEqual(slugify("x +++ y +++ z"), "x-y-z")

    def test_unicode_lower(self):
        # Strategy: NFKD ASCII-fold. Café -> cafe.
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("Über"), "uber")

    def test_already_slug(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_digits(self):
        self.assertEqual(slugify("Chapter 12"), "chapter-12")
        self.assertEqual(slugify("2024-01-01"), "2024-01-01")


if __name__ == "__main__":
    unittest.main()
