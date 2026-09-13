# SE020-slugify · Phase 2 Response

## Unicode strategy (chosen)

**NFKD + drop combining marks (Mn).** Accented letters fold to base ASCII:

| Input | Output |
| --- | --- |
| `Café` | `cafe` |
| `naïve` | `naive` |
| `Über` | `uber` |
| `Ångström` | `angstrom` |
| `Ñoño` | `nono` |
| `Été` | `ete` |

Rationale: URL-safe ASCII slugs are the common web default; deaccented form is stable across systems that cannot handle non-ASCII path segments. Tests lock this in (`test_unicode_nfkd_fold`, `test_only_unicode_letters`).

## RED — tests against original defective `slugify.py`

Original seed:

```python
def slugify(text: str) -> str:
    # DEFECT: no lower, no strip, collapse broken
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

Command: `python -m unittest test_slugify -v`

```
Ran 9 tests in 0.005s
FAILED (failures=7)
```

Failures (before fix):

| Test | Got | Expected |
| --- | --- | --- |
| `test_hello_world` | `Hello-World-` | `hello-world` |
| `test_pure_punctuation` (`!!!`) | `-` | `` |
| `test_collapse_whitespace_and_punct` | `-lots-of-separators-` | `lots-of-separators` |
| `test_strip_leading_trailing_separators` | `-Hello-` | `hello` |
| `test_mixed_case_and_digits` | `Python3-12` | `python3-12` |
| `test_unicode_nfkd_fold` (`Café`) | `Caf-` | `cafe` |
| `test_only_unicode_letters` (`Ñoño`) | `-o-o` | `nono` |

Two tests already passed by accident (`test_empty_string`, `test_non_alnum_stripped`); the other seven expose: no lower, no strip, no NFKD fold.

## Fix — `slugify.py`

1. `unicodedata.normalize("NFKD", text)` then drop `unicodedata.combining(ch)` → deaccent.
2. `s.lower()` before the non-alnum pass so the regex `[a-z0-9]` is sufficient.
3. Collapse runs of non-alnum to a single `-`.
4. `.strip("-")` removes dangling leading/trailing separators (covers pure-punct → `""`).

## GREEN — after fix

```
Ran 9 tests in 0.001s
OK
```

All 9 pass. No test was deleted or weakened; only `slugify.py` was fixed.

## Spec checklist

- [x] `slugify("Hello, World!")` → `"hello-world"`
- [x] consecutive whitespace/punct collapse to single `-`
- [x] strip leading/trailing `-`
- [x] non-alnum (except `-`) removed; empty → `""`
- [x] Unicode: NFKD strategy, documented + tested (`Café` → `cafe`)
- [x] boundaries: empty, pure punct, leading/trailing symbols, multi-separators
