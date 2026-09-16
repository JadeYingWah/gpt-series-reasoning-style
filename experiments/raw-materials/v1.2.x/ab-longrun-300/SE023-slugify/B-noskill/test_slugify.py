# -*- coding: utf-8 -*-
"""Tests for slugify — SE023 RED→GREEN.

Unicode strategy under test: NFKD + drop combining marks + lower.
Café → cafe (ASCII fold), not café.
"""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(slugify(""), "")

    def test_whitespace_only_returns_empty(self):
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify("\t\n"), "")

    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_already_slug(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_digits_kept(self):
        self.assertEqual(slugify("Chapter 12"), "chapter-12")

    def test_whitespace_run_collapses(self):
        self.assertEqual(slugify("a     b"), "a-b")

    def test_punctuation_run_collapses(self):
        self.assertEqual(slugify("a!!!b"), "a-b")

    def test_mixed_whitespace_and_punct_collapses(self):
        self.assertEqual(slugify("a ,.; b"), "a-b")

    def test_leading_trailing_separators_stripped(self):
        self.assertEqual(slugify("  --Hello, World!--  "), "hello-world")

    def test_non_alnum_stripped(self):
        self.assertEqual(slugify("***abc***"), "abc")

    def test_pure_punctuation_or_space(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("   ---   "), "")

    def test_only_one_char(self):
        self.assertEqual(slugify("A"), "a")
        self.assertEqual(slugify("!X!"), "x")

    def test_no_split_inside_alnum_word(self):
        self.assertEqual(slugify("HelloWorld"), "helloworld")

    def test_long_title(self):
        self.assertEqual(
            slugify("The Quick Brown Fox Jumps Over the Lazy Dog"),
            "the-quick-brown-fox-jumps-over-the-lazy-dog",
        )

    def test_unicode_lowercase_applied(self):
        self.assertEqual(slugify("HELLO"), "hello")
        self.assertEqual(slugify("MiXeD"), "mixed")

    def test_unicode_nfkd_accents_fold_to_ascii(self):
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Ünicödé"), "unicode")
        self.assertEqual(slugify("ÉTÉ"), "ete")
        self.assertEqual(slugify("Ångström"), "angstrom")

    def test_hyphen_between_words_preserved_single(self):
        # a - b collapses to single hyphen, not doubled
        self.assertEqual(slugify("a - b"), "a-b")

    def test_underscore_and_symbols_collapse(self):
        self.assertEqual(slugify("foo_bar baz"), "foo-bar-baz")
        self.assertEqual(slugify("v1.2.3"), "v1-2-3")


if __name__ == "__main__":
    unittest.main()
