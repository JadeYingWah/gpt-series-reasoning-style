"""Tests for slugify — written to encode the full spec (RED first)."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_collapse_whitespace(self):
        self.assertEqual(slugify("a   b\tc\nd"), "a-b-c-d")

    def test_collapse_punctuation_and_separators(self):
        self.assertEqual(slugify("a,,--__b"), "a-b")
        self.assertEqual(slugify("foo!!!bar"), "foo-bar")
        self.assertEqual(slugify("a + b = c"), "a-b-c")

    def test_strip_leading_trailing_separators(self):
        self.assertEqual(slugify("  --Hello World--  "), "hello-world")
        self.assertEqual(slugify("!!!Hello!!!"), "hello")
        self.assertEqual(slugify("_under_score_"), "under-score")

    def test_pure_punctuation_returns_empty(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("---"), "")
        self.assertEqual(slugify(" \t\n "), "")
        self.assertEqual(slugify(".,;:!?"), "")

    def test_non_alnum_stripped_except_hyphen(self):
        self.assertEqual(slugify("a$b#c"), "a-b-c")
        self.assertEqual(slugify("user@email.com"), "user-email-com")
        self.assertEqual(slugify("path/to/file"), "path-to-file")

    def test_digits_preserved(self):
        self.assertEqual(slugify("abc 123"), "abc-123")
        self.assertEqual(slugify("v2.0 release"), "v2-0-release")

    def test_unicode_nfkd_strategy(self):
        # Strategy: NFKD normalize then drop combining marks → ASCII-ish slug
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Ünïcödé"), "unicode")
        self.assertEqual(slugify("ÉTÉ"), "ete")

    def test_mixed_realistic_title(self):
        self.assertEqual(
            slugify("The Quick Brown Fox Jumps Over the Lazy Dog!"),
            "the-quick-brown-fox-jumps-over-the-lazy-dog",
        )

    def test_already_slugified(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_only_letters_no_split(self):
        self.assertEqual(slugify("HelloWorld"), "helloworld")


if __name__ == "__main__":
    unittest.main()
