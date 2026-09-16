# SE017-slugify · B-noskill · RED → GREEN

## Unicode strategy (notes)

Chose **NFKD + drop combining marks + lower**.

- `Café` → `cafe`
- `naïve` → `naive`
- `Ünïcödé` → `unicode`
- `ÉTÉ` → `ete`
- `Ångström` → `angstrom`

Rationale: pure-ASCII slugs are portable across URLs, filesystems, and
ASCII-only backends. Combining marks are removed after decomposition so
the base letter survives. Tests encode this choice explicitly
(`test_unicode_nfkd_accents_fold_to_ascii`).

## Seed defects

Initial `slugify.py` was:

```python
def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

Missing: empty-input guard, NFKD/deaccent, lowercase, strip leading/trailing `-`.
Non-alnum collapse was present but applied without case folding, so
trailing punctuation left a dangling `-` and pure punctuation became `"-"`.

## RED — before fix

```
$ python -m unittest test_slugify -v

test_already_slug ... ok
test_digits_kept ... ok
test_empty_input ... ok
test_hello_world ... FAIL
test_leading_trailing_separators_stripped ... FAIL
test_long_title ... FAIL
test_mixed_whitespace_and_punct_collapses ... ok
test_no_split_inside_alnum_word ... FAIL
test_non_alnum_stripped ... ok
test_only_one_char ... FAIL
test_punctuation_run_collapses ... ok
test_pure_punctuation_or_space ... FAIL
test_unicode_lowercase_applied ... FAIL
test_unicode_nfkd_accents_fold_to_ascii ... FAIL
test_whitespace_run_collapses ... ok

FAIL: test_hello_world
AssertionError: 'Hello-World-' != 'hello-world'

FAIL: test_leading_trailing_separators_stripped
AssertionError: '-Hello-World-' != 'hello-world'

FAIL: test_long_title
AssertionError: 'The-Quick-Brown-Fox-Jumps-Over-the-Lazy-Dog-' != 'the-quick-brown-fox-jumps-over-the-lazy-dog'

FAIL: test_no_split_inside_alnum_word
AssertionError: 'HelloWorld' != 'helloworld'

FAIL: test_only_one_char
AssertionError: 'A' != 'a'

FAIL: test_pure_punctuation_or_space
AssertionError: '-' != ''

FAIL: test_unicode_lowercase_applied
AssertionError: 'HELLO' != 'hello'

FAIL: test_unicode_nfkd_accents_fold_to_ascii
AssertionError: 'Caf-' != 'cafe'

Ran 15 tests in 0.004s
FAILED (failures=8)
```

## Fix applied to `slugify.py`

1. Early-return `""` for empty input.
2. `unicodedata.normalize("NFKD", text)` then drop combining marks.
3. `.lower()`.
4. `re.sub(r"[^a-z0-9]+", "-", s)` collapse non-alnum runs.
5. `.strip("-")` remove leading/trailing separators.

## GREEN — after fix

```
$ python -m unittest test_slugify -v

test_already_slug ... ok
test_digits_kept ... ok
test_empty_input ... ok
test_hello_world ... ok
test_leading_trailing_separators_stripped ... ok
test_long_title ... ok
test_mixed_whitespace_and_punct_collapses ... ok
test_no_split_inside_alnum_word ... ok
test_non_alnum_stripped ... ok
test_only_one_char ... ok
test_punctuation_run_collapses ... ok
test_pure_punctuation_or_space ... ok
test_unicode_lowercase_applied ... ok
test_unicode_nfkd_accents_fold_to_ascii ... ok
test_whitespace_run_collapses ... ok

----------------------------------------------------------------------
Ran 15 tests in 0.000s
OK
```

## Acceptance checklist

- [x] 测试文件可跑 (`python -m unittest test_slugify -v`)
- [x] response 含修复前失败 (RED block above)
- [x] 修复后通过 (GREEN block above)
- [x] 边界：空串、纯标点、首尾符号、多分隔符
      (`test_empty_input`, `test_pure_punctuation_or_space`,
       `test_leading_trailing_separators_stripped`,
       `test_punctuation_run_collapses`, `test_only_one_char`)

## Spec compliance

| Spec | Covered by |
|---|---|
| `Hello, World!` → `hello-world` | `test_hello_world` |
| 连续空白/标点折叠为单个 `-` | `test_whitespace_run_collapses`, `test_punctuation_run_collapses`, `test_mixed_whitespace_and_punct_collapses` |
| 去掉首尾 `-` | `test_leading_trailing_separators_stripped` |
| 非字母数字剥离；空串返回 `""` | `test_non_alnum_stripped`, `test_empty_input`, `test_pure_punctuation_or_space` |
| Unicode 小写 + NFKD 策略 | `test_unicode_nfkd_accents_fold_to_ascii`, `test_unicode_lowercase_applied` |
