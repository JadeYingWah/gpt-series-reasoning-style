"""Tests for slugify — full spec, including documented Unicode strategy.

Strategy under test: NFKD + drop combining marks (accents → ASCII base).
"""
import unittest

from slugify import slugify


class TestSlugifySpec(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_input(self):
        self.assertEqual(slugify(""), "")

    def test_whitespace_run_collapses(self):
        self.assertEqual(slugify("one   two\tthree\nfour"), "one-two-three-four")

    def test_punctuation_run_collapses(self):
        self.assertEqual(slugify("a,,!!b"), "a-b")
        self.assertEqual(slugify("foo---bar"), "foo-bar")
        self.assertEqual(slugify("x__y..z"), "x-y-z")

    def test_mixed_whitespace_and_punct_collapses(self):
        self.assertEqual(slugify("a ,. !! b"), "a-b")

    def test_leading_trailing_separators_stripped(self):
        self.assertEqual(slugify("  --Hello World--  "), "hello-world")
        self.assertEqual(slugify("!!!lead and trail!!!"), "lead-and-trail")
        self.assertEqual(slugify("-already-wrapped-"), "already-wrapped")

    def test_pure_punctuation_or_space(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("---"), "")
        self.assertEqual(slugify(" \t\n "), "")
        self.assertEqual(slugify(".,;:!?"), "")

    def test_non_alnum_stripped(self):
        self.assertEqual(slugify("a$b#c"), "a-b-c")
        self.assertEqual(slugify("user@email.com"), "user-email-com")
        self.assertEqual(slugify("path/to/file"), "path-to-file")
        self.assertEqual(slugify("50% off"), "50-off")

    def test_digits_kept(self):
        self.assertEqual(slugify("abc 123"), "abc-123")
        self.assertEqual(slugify("v2.0"), "v2-0")
        self.assertEqual(slugify("2024-01-02"), "2024-01-02")

    def test_unicode_nfkd_accents_fold_to_ascii(self):
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Ünïcödé"), "unicode")
        self.assertEqual(slugify("ÉTÉ"), "ete")
        self.assertEqual(slugify("Ångström"), "angstrom")

    def test_unicode_lowercase_applied(self):
        self.assertEqual(slugify("HELLO"), "hello")
        self.assertEqual(slugify("MiXeD"), "mixed")

    def test_already_slug(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_no_split_inside_alnum_word(self):
        self.assertEqual(slugify("HelloWorld"), "helloworld")
        self.assertEqual(slugify("snake_case"), "snake-case")

    def test_long_title(self):
        self.assertEqual(
            slugify("The Quick Brown Fox Jumps Over the Lazy Dog!"),
            "the-quick-brown-fox-jumps-over-the-lazy-dog",
        )

    def test_only_one_char(self):
        self.assertEqual(slugify("A"), "a")
        self.assertEqual(slugify("!"), "")
        self.assertEqual(slugify("1"), "1")


if __name__ == "__main__":
    unittest.main()
