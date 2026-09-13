# SE007-slugify · B arm · RED→GREEN

## Unicode strategy (notes)

**Chosen: NFKD + strip combining marks (ASCII fold), then lowercase.**

- `Café` → `cafe` (é decomposes to e + combining acute; mark stripped)
- `CAFÉ` → `cafe`
- Non-decomposable non-ASCII letters (e.g. `ß`) and scripts (CJK, Cyrillic without transliteration) become separators. Example: `Grüße` → `gru-e` (ü→u, ß stripped).
- Alternative (documented, not chosen): lower-only would yield `café` / `grüße`. Spec requires the strategy to be stated and tested — this arm uses NFKD fold.

## Defects in seed `slugify.py`

```python
s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
return s
```

Missing: lowercase, edge `-` strip, Unicode fold, empty/punct-only → `""`.

---

## RED (before fix)

Command: `python -m pytest test_slugify.py -v --tb=short`

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0 -- C:\Python314\python.exe
rootdir: <实验根目录>\ab-longrun-300\SE007-slugify\B-noskill
collected 24 items

test_slugify.py::TestSpecExamples::test_hello_world FAILED               [  4%]
test_slugify.py::TestSpecExamples::test_simple_words PASSED              [  8%]
test_slugify.py::TestSpecExamples::test_already_slug PASSED              [ 12%]
test_slugify.py::TestCollapse::test_consecutive_spaces PASSED            [ 16%]
test_slugify.py::TestCollapse::test_mixed_whitespace_and_punct PASSED    [ 20%]
test_slugify.py::TestCollapse::test_multiple_punct PASSED                [ 25%]
test_slugify.py::TestCollapse::test_mixed_separators PASSED              [ 29%]
test_slugify.py::TestStripEdges::test_leading_punct FAILED               [ 33%]
test_slugify.py::TestStripEdges::test_trailing_punct FAILED              [ 37%]
test_slugify.py::TestStripEdges::test_leading_and_trailing_spaces FAILED [ 41%]
test_slugify.py::TestStripEdges::test_leading_trailing_hyphens FAILED    [ 45%]
test_slugify.py::TestStripEdges::test_only_separators_inside PASSED      [ 50%]
test_slugify.py::TestEmptyAndDegenerate::test_empty_string PASSED        [ 54%]
test_slugify.py::TestEmptyAndDegenerate::test_only_spaces FAILED         [ 58%]
test_slugify.py::TestEmptyAndDegenerate::test_only_punctuation FAILED    [ 62%]
test_slugify.py::TestEmptyAndDegenerate::test_only_symbols FAILED        [ 66%]
test_slugify.py::TestUnicode::test_cafe_accent FAILED                    [ 70%]
test_slugify.py::TestUnicode::test_german_ish FAILED                     [ 75%]
test_slugify.py::TestUnicode::test_uppercase_unicode FAILED              [ 79%]
test_slugify.py::TestUnicode::test_digits_preserved PASSED               [ 83%]
test_slugify.py::TestAlnumOnly::test_underscore_stripped PASSED          [ 87%]
test_slugify.py::TestAlnumOnly::test_keep_digits_and_letters PASSED      [ 91%]
test_slugify.py::TestAlnumOnly::test_single_char PASSED                  [ 95%]
test_slugify.py::TestAlnumOnly::test_single_punct FAILED                 [100%]

============================== warnings summary ===============================
======================== 12 failed, 12 passed, 1 warning in 0.12s ========================
```

Representative failures:

```
assert slugify("Hello, World!") == "hello-world"
E   AssertionError: assert 'Hello-World-' == 'hello-world'

assert slugify("!!!hello") == "hello"
E   AssertionError: assert '-hello' == 'hello'

assert slugify("   ") == ""
E   AssertionError: assert '-' == ''

assert slugify("Café") == "cafe"
E   AssertionError: assert 'Caf-' == 'cafe'
```

---

## Fix

Rewrote `slugify.py`:

1. Early-return `""` for empty input.
2. `unicodedata.normalize("NFKD", text)` + drop combining marks.
3. `.lower()`.
4. `re.sub(r"[^a-z0-9]+", "-", s)` — non-ASCII leftover / punct / whitespace become hyphens and collapse.
5. `.strip("-")`.

No test cases were removed or weakened.

---

## GREEN (after fix)

Command: `python -m pytest test_slugify.py -v --tb=short`

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0 -- C:\Python314\python.exe
rootdir: <实验根目录>\ab-longrun-300\SE007-slugify\B-noskill
collected 24 items

test_slugify.py::TestSpecExamples::test_hello_world PASSED               [  4%]
test_slugify.py::TestSpecExamples::test_simple_words PASSED              [  8%]
test_slugify.py::TestSpecExamples::test_already_slug PASSED              [ 12%]
test_slugify.py::TestCollapse::test_consecutive_spaces PASSED            [ 16%]
test_slugify.py::TestCollapse::test_mixed_whitespace_and_punct PASSED    [ 20%]
test_slugify.py::TestCollapse::test_multiple_punct PASSED                [ 25%]
test_slugify.py::TestCollapse::test_mixed_separators PASSED              [ 29%]
test_slugify.py::TestStripEdges::test_leading_punct PASSED               [ 33%]
test_slugify.py::TestStripEdges::test_trailing_punct PASSED              [ 37%]
test_slugify.py::TestStripEdges::test_leading_and_trailing_spaces PASSED [ 41%]
test_slugify.py::TestStripEdges::test_leading_trailing_hyphens PASSED    [ 45%]
test_slugify.py::TestStripEdges::test_only_separators_inside PASSED      [ 50%]
test_slugify.py::TestEmptyAndDegenerate::test_empty_string PASSED        [ 54%]
test_slugify.py::TestEmptyAndDegenerate::test_only_spaces PASSED         [ 58%]
test_slugify.py::TestEmptyAndDegenerate::test_only_punctuation PASSED    [ 62%]
test_slugify.py::TestEmptyAndDegenerate::test_only_symbols PASSED        [ 66%]
test_slugify.py::TestUnicode::test_cafe_accent PASSED                    [ 70%]
test_slugify.py::TestUnicode::test_german_ish PASSED                     [ 75%]
test_slugify.py::TestUnicode::test_uppercase_unicode PASSED              [ 79%]
test_slugify.py::TestUnicode::test_digits_preserved PASSED               [ 83%]
test_slugify.py::TestAlnumOnly::test_underscore_stripped PASSED          [ 87%]
test_slugify.py::TestAlnumOnly::test_keep_digits_and_letters PASSED      [ 91%]
test_slugify.py::TestAlnumOnly::test_single_char PASSED                  [ 95%]
test_slugify.py::TestAlnumOnly::test_single_punct PASSED                 [100%]

============================== warnings summary ===============================
======================== 24 passed, 1 warning in 0.04s ========================
```

---

## Acceptance checklist

- [x] 测试文件可跑 (`python -m pytest test_slugify.py`)
- [x] response 含修复前失败 (RED above, 12 failed)
- [x] 修复后通过 (GREEN above, 24 passed)
- [x] 边界：空串、纯标点、首尾符号、多分隔符
  - empty string → `""`
  - only spaces / punctuation / symbols → `""`
  - leading/trailing punct & hyphens stripped
  - consecutive separators collapsed (`a!!!b`→`a-b`, `a -_- b`→`a-b`)
