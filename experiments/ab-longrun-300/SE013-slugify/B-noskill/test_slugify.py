"""Tests for slugify — written against the spec, not the buggy impl."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_whitespace_collapses_to_single_hyphen(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a\tb\nc"), "a-b-c")

    def test_punctuation_collapses_to_single_hyphen(self):
        self.assertEqual(slugify("a,,b"), "a-b")
        self.assertEqual(slugify("a!!!b???c"), "a-b-c")

    def test_mixed_whitespace_and_punct_collapses(self):
        self.assertEqual(slugify("a , , b"), "a-b")

    def test_strips_leading_trailing_hyphens(self):
        self.assertEqual(slugify("  hello  "), "hello")
        self.assertEqual(slugify("!!!hello!!!"), "hello")
        self.assertEqual(slugify("--hello--"), "hello")

    def test_non_alnum_stripped_keeps_hyphen(self):
        self.assertEqual(slugify("foo_bar"), "foo-bar")
        self.assertEqual(slugify("a&b"), "a-b")
        self.assertEqual(slugify("a/b"), "a-b")

    def test_pure_punctuation_returns_empty(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify(",.;:!@#"), "")

    def test_already_slug_unchanged(self):
        self.assertEqual(slugify("hello-world"), "hello-world")

    def test_unicode_lower(self):
        # Strategy: NFKD — Café → cafe (ASCII-safe)
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("ÑOÑO"), "nono")


if __name__ == "__main__":
    unittest.main()
