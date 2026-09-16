"""Tests for slugify — written BEFORE the fix (RED phase)."""
import unittest

from slugify import slugify


class TestSlugifySpec(unittest.TestCase):
    def test_basic_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_whitespace_only(self):
        self.assertEqual(slugify("   \t\n  "), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!...???"), "")

    def test_leading_trailing_symbols_stripped(self):
        self.assertEqual(slugify("!!!hello!!!"), "hello")
        self.assertEqual(slugify("--world--"), "world")
        self.assertEqual(slugify("  spaced  "), "spaced")

    def test_collapse_multiple_separators(self):
        self.assertEqual(slugify("a---b"), "a-b")
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a ,. b"), "a-b")
        self.assertEqual(slugify("foo,,,bar...baz"), "foo-bar-baz")

    def test_lowercase(self):
        self.assertEqual(slugify("HELLO"), "hello")
        self.assertEqual(slugify("MiXeD CaSe"), "mixed-case")

    def test_digits_kept(self):
        self.assertEqual(slugify("abc 123"), "abc-123")
        self.assertEqual(slugify("v2.0"), "v2-0")

    def test_already_slug_unchanged(self):
        self.assertEqual(slugify("hello-world"), "hello-world")

    # ---- Unicode strategy: NFKD + strip combining marks (Mn) + lower ----
    # Latin accents fold to ASCII; non-Latin letters (e.g. CJK) are kept.

    def test_unicode_cafe_nfkd(self):
        # Café → NFKD → Cafe + combining acute → strip marks → cafe
        self.assertEqual(slugify("Café"), "cafe")

    def test_unicode_uber_nfkd(self):
        self.assertEqual(slugify("Über cool"), "uber-cool")

    def test_unicode_cjk_kept(self):
        self.assertEqual(slugify("中文 测试"), "中文-测试")

    def test_unicode_mixed_script(self):
        self.assertEqual(slugify("Hello 世界 Café!"), "hello-世界-cafe")

    def test_unicode_ligature(self):
        # ﬁ (U+FB01) NFKD → "fi"
        self.assertEqual(slugify("ﬁle"), "file")

    def test_only_non_alnum_unicode(self):
        self.assertEqual(slugify("——"), "")

    def test_single_word(self):
        self.assertEqual(slugify("Python"), "python")

    def test_newlines_and_tabs(self):
        self.assertEqual(slugify("a\nb\tc"), "a-b-c")


if __name__ == "__main__":
    unittest.main()
