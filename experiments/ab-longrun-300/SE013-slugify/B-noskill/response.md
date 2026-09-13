# SE013-slugify · B-arm (noskill) RED→GREEN

## Strategy choice (Unicode)

**NFKD + strip combining marks** — `Café` → `cafe`, `ÑOÑO` → `nono` (ASCII-safe slugs).
Not the "lower-only" alternative (`café` → `café`).

## RED — failing tests against original `slugify.py`

Original impl:

```python
def slugify(text: str) -> str:
    # DEFECT: no lower, no strip, collapse broken
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

Command:

```
python -m unittest test_slugify -v
```

RED output:

```
test_already_slug_unchanged ... ok
test_empty_string ... ok
test_hello_world ... FAIL
test_mixed_whitespace_and_punct_collapses ... ok
test_non_alnum_stripped_keeps_hyphen ... ok
test_punctuation_collapses_to_single_hyphen ... ok
test_pure_punctuation_returns_empty ... FAIL
test_strips_leading_trailing_hyphens ... FAIL
test_unicode_lower ... FAIL
test_whitespace_collapses_to_single_hyphen ... ok
======================================================================
FAIL: test_hello_world
AssertionError: 'Hello-World-' != 'hello-world'

FAIL: test_pure_punctuation_returns_empty
AssertionError: '-' != ''

FAIL: test_strips_leading_trailing_hyphens
AssertionError: '-hello-' != 'hello'

FAIL: test_unicode_lower
AssertionError: 'Caf-' != 'cafe'

Ran 10 tests in 0.004s
FAILED (failures=4)
```

## Fix applied to `slugify.py`

- `unicodedata.normalize("NFKD", text)` + drop combining marks
- `.lower()`
- `re.sub(r"[^a-z0-9]+", "-", text)` collapses runs of non-alnum
- `.strip("-")` removes edge hyphens
- early return `""` for empty input

## GREEN — all pass after fix

```
test_already_slug_unchanged ... ok
test_empty_string ... ok
test_hello_world ... ok
test_mixed_whitespace_and_punct_collapses ... ok
test_non_alnum_stripped_keeps_hyphen ... ok
test_punctuation_collapses_to_single_hyphen ... ok
test_pure_punctuation_returns_empty ... ok
test_strips_leading_trailing_hyphens ... ok
test_unicode_lower ... ok
test_whitespace_collapses_to_single_hyphen ... ok
----------------------------------------------------------------------
Ran 10 tests in 0.000s
OK
```

## Acceptance checklist

- [x] 测试文件可跑 (`test_slugify.py`)
- [x] response 含修复前失败 (RED above)
- [x] 修复后通过 (GREEN above)
- [x] 边界：空串、纯标点、首尾符号、多分隔符 — all covered

## 禁止

- 未删失败用例变绿；只改了实现 `slugify.py`，测试先写且未削弱。
