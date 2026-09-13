# SE009-slugify · RED → GREEN

## Unicode strategy

**NFKD normalize + strip combining marks** → ASCII-safe slug.
`Café` → `cafe`, `naïve` → `naive`, `Ünïcödé` → `unicode`.

Rationale: URL-safe ASCII is the usual slug goal; accent decomposition
is lossy but predictable and fully tested.

## RED (before fix)

```
test_already_slug ... ok
test_basic_hello_world ... FAIL
test_collapse_whitespace_and_punctuation ... ok
test_empty_string ... ok
test_non_alnum_stripped_except_hyphen ... ok
test_only_punctuation_returns_empty ... FAIL
test_strip_leading_and_trailing_separators ... FAIL
test_unicode_nfkd_strategy ... FAIL

FAIL: test_basic_hello_world
AssertionError: 'Hello-World-' != 'hello-world'

FAIL: test_only_punctuation_returns_empty
AssertionError: '-' != ''

FAIL: test_strip_leading_and_trailing_separators
AssertionError: '-Hello-' != 'hello'

FAIL: test_unicode_nfkd_strategy
AssertionError: 'Caf-' != 'cafe'

Ran 8 tests in 0.005s
FAILED (failures=4)
```

Defects in original `slugify.py`:
- no lowercasing
- no leading/trailing hyphen strip
- Unicode accents dropped instead of decomposed to ASCII

## GREEN (after fix)

```
test_already_slug ... ok
test_basic_hello_world ... ok
test_collapse_whitespace_and_punctuation ... ok
test_empty_string ... ok
test_non_alnum_stripped_except_hyphen ... ok
test_only_punctuation_returns_empty ... ok
test_strip_leading_and_trailing_separators ... ok
test_unicode_nfkd_strategy ... ok

Ran 8 tests in 0.001s
OK
```

## Boundary coverage

| Case | Result |
|------|--------|
| empty string | `""` |
| pure punctuation `!!!...???` | `""` |
| only hyphens `---` | `""` |
| only whitespace | `""` |
| leading/trailing `--Hello--` | `hello` |
| multi separators `a   b...c!!d` | `a-b-c-d` |
| already slug `simple-slug` | unchanged |
