"""Tests for slugify — run against the current (broken) implementation first."""
import pytest

from slugify import slugify


class TestSpec:
    def test_hello_world(self):
        assert slugify("Hello, World!") == "hello-world"

    def test_collapse_whitespace_and_punct(self):
        assert slugify("a   b") == "a-b"
        assert slugify("a!!!b") == "a-b"
        assert slugify("a  --  b") == "a-b"
        assert slugify("foo   bar!!baz") == "foo-bar-baz"

    def test_strip_leading_trailing_separator(self):
        assert slugify("  --hello--  ") == "hello"
        assert slugify("-start-") == "start"
        assert slugify("!!!end!!!") == "end"

    def test_empty_string(self):
        assert slugify("") == ""

    def test_pure_punctuation(self):
        assert slugify("!!!") == ""
        assert slugify("  ") == ""
        assert slugify("---") == ""

    def test_alphanumeric_preserved(self):
        assert slugify("abc123") == "abc123"
        assert slugify("Version 2.0") == "version-2-0"

    def test_unicode_nfkd_strategy(self):
        """Strategy: NFKD decompose then drop combining marks, then lower.
        Café → cafe (not café).
        """
        assert slugify("Café") == "cafe"
        assert slugify("naïve") == "naive"
        assert slugify("Ünïcödé") == "unicode"


class TestBoundaries:
    def test_single_char(self):
        assert slugify("a") == "a"
        assert slugify("!") == ""

    def test_multiple_separators_between_words(self):
        assert slugify("one---two...three") == "one-two-three"

    def test_leading_digits(self):
        assert slugify("123 abc") == "123-abc"

    def test_underscore_treated_as_separator(self):
        assert slugify("hello_world") == "hello-world"

    def test_already_slug(self):
        assert slugify("already-a-slug") == "already-a-slug"
