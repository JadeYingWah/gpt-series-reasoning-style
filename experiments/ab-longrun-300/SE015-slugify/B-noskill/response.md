# SE015-slugify · B-noskill · RED → GREEN

## Unicode strategy (notes)

Chose **NFKD + drop combining marks**. Accents decompose then the
combining marks are discarded, so letters fold to ASCII base form:

- `Café` → `cafe`
- `naïve` → `naive`
- `Ünïcödé` → `unicode`
- `ÉTÉ` → `ete`

Rationale: URL slugs are safer and more portable as pure ASCII.
Tests explicitly encode this choice (`test_unicode_nfkd_strategy`).

## Defects in seed `slugify.py`

Seed was:

```python
s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
return s
```

Missing: lowercase, NFKD/deaccent, strip leading/trailing `-`
(also leftover trailing `-` when input ends with punctuation).
Collapse of non-alnum runs was already present but case not applied.

## RED — before fix

```
$ python -m unittest test_slugify -v

test_already_slugified ... ok
test_basic_hello_world ... FAIL
test_collapse_punctuation_and_separators ... ok
test_collapse_whitespace ... ok
test_digits_preserved ... ok
test_empty_string ... ok
test_mixed_realistic_title ... FAIL
test_non_alnum_stripped_except_hyphen ... ok
test_only_letters_no_split ... FAIL
test_pure_punctuation_returns_empty ... FAIL
test_strip_leading_trailing_separators ... FAIL
test_unicode_nfkd_strategy ... FAIL
======================================================================
FAIL: test_basic_hello_world
AssertionError: 'Hello-World-' != 'hello-world'

FAIL: test_mixed_realistic_title
AssertionError: 'The-Quick-Brown-Fox-Jumps-Over-the-Lazy-Dog-' != 'the-quick-brown-fox-jumps-over-the-lazy-dog'

FAIL: test_only_letters_no_split
AssertionError: 'HelloWorld' != 'helloworld'

FAIL: test_pure_punctuation_returns_empty
AssertionError: '-' != ''

FAIL: test_strip_leading_trailing_separators
AssertionError: '-Hello-World-' != 'hello-world'

FAIL: test_unicode_nfkd_strategy
AssertionError: 'Caf-' != 'cafe'
----------------------------------------------------------------------
Ran 12 tests in 0.005s
FAILED (failures=6)
```

## Fix applied to `slugify.py`

1. Early-return `""` for empty input.
2. `unicodedata.normalize("NFKD", text)` then drop combining marks.
3. `.lower()`.
4. `re.sub(r"[^a-z0-9]+", "-", s)` to collapse non-alnum runs.
5. `.strip("-")` to remove leading/trailing separators.

## GREEN — after fix

```
$ python -m unittest test_slugify -v

test_already_slugified ... ok
test_basic_hello_world ... ok
test_collapse_punctuation_and_separators ... ok
test_collapse_whitespace ... ok
test_digits_preserved ... ok
test_empty_string ... ok
test_mixed_realistic_title ... ok
test_non_alnum_stripped_except_hyphen ... ok
test_only_letters_no_split ... ok
test_pure_punctuation_returns_empty ... ok
test_strip_leading_trailing_separators ... ok
test_unicode_nfkd_strategy ... ok
----------------------------------------------------------------------
Ran 12 tests in 0.001s
OK
```

## Acceptance checklist

- [x] 测试文件可跑 (`python -m unittest test_slugify -v`)
- [x] response 含修复前失败 (RED block above)
- [x] 修复后通过 (GREEN block above)
- [x] 边界：空串、纯标点、首尾符号、多分隔符
      (`test_empty_string`, `test_pure_punctuation_returns_empty`,
       `test_strip_leading_trailing_separators`,
       `test_collapse_punctuation_and_separators`)

## Spec compliance

| Spec | Covered by |
|---|---|
| `Hello, World!` → `hello-world` | `test_basic_hello_world` |
| 连续空白/标点折叠为单个 `-` | `test_collapse_whitespace`, `test_collapse_punctuation_and_separators` |
| 去掉首尾 `-` | `test_strip_leading_trailing_separators` |
| 非字母数字剥离；空串返回 `""` | `test_non_alnum_stripped_except_hyphen`, `test_empty_string`, `test_pure_punctuation_returns_empty` |
| Unicode 小写 + NFKD 策略 | `test_unicode_nfkd_strategy` (notes above) |
