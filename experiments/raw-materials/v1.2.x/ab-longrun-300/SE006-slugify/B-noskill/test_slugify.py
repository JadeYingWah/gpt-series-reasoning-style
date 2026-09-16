"""Tests for slugify. RED first against the defective seed."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_collapse_whitespace_and_punctuation(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a,,,b"), "a-b")
        self.assertEqual(slugify("a , b !! c"), "a-b-c")
        self.assertEqual(slugify("  multiple   spaces  --  here  "), "multiple-spaces-here")

    def test_strip_leading_and_trailing_separators(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("!!Hello!!"), "hello")
        self.assertEqual(slugify("  Hello  "), "hello")
        self.assertEqual(slugify("-.-Hello-.-"), "hello")

    def test_empty_and_whitespace_only(self):
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("-"), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("..."), "")
        self.assertEqual(slugify("!!!???"), "")
        self.assertEqual(slugify("___"), "")

    def test_digits_and_mixed(self):
        self.assertEqual(slugify("abc 123"), "abc-123")
        self.assertEqual(slugify("v1.2.3"), "v1-2-3")
        self.assertEqual(slugify("2024-01-01"), "2024-01-01")

    def test_unicode_nfkd_strategy(self):
        """Strategy: NFKD decompose then strip combining marks → Café becomes cafe."""
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Ünïcödé"), "unicode")
        self.assertEqual(slugify("résumé"), "resume")

    def test_unicode_letters_with_no_combining_decomposition(self):
        """Letters that survive NFKD as non-ASCII are kept if alphanumeric."""
        # Chinese characters are alphanumeric after NFKD; keep them lowercased.
        self.assertEqual(slugify("你好世界"), "你好世界")
        self.assertEqual(slugify("Hello 世界"), "hello-世界")

    def test_already_slug(self):
        self.assertEqual(slugify("hello-world"), "hello-world")
        self.assertEqual(slugify("hello"), "hello")

    def test_mixed_case_collapses_to_lower(self):
        self.assertEqual(slugify("HeLLo WoRLD"), "hello-world")


if __name__ == "__main__":
    unittest.main()
