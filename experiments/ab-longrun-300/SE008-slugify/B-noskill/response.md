# response.md — SE008-slugify B-arm

## Strategy notes (Unicode)

**Chosen policy: NFKD + strip combining marks + ASCII fold.**

- `Café` → NFKD → `Cafe` + combining acute → drop mark → `Cafe` → `cafe`
- `Ñoño` → `nono`
- Rationale: URLs/slugs are safest as pure ASCII; matches common slugify libraries (e.g. Python `python-slugify` default, Django `slugify` with allow_unicode=False).
- Alternative rejected: keep Unicode letters (`café`) — works for some stacks but worse portability.

## RED output (before fix)

Command: `python -m pytest test_slugify.py -v`

```
collected 10 items

test_slugify.py::TestSlugify::test_already_slug PASSED                   [ 10%]
test_slugify.py::TestSlugify::test_collapse_whitespace_and_punctuation PASSED [ 20%]
test_slugify.py::TestSlugify::test_empty_string PASSED                   [ 30%]
test_slugify.py::TestSlugify::test_hello_world FAILED                    [ 40%]
test_slugify.py::TestSlugify::test_non_alnum_stripped PASSED             [ 50%]
test_slugify.py::TestSlugify::test_numbers_preserved FAILED              [ 60%]
test_slugify.py::TestSlugify::test_pure_punctuation FAILED               [ 70%]
test_slugify.py::TestSlugify::test_single_word FAILED                    [ 80%]
test_slugify.py::TestSlugify::test_strip_leading_trailing_hyphens FAILED [ 90%]
test_slugify.py::TestSlugify::test_unicode_nfd_lowercase FAILED          [100%]

FAILED test_slugify.py::TestSlugify::test_hello_world
  AssertionError: 'Hello-World-' != 'hello-world'
FAILED test_slugify.py::TestSlugify::test_numbers_preserved
  AssertionError: 'Chapter-42-The-End' != 'chapter-42-the-end'
FAILED test_slugify.py::TestSlugify::test_pure_punctuation
  AssertionError: '-' != ''
FAILED test_slugify.py::TestSlugify::test_single_word
  AssertionError: 'Python' != 'python'
FAILED test_slugify.py::TestSlugify::test_strip_leading_trailing_hyphens
  AssertionError: '-hello-' != 'hello'
FAILED test_slugify.py::TestSlugify::test_unicode_nfd_lowercase
  AssertionError: 'Caf-' != 'cafe'

6 failed, 4 passed
```

Defects observed in seed `slugify.py`:
1. No lowercasing
2. No strip of leading/trailing hyphens
3. Unicode letters dropped / not folded (`Café` → `Caf-`)
4. Pure punctuation becomes `-` not `""`

## Fix

Rewrote `slugify.py`:
- `unicodedata.normalize("NFKD")` + strip combining marks
- collapse non-alnum runs to `-`
- `.lower()` + `.strip("-")`
- empty input short-circuit

## GREEN output (after fix)

Command: `python -m pytest test_slugify.py -v`

```
collected 10 items

test_slugify.py::TestSlugify::test_already_slug PASSED                   [ 10%]
test_slugify.py::TestSlugify::test_collapse_whitespace_and_punctuation PASSED [ 20%]
test_slugify.py::TestSlugify::test_empty_string PASSED                   [ 30%]
test_slugify.py::TestSlugify::test_hello_world PASSED                    [ 40%]
test_slugify.py::TestSlugify::test_non_alnum_stripped PASSED             [ 50%]
test_slugify.py::TestSlugify::test_numbers_preserved PASSED              [ 60%]
test_slugify.py::TestSlugify::test_pure_punctuation PASSED               [ 70%]
test_slugify.py::TestSlugify::test_single_word PASSED                    [ 80%]
test_slugify.py::TestSlugify::test_strip_leading_trailing_hyphens PASSED [ 90%]
test_slugify.py::TestSlugify::test_unicode_nfd_lowercase PASSED          [100%]

10 passed, 1 warning in 0.02s
```

## Acceptance checklist

- [x] 测试文件可跑
- [x] response 含修复前失败
- [x] 修复后通过
- [x] 边界：空串、纯标点、首尾符号、多分隔符
