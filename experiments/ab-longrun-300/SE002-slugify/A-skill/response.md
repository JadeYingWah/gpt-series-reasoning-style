# Response — SE002-slugify

## Unicode strategy (chosen)

**NFKD + strip combining marks + lower.**

`unicodedata.normalize("NFKD", text)` decomposes accented letters into base + combining mark
(e.g. `é` → `e` + U+0301), then combining marks are dropped. Result is ASCII-safe slugs:

| input | output |
|---|---|
| `Café` | `cafe` |
| `naïve café` | `naive-cafe` |
| `ÅNGSTRÖM` | `angstrom` |

The alternative (only `lower()`, keep `café`) was rejected: NFKD matches common slug libraries
(python-slugify, Django) and produces more portable URL tokens.

## RED — failing run against original `slugify.py`

Original defect seed:

```python
def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

Missing: lower, edge-strip, Unicode handling. Collapse regex was correct in isolation.

```
$ python -m unittest test_slugify -v
test_basic_phrase ... FAIL
  AssertionError: 'Hello-World-' != 'hello-world'
test_collapse_multiple_separators ... ok
test_digits_kept ... FAIL
  AssertionError: 'Chapter-42' != 'chapter-42'
test_empty_string ... ok
test_leading_trailing_symbols_stripped ... FAIL
  AssertionError: '-Hello-' != 'hello'
test_preserves_existing_hyphen_between_words ... ok
test_pure_punctuation ... FAIL
  AssertionError: '-' != ''
test_unicode_nfkd ... FAIL
  AssertionError: 'Caf-' != 'cafe'
test_unicode_nfkd_empty_after_decomposition ... FAIL
  AssertionError: '-' != ''

Ran 9 tests in 0.003s
FAILED (failures=6)
```

**RED: 6 failed, 3 passed.** No test was deleted or weakened.

## Fix

Rewrote `slugify.py`:

1. NFKD normalize + drop combining marks → ASCII base letters
2. `.lower()`
3. `re.sub(r"[^a-z0-9]+", "-", s)` collapse runs of non-alnum to single `-`
4. `.strip("-")` remove leading/trailing separators
5. Guard empty/`None`-ish early return of `""`

## GREEN — passing run after fix

```
$ python -m unittest test_slugify -v
test_basic_phrase ... ok
test_collapse_multiple_separators ... ok
test_digits_kept ... ok
test_empty_string ... ok
test_leading_trailing_symbols_stripped ... ok
test_preserves_existing_hyphen_between_words ... ok
test_pure_punctuation ... ok
test_unicode_nfkd ... ok
test_unicode_nfkd_empty_after_decomposition ... ok

Ran 9 tests in 0.000s
OK
```

**GREEN: 9 passed, 0 failed.**

## Acceptance checklist

- [x] test file runnable (`python -m unittest test_slugify -v`)
- [x] response contains pre-fix failures (RED above)
- [x] post-fix all pass (GREEN above)
- [x] edges covered: empty string, pure punctuation, leading/trailing symbols, multi-separators, Unicode
