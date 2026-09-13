# Response — SE023-slugify Phase 2 (RED → GREEN)

## Unicode strategy (chosen)

**NFKD + strip combining marks → ASCII slug.**

- Normalize with `unicodedata.normalize("NFKD", text)`
- Drop all combining marks (`unicodedata.combining(ch)` truthy)
- Lowercase, then keep only `[a-z0-9]`, collapse everything else to `-`, strip leading/trailing `-`
- Result: `Café` → `cafe`, `Crème Brûlée` → `creme-brulee`, ` naïve ` → `naive`
- Not chosen: lower-only Unicode-preserving (`café`) — would leave non-ASCII in the slug, which is usually unwanted for URL slugs.

## Defects in the seed `slugify.py`

| Defect | Symptom |
| --- | --- |
| no `.lower()` | `Hello` stays `Hello` |
| no NFKD / deaccent | `Café` → `Caf-` |
| no `strip("-")` | `--Hello--` → `-Hello-` |
| empty / punct-only not special-cased | `!!!` → `-` |

## RED — tests against the original defective seed

Command: `python -m unittest test_slugify -v`

```
test_all_non_alnum_is_separated ... ok
test_collapses_runs_of_separators ... FAIL
test_digits_kept ... FAIL
test_empty_string ... ok
test_hello_world ... FAIL
test_leading_trailing_separators_stripped ... FAIL
test_mixed_case_lowered ... FAIL
test_pure_punctuation ... FAIL
test_underscore_and_other_symbols_become_separators ... FAIL
test_unicode_nfkd_strategy ... FAIL
======================================================================
FAIL: test_hello_world
AssertionError: 'Hello-World-' != 'hello-world'
FAIL: test_leading_trailing_separators_stripped
AssertionError: '-Hello-' != 'hello'
FAIL: test_pure_punctuation
AssertionError: '-' != ''
FAIL: test_unicode_nfkd_strategy
AssertionError: 'Caf-' != 'cafe'
======================================================================
Ran 10 tests
FAILED (failures=8)
```

(8 of 10 failed. Empty-string and `a/b\c` accidentally passed on the seed.)

## Fix — `slugify.py`

```python
def slugify(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    lowered = stripped.lower()
    hyphenated = re.sub(r"[^a-z0-9]+", "-", lowered)
    return hyphenated.strip("-")
```

One test expectation was corrected during GREEN (`hello@world#` → `hello-world`, not `helloworld`) so that non-alnum symbols consistently become separators, matching the `Hello, World!` / `a/b\c` behavior. No failing case was deleted.

## GREEN — after the fix

```
test_all_non_alnum_is_separated ... ok
test_collapses_runs_of_separators ... ok
test_digits_kept ... ok
test_empty_string ... ok
test_hello_world ... ok
test_leading_trailing_separators_stripped ... ok
test_mixed_case_lowered ... ok
test_pure_punctuation ... ok
test_underscore_and_other_symbols_become_separators ... ok
test_unicode_nfkd_strategy ... ok
----------------------------------------------------------------------
Ran 10 tests
OK
```

## Spec coverage checklist

- [x] `slugify("Hello, World!")` → `"hello-world"`
- [x] consecutive whitespace/punctuation collapses to single `-`
- [x] leading/trailing `-` stripped
- [x] non-alnum (except `-`) becomes separator; empty input → `""`
- [x] Unicode: NFKD strategy documented and tested (`Café` → `cafe`)
- [x] edge cases: empty string, pure punctuation, leading/trailing symbols, multi-separators
