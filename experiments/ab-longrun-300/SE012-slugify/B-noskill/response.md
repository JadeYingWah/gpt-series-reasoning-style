# SE012-slugify · RED → GREEN

## Unicode policy (chosen)

**NFKD**: decompose characters, drop combining marks, then lower-case.
- `Café` → `cafe`
- `naïve` → `naive`
- `Ünïcödé` → `unicode`

(Alternative would be lower-only, yielding `café`; NFKD chosen for URL-safe ASCII slugs.)

## RED (before fix)

Initial `slugify.py` defects: no lowercasing, no leading/trailing strip, Unicode letters dropped entirely, pure punctuation left as `-`.

```
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0
collected 10 items

test_slugify.py::test_basic_hello_world FAILED
test_slugify.py::test_lowercase FAILED
test_slugify.py::test_collapses_runs_to_single_dash PASSED
test_slugify.py::test_strips_leading_and_trailing_separators FAILED
test_slugify.py::test_empty_string PASSED
test_slugify.py::test_only_punctuation_or_whitespace FAILED
test_slugify.py::test_keeps_alphanumeric_and_hyphen PASSED
test_slugify.py::test_strips_non_alnum_except_hyphen PASSED
test_slugify.py::test_unicode_nfkd_policy FAILED
test_slugify.py::test_multiple_separators_and_mixed_content FAILED

6 failed, 4 passed
```

Representative failures:
- `slugify("Hello, World!")` → `'Hello-World-'` (expected `'hello-world'`)
- `slugify("---Hello---")` → `'-Hello-'` (expected `'hello'`)
- `slugify("!!!")` → `'-'` (expected `''`)
- `slugify("Café")` → `'Caf-'` (expected `'cafe'`)

## Fix

Rewrote `slugify.py`:
1. Early-return `""` for empty input
2. `unicodedata.normalize("NFKD", …)` + strip combining marks
3. `.lower()`
4. `re.sub(r"[^a-z0-9]+", "-", …)` — collapse runs of non-alnum
5. `.strip("-")`

## GREEN (after fix)

```
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0
collected 10 items

test_slugify.py::test_basic_hello_world PASSED
test_slugify.py::test_lowercase PASSED
test_slugify.py::test_collapses_runs_to_single_dash PASSED
test_slugify.py::test_strips_leading_and_trailing_separators PASSED
test_slugify.py::test_empty_string PASSED
test_slugify.py::test_only_punctuation_or_whitespace PASSED
test_slugify.py::test_keeps_alphanumeric_and_hyphen PASSED
test_slugify.py::test_strips_non_alnum_except_hyphen PASSED
test_slugify.py::test_unicode_nfkd_policy PASSED
test_slugify.py::test_multiple_separators_and_mixed_content PASSED

10 passed
```

## Acceptance checklist

- [x] Test file runnable (`python -m pytest test_slugify.py`)
- [x] response contains pre-fix failures
- [x] Post-fix all pass
- [x] Boundaries covered: empty string, pure punctuation, leading/trailing symbols, multi-separator runs

## Notes

- No failing tests were removed or weakened; only `slugify.py` was fixed after the RED run.
