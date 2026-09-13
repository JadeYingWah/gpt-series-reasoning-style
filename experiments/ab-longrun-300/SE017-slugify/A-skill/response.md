# Response — SE017-slugify (A-skill)

## Unicode strategy (chosen)

**NFKD + strip combining marks (Mn) → ASCII-fold accents; keep non-decomposable Unicode letters lowercased.**

| Input | Output | Why |
| --- | --- | --- |
| `Café` | `cafe` | NFKD splits `é` → `e` + U+0301; Mn dropped |
| `Ångström` | `angstrom` | `Å` → `A`+ring, `ö` → `o`+diaeresis; Mn dropped |
| `naïve` | `naive` | same fold |
| `crème brûlée` | `creme-brulee` | fold + separator collapse |
| `你好` | `你好` | no NFKD decomposition; letter kept, lower is identity |
| `ПРИВЕТ` | `привет` | Cyrillic letter, lowercased, not stripped |

Rationale: URL-friendly ASCII slugs for Latin accents; non-Latin scripts that cannot fold still produce usable slugs instead of being erased.

## Seed defects

```python
# original seed
s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
return s
```

- no `.lower()`
- no NFKD / deaccent
- no `strip("-")` of edges
- `[^a-zA-Z0-9]` erases non-ASCII letters (你好 → `-`)
- pure punctuation (`!!!`) → `-` instead of `""`

## RED — run against seed

```
$ python -m pytest test_slugify.py -v
collected 11 items

test_slugify.py::TestSlugify::test_basic_hello_world FAILED
test_slugify.py::TestSlugify::test_collapse_whitespace_and_punctuation PASSED
test_slugify.py::TestSlugify::test_digits_preserved FAILED
test_slugify.py::TestSlugify::test_empty_input PASSED
test_slugify.py::TestSlugify::test_lowercase FAILED
test_slugify.py::TestSlugify::test_mixed_edge FAILED
test_slugify.py::TestSlugify::test_non_alnum_stripped PASSED
test_slugify.py::TestSlugify::test_pure_punctuation_or_whitespace FAILED
test_slugify.py::TestSlugify::test_strip_leading_trailing_separators FAILED
test_slugify.py::TestSlugify::test_unicode_letters_without_decomposable_accent FAILED
test_slugify.py::TestSlugify::test_unicode_nfkd_fold FAILED

========================= 8 failed, 3 passed in 0.12s =========================
```

Representative failures:

- `test_basic_hello_world`: `'Hello-World-' != 'hello-world'`
- `test_strip_leading_trailing_separators`: `'-hello-' != 'hello'`
- `test_pure_punctuation_or_whitespace`: `'-' != ''`
- `test_unicode_nfkd_fold`: `'Caf-' != 'cafe'`
- `test_unicode_letters_without_decomposable_accent`: `'-' != '你好'`

## Fix (`slugify.py`)

```python
def slugify(text: str) -> str:
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[\W_]+", "-", s, flags=re.UNICODE)
    return s.strip("-")
```

Pipeline: NFKD → drop Mn → lower → collapse non-alnum/`_` to single `-` → strip edge `-`.

## GREEN — run against fix

```
$ python -m pytest test_slugify.py -v
collected 11 items

test_slugify.py::TestSlugify::test_basic_hello_world PASSED
test_slugify.py::TestSlugify::test_collapse_whitespace_and_punctuation PASSED
test_slugify.py::TestSlugify::test_digits_preserved PASSED
test_slugify.py::TestSlugify::test_empty_input PASSED
test_slugify.py::TestSlugify::test_lowercase PASSED
test_slugify.py::TestSlugify::test_mixed_edge PASSED
test_slugify.py::TestSlugify::test_non_alnum_stripped PASSED
test_slugify.py::TestSlugify::test_pure_punctuation_or_whitespace PASSED
test_slugify.py::TestSlugify::test_strip_leading_trailing_separators PASSED
test_slugify.py::TestSlugify::test_unicode_letters_without_decomposable_accent PASSED
test_slugify.py::TestSlugify::test_unicode_nfkd_fold PASSED

========================== 11 passed in 0.03s ===============================
```

## Acceptance checklist

- [x] 测试文件可跑 (`python -m pytest test_slugify.py`)
- [x] response 含修复前失败 (RED above, 8 failed)
- [x] 修复后通过 (GREEN above, 11 passed)
- [x] 边界：空串、纯标点、首尾符号、多分隔符 (covered in `test_empty_input`, `test_pure_punctuation_or_whitespace`, `test_strip_leading_trailing_separators`, `test_collapse_whitespace_and_punctuation`, `test_mixed_edge`)

## Spec coverage

| Rule | Test |
| --- | --- |
| `slugify("Hello, World!")` → `"hello-world"` | `test_basic_hello_world` |
| 连续空白/标点折叠为单个 `-` | `test_collapse_whitespace_and_punctuation` |
| 去掉首尾 `-` | `test_strip_leading_trailing_separators` |
| 非字母数字剥离；空串 → `""` | `test_non_alnum_stripped`, `test_empty_input` |
| Unicode：NFKD fold + non-decomposable keep | `test_unicode_nfkd_fold`, `test_unicode_letters_without_decomposable_accent` |
| 数字保留 | `test_digits_preserved` |
