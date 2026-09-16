import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_collapse_whitespace_and_punctuation(self):
        self.assertEqual(slugify("a   b...c!!d"), "a-b-c-d")
        self.assertEqual(slugify("foo -- bar"), "foo-bar")

    def test_strip_leading_and_trailing_separators(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("!!!spam!!!"), "spam")
        self.assertEqual(slugify("  padded  "), "padded")

    def test_non_alnum_stripped_except_hyphen(self):
        self.assertEqual(slugify("a_b#c"), "a-b-c")
        self.assertEqual(slugify("keep-me"), "keep-me")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_only_punctuation_returns_empty(self):
        self.assertEqual(slugify("!!!...???"), "")
        self.assertEqual(slugify("---"), "")
        self.assertEqual(slugify("   "), "")

    def test_already_slug(self):
        self.assertEqual(slugify("simple-slug"), "simple-slug")

    def test_unicode_nfkd_strategy(self):
        """NFKD strategy: accents decomposed and stripped → ascii-safe slug."""
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Ünïcödé"), "unicode")


if __name__ == "__main__":
    unittest.main()
