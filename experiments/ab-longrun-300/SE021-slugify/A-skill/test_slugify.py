"""Tests for slugify — SE021.

Unicode strategy: NFKD normalize + strip combining marks.
'Café' -> 'cafe' (not 'café').
"""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_lowercase(self):
        self.assertEqual(slugify("HELLO"), "hello")
        self.assertEqual(slugify("MiXeD"), "mixed")

    def test_collapses_whitespace_and_punct_to_single_dash(self):
        self.assertEqual(slugify("foo   bar"), "foo-bar")
        self.assertEqual(slugify("foo, bar"), "foo-bar")
        self.assertEqual(slugify("foo---bar"), "foo-bar")
        self.assertEqual(slugify("foo !@# bar"), "foo-bar")
        self.assertEqual(slugify("  Foo  Bar  "), "foo-bar")

    def test_strips_leading_trailing_dashes(self):
        self.assertEqual(slugify("  Hello World  "), "hello-world")
        self.assertEqual(slugify("--hello--"), "hello")
        self.assertEqual(slugify("!!!hello!!!"), "hello")

    def test_pure_punct_or_whitespace_returns_empty(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify("---"), "")
        self.assertEqual(slugify(" !@#$%^&*() "), "")

    def test_keeps_digits(self):
        self.assertEqual(slugify("abc 123"), "abc-123")
        self.assertEqual(slugify("v2.0"), "v2-0")

    def test_unicode_nfkd_deaccent(self):
        # Strategy: NFKD + strip combining marks -> ASCII base letters
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Ångström"), "angstrom")
        self.assertEqual(slugify("Ünïcödé"), "unicode")

    def test_unicode_letters_without_decomposable_accent(self):
        # Letters that NFKD cannot fold to ASCII stay (lowercased)
        self.assertEqual(slugify("中文"), "中文")
        self.assertEqual(slugify("ЖЖЖ"), "жжж")
        self.assertEqual(slugify("日本語"), "日本語")

    def test_mixed_unicode_and_ascii(self):
        self.assertEqual(slugify("Café au Lait!"), "cafe-au-lait")
        self.assertEqual(slugify("Résumé Builder"), "resume-builder")

    def test_non_alnum_stripped_except_dash(self):
        self.assertEqual(slugify("a_b"), "ab")
        self.assertEqual(slugify("a.b"), "a-b")
        self.assertEqual(slugify("a+b"), "a-b")


if __name__ == "__main__":
    unittest.main()
