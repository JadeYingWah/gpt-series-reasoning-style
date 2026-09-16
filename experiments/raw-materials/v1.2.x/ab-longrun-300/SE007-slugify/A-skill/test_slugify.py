"""Tests for slugify — written BEFORE the fix (RED)."""
import unittest

from slugify import slugify


class TestSlugifyBasic(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_already_slug(self):
        self.assertEqual(slugify("hello-world"), "hello-world")

    def test_leading_trailing_whitespace(self):
        self.assertEqual(slugify("  hello  "), "hello")

    def test_leading_trailing_punctuation(self):
        self.assertEqual(slugify("!!hello!!"), "hello")

    def test_leading_trailing_hyphen(self):
        self.assertEqual(slugify("--hello--"), "hello")


class TestSlugifyCollapse(unittest.TestCase):
    def test_multiple_spaces(self):
        self.assertEqual(slugify("hello   world"), "hello-world")

    def test_mixed_whitespace_and_punct(self):
        self.assertEqual(slugify("hello,   world!"), "hello-world")

    def test_mixed_separators(self):
        self.assertEqual(slugify("a  ,  b"), "a-b")

    def test_only_punctuation(self):
        self.assertEqual(slugify("!!!...???"), "")

    def test_only_whitespace(self):
        self.assertEqual(slugify("   \t\n  "), "")

    def test_mixed_case_lowered(self):
        self.assertEqual(slugify("FooBar BAZ"), "foobar-baz")

    def test_numbers_kept(self):
        self.assertEqual(slugify("v1.2.3 release"), "v1-2-3-release")

    def test_underscores_stripped_to_sep(self):
        self.assertEqual(slugify("hello_world"), "hello-world")


class TestSlugifyUnicode(unittest.TestCase):
    """Strategy: NFKD normalize, strip combining marks, keep [a-z0-9].

    Café → cafe (decomposed é → e + combining acute → e).
    """

    def test_cafe_nfd(self):
        self.assertEqual(slugify("Café"), "cafe")

    def test_nfd_form(self):
        self.assertEqual(slugify("Cafe\u0301"), "cafe")

    def test_german_umlaut(self):
        # ü → u after NFKD strip of diaeresis
        self.assertEqual(slugify("über"), "uber")

    def test_chinese_stripped(self):
        # CJK has no NFKD ascii fold — non-alnum becomes separator
        self.assertEqual(slugify("你好 世界"), "")

    def test_mixed_latin_cjk(self):
        self.assertEqual(slugify("Hello 世界 World"), "hello-world")


if __name__ == "__main__":
    unittest.main()
