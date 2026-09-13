# SE014-slugify · B-noskill · RED → GREEN

## Unicode strategy (notes)

**NFKD ASCII-fold**: `unicodedata.normalize("NFKD", …)` then drop combining
marks before lowercasing. Accented Latin letters collapse to their ASCII
base:

| input  | output | why                    |
|--------|--------|------------------------|
| Café   | cafe   | é → e + U+0301, strip  |
| Über   | uber   | Ü → U + umlaut, strip  |
| naïve  | naive  | ï → i                  |

Letters with no NFKD base (e.g. CJK) are retained after `.lower()` and
treated as "alphanumeric" only if they match `\w` after the fold — the
implementation currently keeps only `[a-z0-9]` after folding, so CJK is
replaced by `-`. This is intentional for URL-safety and documented here.

---

## RED — before fix

Command: `python -m unittest test_slugify -v`

```
test_already_slug (test_slugify.TestSlugify.test_already_slug) ... ok
test_collapse_whitespace_and_punct (test_slugify.TestSlugify.test_collapse_whitespace_and_punct) ... ok
test_digits (test_slugify.TestSlugify.test_digits) ... FAIL
test_empty_and_whitespace_only (test_slugify.TestSlugify.test_empty_and_whitespace_only) ... FAIL
test_hello_world (test_slugify.TestSlugify.test_hello_world) ... FAIL
test_leading_trailing_symbols (test_slugify.TestSlugify.test_leading_trailing_symbols) ... FAIL
test_multiple_separators_collapse_to_one (test_slugify.TestSlugify.test_multiple_separators_collapse_to_one) ... ok
test_non_alnum_stripped_except_hyphen (test_slugify.TestSlugify.test_non_alnum_stripped_except_hyphen) ... ok
test_pure_punctuation (test_slugify.TestSlugify.test_pure_punctuation) ... FAIL
test_strip_leading_trailing_hyphens (test_slugify.TestSlugify.test_strip_leading_trailing_hyphens) ... FAIL
test_unicode_lower (test_slugify.TestSlugify.test_unicode_lower) ... FAIL
======================================================================
FAIL: test_digits
  AssertionError: 'Chapter-12' != 'chapter-12'
FAIL: test_empty_and_whitespace_only
  AssertionError: '-' != ''
FAIL: test_hello_world
  AssertionError: 'Hello-World-' != 'hello-world'
FAIL: test_leading_trailing_symbols
  AssertionError: '-abc-' != 'abc'
FAIL: test_pure_punctuation
  AssertionError: '-' != ''
FAIL: test_strip_leading_trailing_hyphens
  AssertionError: '-Hello-' != 'hello'
FAIL: test_unicode_lower
  AssertionError: 'Caf-' != 'cafe'
======================================================================
Ran 11 tests in 0.004s
FAILED (failures=7)
```

**7 failures.** Root causes of the seed:

1. No `.lower()` → `Chapter-12`, `Hello-World-`
2. No `strip("-")` → leading/trailing hyphens remain
3. Empty / pure-punct input collapses to `"-"` instead of `""`
4. No NFKD fold → `Café` becomes `Caf-` (é dropped by ASCII-only regex)
5. Trailing `!` in `"Hello, World!"` produced a trailing `-`

---

## Fix applied

`slugify.py` rewritten (no tests deleted, no test-only edits):

```python
def slugify(text: str) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s
```

Pipeline: NFKD → drop combining → lower → collapse non-alnum to `-` →
strip edge hyphens.

---

## GREEN — after fix

Command: `python -m unittest test_slugify -v`

```
test_already_slug (test_slugify.TestSlugify.test_already_slug) ... ok
test_collapse_whitespace_and_punct (test_slugify.TestSlugify.test_collapse_whitespace_and_punct) ... ok
test_digits (test_slugify.TestSlugify.test_digits) ... ok
test_empty_and_whitespace_only (test_slugify.TestSlugify.test_empty_and_whitespace_only) ... ok
test_hello_world (test_slugify.TestSlugify.test_hello_world) ... ok
test_leading_trailing_symbols (test_slugify.TestSlugify.test_leading_trailing_symbols) ... ok
test_multiple_separators_collapse_to_one (test_slugify.TestSlugify.test_multiple_separators_collapse_to_one) ... ok
test_non_alnum_stripped_except_hyphen (test_slugify.TestSlugify.test_non_alnum_stripped_except_hyphen) ... ok
test_pure_punctuation (test_slugify.TestSlugify.test_pure_punctuation) ... ok
test_strip_leading_trailing_hyphens (test_slugify.TestSlugify.test_strip_leading_trailing_hyphens) ... ok
test_unicode_lower (test_slugify.TestSlugify.test_unicode_lower) ... ok
----------------------------------------------------------------------
Ran 11 tests in 0.001s

OK
```

---

## Acceptance checklist

- [x] Test file runs
- [x] Response contains pre-fix failures
- [x] Post-fix all pass
- [x] Edge cases covered: empty string, pure punctuation, leading/trailing symbols, multi-separator collapse
- [x] No failing cases deleted; only implementation fixed
