"""Tests for slugify — RED first, then GREEN after fix.

Unicode strategy: NFKD normalization + strip combining marks (ASCII fold).
  Cafe acute -> cafe
"""
import pytest

from slugify import slugify


class TestSpecExamples:
    def test_hello_world(self):
        assert slugify("Hello, World!") == "hello-world"

    def test_simple_words(self):
        assert slugify("foo bar") == "foo-bar"

    def test_already_slug(self):
        assert slugify("already-a-slug") == "already-a-slug"


class TestCollapse:
    def test_consecutive_spaces(self):
        assert slugify("foo   bar") == "foo-bar"

    def test_mixed_whitespace_and_punct(self):
        assert slugify("foo \t\n,.;:! bar") == "foo-bar"

    def test_multiple_punct(self):
        assert slugify("a!!!b") == "a-b"

    def test_mixed_separators(self):
        assert slugify("a -_- b") == "a-b"


class TestStripEdges:
    def test_leading_punct(self):
        assert slugify("!!!hello") == "hello"

    def test_trailing_punct(self):
        assert slugify("hello!!!") == "hello"

    def test_leading_and_trailing_spaces(self):
        assert slugify("  hello  ") == "hello"

    def test_leading_trailing_hyphens(self):
        assert slugify("-hello-") == "hello"

    def test_only_separators_inside(self):
        assert slugify("a---b") == "a-b"


class TestEmptyAndDegenerate:
    def test_empty_string(self):
        assert slugify("") == ""

    def test_only_spaces(self):
        assert slugify("   ") == ""

    def test_only_punctuation(self):
        assert slugify("!!!") == ""

    def test_only_symbols(self):
        assert slugify("@#$%^&*()") == ""


class TestUnicode:
    def test_cafe_accent(self):
        # NFKD strategy: e-acute -> e
        assert slugify("Café") == "cafe"

    def test_german_ish(self):
        # NFKD: ü -> u; ß is not ASCII-decomposable and is stripped as separator
        assert slugify("Grüße") == "gru-e"

    def test_uppercase_unicode(self):
        assert slugify("CAFÉ") == "cafe"

    def test_digits_preserved(self):
        assert slugify("v2.0 release") == "v2-0-release"


class TestAlnumOnly:
    def test_underscore_stripped(self):
        # underscore is non-alnum except hyphen -> becomes separator
        assert slugify("foo_bar") == "foo-bar"

    def test_keep_digits_and_letters(self):
        assert slugify("abc123") == "abc123"

    def test_single_char(self):
        assert slugify("a") == "a"

    def test_single_punct(self):
        assert slugify("-") == ""
