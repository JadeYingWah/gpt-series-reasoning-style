# SE003-slugify · B-noskill · RED → GREEN

## Unicode strategy (notes)

**NFKD fold**: `unicodedata.normalize("NFKD", …)` then drop combining marks, keep ASCII.
`Café` → `cafe`, `Ünïcödé` → `unicode`. Documented in `slugify.py` and asserted in `test_unicode_nfkd_fold`.

## Defects in seed

- no lowercasing
- no strip of leading/trailing `-`
- pure punctuation produced `"-"` instead of `""`
- no Unicode decomposition (accents became stray `-`)

## RED (before fix)

```
$ python -m unittest test_slugify -v
...
FAIL: test_basic_sentence
AssertionError: 'Hello-World-' != 'hello-world'
FAIL: test_consecutive_whitespace_and_punct_collapse
AssertionError: 'a-b-' != 'a-b'
FAIL: test_empty_and_pure_punct
AssertionError: '-' != ''
FAIL: test_mixed_case_lowered
AssertionError: 'MiXeD-CaSe' != 'mixed-case'
FAIL: test_strip_leading_trailing_hyphens
AssertionError: '-Hello-' != 'hello'
FAIL: test_unicode_nfkd_fold
AssertionError: 'Caf-' != 'cafe'
----------------------------------------------------------------------
Ran 8 tests in 0.005s
FAILED (failures=6)
```

(2 of 8 passed on the broken seed: `test_alphanumeric_and_hyphen_passthrough`, `test_already_slug`.)

## Fix

Rewrote `slugify.py`: NFKD → strip combining → collapse non-alnum to `-` → strip edge `-` → `.lower()`.
No test cases were removed or weakened.

## GREEN (after fix)

```
$ python -m unittest test_slugify -v
test_alphanumeric_and_hyphen_passthrough ... ok
test_already_slug ... ok
test_basic_sentence ... ok
test_consecutive_whitespace_and_punct_collapse ... ok
test_empty_and_pure_punct ... ok
test_mixed_case_lowered ... ok
test_strip_leading_trailing_hyphens ... ok
test_unicode_nfkd_fold ... ok
----------------------------------------------------------------------
Ran 8 tests in 0.001s
OK
```

## Acceptance checklist

- [x] 测试文件可跑 (`test_slugify.py`, unittest)
- [x] response 含修复前失败 (RED above)
- [x] 修复后通过 (GREEN: 8/8)
- [x] 边界：空串、纯标点、首尾符号、多分隔符
