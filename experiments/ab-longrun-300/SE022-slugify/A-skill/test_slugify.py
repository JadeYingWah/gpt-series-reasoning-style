"""Tests for slugify — TDD RED then GREEN."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_lowercases(self):
        self.assertEqual(slugify("Hello"), "hello")
        self.assertEqual(slugify("HELLO WORLD"), "hello-world")

    def test_collapses_whitespace_and_punct(self):
        self.assertEqual(slugify("a  b!!c"), "a-b-c")
        self.assertEqual(slugify("a, b, c"), "a-b-c")
        self.assertEqual(slugify("a --- b"), "a-b")

    def test_strips_leading_trailing_separators(self):
        self.assertEqual(slugify("--hello--"), "hello")
        self.assertEqual(slugify("  --Hello,   World!--  "), "hello-world")
        self.assertEqual(slugify("-a-"), "a")

    def test_strips_non_alnum(self):
        self.assertEqual(slugify("hello@world!"), "hello-world")
        self.assertEqual(slugify("foo/bar\\baz"), "foo-bar-baz")

    def test_empty_input(self):
        self.assertEqual(slugify(""), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("---"), "")
        self.assertEqual(slugify(" ,.; "), "")

    def test_numbers_kept(self):
        self.assertEqual(slugify("hello 123 world"), "hello-123-world")
        self.assertEqual(slugify("v2.0.1"), "v2-0-1")

    def test_unicode_nfkd_deaccent(self):
        # Strategy: NFKD + drop combining marks → Café → cafe
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("ÜBER"), "uber")
        self.assertEqual(slugify("résumé"), "resume")

    def test_unicode_letters_retained_when_no_deaccent_needed(self):
        self.assertEqual(slugify("日本語"), "日本語")
        self.assertEqual(slugify("Москва"), "москва")

    def test_multiple_separators_between_words(self):
        self.assertEqual(slugify("one--two___three"), "one-two-three")
        self.assertEqual(slugify("a...b...c"), "a-b-c")


if __name__ == "__main__":
    unittest.main()
