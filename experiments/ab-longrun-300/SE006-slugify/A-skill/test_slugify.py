"""Tests for slugify — written before the fix (RED phase)."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_only_punctuation_returns_empty(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("..."), "")
        self.assertEqual(slugify(",.!?;:"), "")

    def test_collapse_whitespace_and_punctuation(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a---b"), "a-b")
        self.assertEqual(slugify("a ,. b"), "a-b")
        self.assertEqual(slugify("foo  bar!!baz"), "foo-bar-baz")

    def test_strip_leading_trailing_separators(self):
        self.assertEqual(slugify("-hello-"), "hello")
        self.assertEqual(slugify("  hello  "), "hello")
        self.assertEqual(slugify("!!hello!!"), "hello")
        self.assertEqual(slugify("--Hello, World!--"), "hello-world")

    def test_alphanumeric_preserved(self):
        self.assertEqual(slugify("abc123"), "abc123")
        self.assertEqual(slugify("a1b2c3"), "a1b2c3")

    def test_hyphen_preserved_inside(self):
        self.assertEqual(slugify("already-slugged"), "already-slugged")

    def test_unicode_nfkd_strategy(self):
        # NFKD strategy: Café -> cafe (diacritics folded, then non-ascii dropped)
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("ÜBER"), "uber")

    def test_mixed_unicode_and_ascii(self):
        self.assertEqual(slugify("Café au Lait!"), "cafe-au-lait")

    def test_numbers_only(self):
        self.assertEqual(slugify("12345"), "12345")


if __name__ == "__main__":
    unittest.main()
