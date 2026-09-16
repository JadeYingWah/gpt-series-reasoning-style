"""Tests for slugify — written against the spec before the fix (RED)."""
import pytest

from slugify import slugify


def test_basic_hello_world():
    assert slugify("Hello, World!") == "hello-world"


def test_lowercase():
    assert slugify("UPPER Case") == "upper-case"


def test_collapses_runs_to_single_dash():
    assert slugify("a   b") == "a-b"
    assert slugify("a!!!b") == "a-b"
    assert slugify("a ,. b") == "a-b"
    assert slugify("a--b") == "a-b"


def test_strips_leading_and_trailing_separators():
    assert slugify("---Hello---") == "hello"
    assert slugify("  Hello  ") == "hello"
    assert slugify("!!!Hello!!!") == "hello"


def test_empty_string():
    assert slugify("") == ""


def test_only_punctuation_or_whitespace():
    assert slugify("!!!") == ""
    assert slugify("   ") == ""
    assert slugify("---") == ""


def test_keeps_alphanumeric_and_hyphen():
    assert slugify("foo-bar_42") == "foo-bar-42"
    assert slugify("abc123") == "abc123"


def test_strips_non_alnum_except_hyphen():
    assert slugify("a@b#c") == "a-b-c"
    assert slugify("path/to/file.txt") == "path-to-file-txt"


def test_unicode_nfkd_policy():
    """Strategy: NFKD — decompose then drop combining marks.

    Café -> cafe (not café, not caf)
    naïve -> naive
    """
    assert slugify("Café") == "cafe"
    assert slugify("naïve") == "naive"
    assert slugify("Ünïcödé") == "unicode"


def test_multiple_separators_and_mixed_content():
    assert slugify("  --Hello,   World!---  ") == "hello-world"
    assert slugify("a1!!b2__c3") == "a1-b2-c3"
