# Response — SE019-slugify (Phase 2)

## Unicode strategy

**NFKD decompose → drop combining marks → lowercase.**

- Accented Latin letters fold to ASCII bases: `Café` → `cafe`, `Ångström` → `angstrom`.
- Letters without combining marks (CJK etc.) are kept: `中文标题` → `中文标题`.
- `\w` (Unicode) keeps letters/digits; `_` is treated as a separator, not a kept character.
- Non-letter/digit runs collapse to a single `-`; leading/trailing `-` stripped.
- Empty / whitespace-only / punct-only inputs return `""`.

## RED — tests against original seed

Seed defects: no `.lower()`, no NFKD, no strip of edge `-`, non-alnum path leaves dangling separators, empty/punct not special-cased.

```
test_collapse_runs (test_slugify.TestSlugifySpec.test_collapse_runs) ... ok
test_digits_kept (test_slugify.TestSlugifySpec.test_digits_kept) ... FAIL
test_empty_and_punct_only (test_slugify.TestSlugifySpec.test_empty_and_punct_only) ... FAIL
test_hello_world (test_slugify.TestSlugifySpec.test_hello_world) ... FAIL
test_mixed_word (test_slugify.TestSlugifySpec.test_mixed_word) ... FAIL
test_non_alnum_stripped (test_slugify.TestSlugifySpec.test_non_alnum_stripped) ... ok
test_strip_edges (test_slugify.TestSlugifySpec.test_strip_edges) ... FAIL
test_unicode_letters_kept_when_no_mark (test_slugify.TestSlugifySpec.test_unicode_letters_kept_when_no_mark) ... FAIL
test_unicode_nfkd_fold (test_slugify.TestSlugifySpec.test_unicode_nfkd_fold) ... FAIL

======================================================================
FAIL: test_digits_kept (test_slugify.TestSlugifySpec.test_digits_kept)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<实验根目录>\ab-longrun-300\SE019-slugify\A-skill\test_slugify.py", line 37, in test_digits_kept
    self.assertEqual(slugify("Chapter 12!"), "chapter-12")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'Chapter-12-' != 'chapter-12'
- Chapter-12-
? ^         -
+ chapter-12
? ^


======================================================================
FAIL: test_empty_and_punct_only (test_slugify.TestSlugifySpec.test_empty_and_punct_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<实验根目录>\ab-longrun-300\SE019-slugify\A-skill\test_slugify.py", line 32, in test_empty_and_punct_only
    self.assertEqual(slugify("   "), "")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: '-' != ''
- -


======================================================================
FAIL: test_hello_world (test_slugify.TestSlugifySpec.test_hello_world)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<实验根目录>\ab-longrun-300\SE019-slugify\A-skill\test_slugify.py", line 15, in test_hello_world
    self.assertEqual(slugify("Hello, World!"), "hello-world")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'Hello-World-' != 'hello-world'
- Hello-World-
? ^     ^    -
+ hello-world
? ^     ^


======================================================================
FAIL: test_mixed_word (test_slugify.TestSlugifySpec.test_mixed_word)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<实验根目录>\ab-longrun-300\SE019-slugify\A-skill\test_slugify.py", line 53, in test_mixed_word
    self.assertEqual(slugify("Hello World Example"), "hello-world-example")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'Hello-World-Example' != 'hello-world-example'
- Hello-World-Example
? ^     ^     ^
+ hello-world-example
? ^     ^     ^


======================================================================
FAIL: test_strip_edges (test_slugify.TestSlugifySpec.test_strip_edges)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<实验根目录>\ab-longrun-300\SE019-slugify\A-skill\test_slugify.py", line 22, in test_strip_edges
    self.assertEqual(slugify("--Hello--"), "hello")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: '-Hello-' != 'hello'
- -Hello-
+ hello


======================================================================
FAIL: test_unicode_letters_kept_when_no_mark (test_slugify.TestSlugifySpec.test_unicode_letters_kept_when_no_mark)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<实验根目录>\ab-longrun-300\SE019-slugify\A-skill\test_slugify.py", line 49, in test_unicode_letters_kept_when_no_mark
    self.assertEqual(slugify("中文标题"), "中文标题")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: '-' != '中文标题'
- -
+ 中文标题


======================================================================
FAIL: test_unicode_nfkd_fold (test_slugify.TestSlugifySpec.test_unicode_nfkd_fold)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<实验根目录>\ab-longrun-300\SE019-slugify\A-skill\test_slugify.py", line 42, in test_unicode_nfkd_fold
    self.assertEqual(slugify("Café"), "cafe")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'Caf-' != 'cafe'
- Caf-
+ cafe


----------------------------------------------------------------------
Ran 9 tests in 0.005s

FAILED (failures=7)
```

## Fix

`slugify.py` rewritten:

1. early-return `""` for empty input
2. `unicodedata.normalize("NFKD", text)` + drop `combining(ch)`
3. `.lower()`
4. `re.sub(r"[^\w]+", "-", ...)` then `_` → `-`, collapse `-` runs, `.strip("-")`

## GREEN — after fix

```
test_collapse_runs (test_slugify.TestSlugifySpec.test_collapse_runs) ... ok
test_digits_kept (test_slugify.TestSlugifySpec.test_digits_kept) ... ok
test_empty_and_punct_only (test_slugify.TestSlugifySpec.test_empty_and_punct_only) ... ok
test_hello_world (test_slugify.TestSlugifySpec.test_hello_world) ... ok
test_mixed_word (test_slugify.TestSlugifySpec.test_mixed_word) ... ok
test_non_alnum_stripped (test_slugify.TestSlugifySpec.test_non_alnum_stripped) ... ok
test_strip_edges (test_slugify.TestSlugifySpec.test_strip_edges) ... ok
test_unicode_letters_kept_when_no_mark (test_slugify.TestSlugifySpec.test_unicode_letters_kept_when_no_mark) ... ok
test_unicode_nfkd_fold (test_slugify.TestSlugifySpec.test_unicode_nfkd_fold) ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.001s

OK
```

## Acceptance

- [x] test file runs
- [x] response has pre-fix failures
- [x] post-fix pass
- [x] edges: empty, punct-only, edge symbols, multi-separators covered

## Files touched (this phase)

- `test_slugify.py` (new)
- `slugify.py` (fixed)
- `response.md` (this file)
