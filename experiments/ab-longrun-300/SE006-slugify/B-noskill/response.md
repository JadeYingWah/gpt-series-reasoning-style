# SE006-slugify · RED → GREEN

## Unicode strategy (chosen)

**NFKD decomposition + strip combining marks**, then keep alphanumeric Unicode (via `str.isalnum`), lowercase, non-alnum → `-`.

Rationale: ASCII-friendly slugs (`Café` → `cafe`) while still preserving scripts that have no ASCII fold (`你好世界` stays). Documented and tested in `test_unicode_nfkd_strategy` and `test_unicode_letters_with_no_combining_decomposition`.

## RED (before fix)

Command: `python -m unittest test_slugify -v`

```
test_already_slug (test_slugify.TestSlugify.test_already_slug) ... ok
test_basic_hello_world (test_slugify.TestSlugify.test_basic_hello_world) ... FAIL
test_collapse_whitespace_and_punctuation (test_slugify.TestSlugify.test_collapse_whitespace_and_punctuation) ... FAIL
test_digits_and_mixed (test_slugify.TestSlugify.test_digits_and_mixed) ... ok
test_empty_and_whitespace_only (test_slugify.TestSlugify.test_empty_and_whitespace_only) ... FAIL
test_mixed_case_collapses_to_lower (test_slugify.TestSlugify.test_mixed_case_collapses_to_lower) ... FAIL
test_pure_punctuation (test_slugify.TestSlugify.test_pure_punctuation) ... FAIL
test_strip_leading_and_trailing_separators (test_slugify.TestSlugify.test_strip_leading_and_trailing_separators) ... FAIL
test_unicode_letters_with_no_combining_decomposition (test_slugify.TestSlugify.test_unicode_letters_with_no_combining_decomposition) ... FAIL
test_unicode_nfkd_strategy (test_slugify.TestSlugify.test_unicode_nfkd_strategy) ... FAIL
======================================================================
FAIL: test_basic_hello_world
AssertionError: 'Hello-World-' != 'hello-world'

FAIL: test_collapse_whitespace_and_punctuation
AssertionError: '-multiple-spaces-here-' != 'multiple-spaces-here'

FAIL: test_empty_and_whitespace_only
AssertionError: '-' != ''

FAIL: test_mixed_case_collapses_to_lower
AssertionError: 'HeLLo-WoRLD' != 'hello-world'

FAIL: test_pure_punctuation
AssertionError: '-' != ''

FAIL: test_strip_leading_and_trailing_separators
AssertionError: '-Hello-' != 'hello'

FAIL: test_unicode_letters_with_no_combining_decomposition
AssertionError: '-' != '你好世界'

FAIL: test_unicode_nfkd_strategy
AssertionError: 'Caf-' != 'cafe'
----------------------------------------------------------------------
Ran 10 tests in 0.003s
FAILED (failures=8)
```

Defects in seed `slugify.py`:
1. No `.lower()`
2. No strip of leading/trailing `-`
3. ASCII-only character class (`[a-zA-Z0-9]`) drops all non-ASCII, including NFKD-foldable accents and CJK
4. Pure-punctuation / whitespace-only inputs become `"-"` instead of `""`

## Fix

Rewrote `slugify.py`:
- NFKD normalize → drop combining marks (`Mn`)
- lowercase
- replace runs of non-alphanumeric with `-`
- strip leading/trailing `-`

## GREEN (after fix)

Command: `python -m unittest test_slugify -v`

```
test_already_slug (test_slugify.TestSlugify.test_already_slug) ... ok
test_basic_hello_world (test_slugify.TestSlugify.test_basic_hello_world) ... ok
test_collapse_whitespace_and_punctuation (test_slugify.TestSlugify.test_collapse_whitespace_and_punctuation) ... ok
test_digits_and_mixed (test_slugify.TestSlugify.test_digits_and_mixed) ... ok
test_empty_and_whitespace_only (test_slugify.TestSlugify.test_empty_and_whitespace_only) ... ok
test_mixed_case_collapses_to_lower (test_slugify.TestSlugify.test_mixed_case_collapses_to_lower) ... ok
test_pure_punctuation (test_slugify.TestSlugify.test_pure_punctuation) ... ok
test_strip_leading_and_trailing_separators (test_slugify.TestSlugify.test_strip_leading_and_trailing_separators) ... ok
test_unicode_letters_with_no_combining_decomposition (test_slugify.TestSlugify.test_unicode_letters_with_no_combining_decomposition) ... ok
test_unicode_nfkd_strategy (test_slugify.TestSlugify.test_unicode_nfkd_strategy) ... ok
----------------------------------------------------------------------
Ran 10 tests in 0.000s
OK
```

## Acceptance checklist

- [x] 测试文件可跑 — `test_slugify.py` via unittest
- [x] response 含修复前失败 — RED section above (8 failures)
- [x] 修复后通过 — GREEN section above (10/10)
- [x] 边界：空串、纯标点、首尾符号、多分隔符 — covered by dedicated test methods
