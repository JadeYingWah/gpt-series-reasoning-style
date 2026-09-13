# SE004-slugify — RED → GREEN

## Unicode strategy (chosen)

**NFKD + drop combining marks + lower.**

- `unicodedata.normalize("NFKD", …)` decomposes accented letters (`é` → `e` + U+0301).
- Combining marks are stripped, then the result is lowercased.
- Effect: `Café` → `cafe`, `naïve` → `naive`, `Ünïcödé` → `unicode`.
- Letters that do not decompose are kept in their lowercase form (category `L*`/`N*`).

## Test file

`test_slugify.py` — 12 tests covering the spec and boundaries:
empty string, pure punctuation, leading/trailing symbols, multi-separators, NFKD Unicode.

---

## RED — run against original `slugify.py`

Command: `python -m pytest test_slugify.py -v --tb=short`

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: <实验根目录>\ab-longrun-300\SE004-slugify\B-noskill
plugins: anyio-4.14.2, asyncio-0.26.0, cov-6.3.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 12 items

test_slugify.py::TestSpec::test_hello_world FAILED                       [  8%]
test_slugify.py::TestSpec::test_collapse_whitespace_and_punct PASSED     [ 16%]
test_slugify.py::TestSpec::test_strip_leading_trailing_separator FAILED  [ 25%]
test_slugify.py::TestSpec::test_empty_string PASSED                      [ 33%]
test_slugify.py::TestSpec::test_pure_punctuation FAILED                  [ 41%]
test_slugify.py::TestSpec::test_alphanumeric_preserved FAILED            [ 50%]
test_slugify.py::TestSpec::test_unicode_nfkd_strategy FAILED             [ 58%]
test_slugify.py::TestBoundaries::test_single_char FAILED                 [ 66%]
test_slugify.py::TestBoundaries::test_multiple_separators_between_words PASSED [ 75%]
test_slugify.py::TestBoundaries::test_leading_digits PASSED              [ 83%]
test_slugify.py::TestBoundaries::test_underscore_treated_as_separator PASSED [ 91%]
test_slugify.py::TestBoundaries::test_already_slug PASSED                [100%]

======================== FAILURES =============================================
____________________________ TestSpec.test_hello_world ________________________
test_slugify.py:9: in test_hello_world
    assert slugify("Hello, World!") == "hello-world"
E   AssertionError: assert 'Hello-World-' == 'hello-world'
____________________________ TestSpec.test_strip_leading_trailing_separator __
test_slugify.py:18: in test_strip_leading_trailing_separator
    assert slugify("  --hello--  ") == "hello"
E   AssertionError: assert '-hello-' == 'hello'
____________________________ TestSpec.test_pure_punctuation ___________________
test_slugify.py:26: in test_pure_punctuation
    assert slugify("!!!") == ""
E   AssertionError: assert '-' == ''
____________________________ TestSpec.test_alphanumeric_preserved _____________
test_slugify.py:32: in test_alphanumeric_preserved
    assert slugify("Version 2.0") == "version-2-0"
E   AssertionError: assert 'Version-2-0' == 'version-2-0'
____________________________ TestSpec.test_unicode_nfkd_strategy ______________
test_slugify.py:38: in test_unicode_nfkd_strategy
    assert slugify("Café") == "cafe"
E   AssertionError: assert 'Caf-' == 'cafe'
____________________________ TestBoundaries.test_single_char _________________
test_slugify.py:46: in test_single_char
    assert slugify("!") == ""
E   AssertionError: assert '-' == ''
============================ warnings summary =================================
test_slugify.py::TestSpec::test_hello_world
  <用户目录>\AppData\Roaming\Python\Python314\site-packages\pytest_asyncio\plugin.py:1216: DeprecationWarning: 'asyncio.get_event_loop_policy' is deprecated and slated for removal in Python 3.16
    return asyncio.get_event_loop_policy()
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED test_slugify.py::TestSpec::test_hello_world - AssertionError: assert '...
FAILED test_slugify.py::TestSpec::test_strip_leading_trailing_separator - Ass...
FAILED test_slugify.py::TestSpec::test_pure_punctuation - AssertionError: ass...
FAILED test_slugify.py::TestSpec::test_alphanumeric_preserved - AssertionErro...
FAILED test_slugify.py::TestSpec::test_unicode_nfkd_strategy - AssertionErro...
FAILED test_slugify.py::TestBoundaries::test_single_char - AssertionError: as...
==================== 6 failed, 6 passed, 1 warning in 0.10s ====================
```

### Defects observed

| Defect | Evidence |
|--------|----------|
| No lowercasing | `Hello-World-` instead of `hello-world` |
| No strip of leading/trailing `-` | `-hello-` instead of `hello`; pure punct → `-` not `""` |
| Accented letters dropped as separators | `Café` → `Caf-` |
| Empty/edge inputs leave stray `-` | `!!!` → `-` |

---

## GREEN — after fix in `slugify.py`

Fix applied: NFKD normalize → strip combining marks → lower → collapse non L*/N* runs to `-` → strip edge `-`.

Command: `python -m pytest test_slugify.py -v --tb=short`

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: <实验根目录>\ab-longrun-300\SE004-slugify\B-noskill
plugins: anyio-4.14.2, asyncio-0.26.0, cov-6.3.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 12 items

test_slugify.py::TestSpec::test_hello_world PASSED                       [  8%]
test_slugify.py::TestSpec::test_collapse_whitespace_and_punct PASSED     [ 16%]
test_slugify.py::TestSpec::test_strip_leading_trailing_separator PASSED  [ 25%]
test_slugify.py::TestSpec::test_empty_string PASSED                      [ 33%]
test_slugify.py::TestSpec::test_pure_punctuation PASSED                  [ 41%]
test_slugify.py::TestSpec::test_alphanumeric_preserved PASSED            [ 50%]
test_slugify.py::TestSpec::test_unicode_nfkd_strategy PASSED             [ 58%]
test_slugify.py::TestBoundaries::test_single_char PASSED                 [ 66%]
test_slugify.py::TestBoundaries::test_multiple_separators_between_words PASSED [ 75%]
test_slugify.py::TestBoundaries::test_leading_digits PASSED              [ 83%]
test_slugify.py::TestBoundaries::test_underscore_treated_as_separator PASSED [ 91%]
test_slugify.py::TestBoundaries::test_already_slug PASSED                [100%]

============================== warnings summary ===============================
test_slugify.py::TestSpec::test_hello_world
  <用户目录>\AppData\Roaming\Python\Python314\site-packages\pytest_asyncio\plugin.py:1216: DeprecationWarning: 'asyncio.get_event_loop_policy' is deprecated and slated for removal in Python 3.16
    return asyncio.get_event_loop_policy()
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 12 passed, 1 warning in 0.03s ========================
```

## Acceptance checklist

- [x] Tests runnable (`pytest test_slugify.py`)
- [x] response contains pre-fix failures (RED above)
- [x] All tests pass after fix (GREEN above)
- [x] Boundaries covered: empty string, pure punctuation, leading/trailing symbols, multi-separators
- [x] No test cases removed/weakened; only `slugify.py` was fixed
