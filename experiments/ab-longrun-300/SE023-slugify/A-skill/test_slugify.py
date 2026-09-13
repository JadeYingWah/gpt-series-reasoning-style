"""Tests for slugify — written before the implementation fix (TDD RED phase)."""
import unittest

from slugify import slugify


class TestSlugifySpec(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("---"), "")
        self.assertEqual(slugify(" .,;: "), "")

    def test_leading_trailing_separators_stripped(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("!!Hello!!"), "hello")
        self.assertEqual(slugify("  Hello  "), "hello")

    def test_collapses_runs_of_separators(self):
        self.assertEqual(slugify("Hello   World"), "hello-world")
        self.assertEqual(slugify("Hello,,,World"), "hello-world")
        self.assertEqual(slugify("Hello - World"), "hello-world")
        self.assertEqual(slugify("a  --  b"), "a-b")

    def test_mixed_case_lowered(self):
        self.assertEqual(slugify("HelloWorld"), "helloworld")
        self.assertEqual(slugify("ABC"), "abc")

    def test_digits_kept(self):
        self.assertEqual(slugify("v1.2.3"), "v1-2-3")
        self.assertEqual(slugify("2024 Year"), "2024-year")

    def test_underscore_and_other_symbols_become_separators(self):
        self.assertEqual(slugify("hello_world"), "hello-world")
        self.assertEqual(slugify("hello@world#"), "hello-world")

    def test_unicode_nfkd_strategy(self):
        # Strategy: NFKD + strip combining marks → ASCII slug.
        # Café → cafe (not café). Documented in response.md.
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("Crème Brûlée"), "creme-brulee")
        self.assertEqual(slugify(" naïve "), "naive")

    def test_all_non_alnum_is_separated(self):
        self.assertEqual(slugify("a/b\\c"), "a-b-c")


if __name__ == "__main__":
    unittest.main()
