# Response — SE018-slugify

## Unicode 策略

**选用 NFKD 归一化 + 剥离组合变音符 + 小写**。理由：slug 用于 URL/标识符，ASCII 化更安全、可移植。

- `Café` → `NFKD` → `Cafe` + combining accent → 去 combining → `cafe`
- `naïve` → `naive`
- `Über` → `uber`
- `crème brûlée` → `creme-brulee`

未选纯 `.lower()` 策略（那会得到 `café` / `naïve` / `über`）。

## 流程

1. 先写 `test_slugify.py`，对有缺陷的种子实现跑出 RED
2. 修复 `slugify.py`（NFKD + lower + 折叠 + strip）
3. 再跑同一套测试得到 GREEN

未删减失败用例；只改了 `slugify.py` 的实现逻辑。

---

## RED — 修复前（7 failed, 2 passed）

种子缺陷：无 `.lower()`、无 strip、无 NFKD、折叠后不 strip 首尾 `-`。

```
$ python -m pytest test_slugify.py -v

test_slugify.py::TestSlugify::test_already_slug PASSED                   [ 11%]
test_slugify.py::TestSlugify::test_collapse_whitespace_and_punctuation FAILED [ 22%]
test_slugify.py::TestSlugify::test_digits_preserved FAILED               [ 33%]
test_slugify.py::TestSlugify::test_empty_string PASSED                   [ 44%]
test_slugify.py::TestSlugify::test_hello_world FAILED                    [ 55%]
test_slugify.py::TestSlugify::test_leading_trailing_symbols FAILED       [ 66%]
test_slugify.py::TestSlugify::test_mixed_case_and_spaces FAILED          [ 77%]
test_slugify.py::TestSlugify::test_pure_punctuation FAILED               [ 88%]
test_slugify.py::TestSlugify::test_unicode_nfkd_strategy FAILED          [100%]

=============================== FAILURES ===============================

____________ TestSlugify.test_collapse_whitespace_and_punctuation _______
>       self.assertEqual(slugify("a, b! c?"), "a-b-c")
E       AssertionError: 'a-b-c-' != 'a-b-c'

____________ TestSlugify.test_digits_preserved __________________________
>       self.assertEqual(slugify("Python 3.12"), "python-3-12")
E       AssertionError: 'Python-3-12' != 'python-3-12'

____________ TestSlugify.test_hello_world ______________________________
>       self.assertEqual(slugify("Hello, World!"), "hello-world")
E       AssertionError: 'Hello-World-' != 'hello-world'

____________ TestSlugify.test_leading_trailing_symbols _________________
>       self.assertEqual(slugify("--Hello--"), "hello")
E       AssertionError: '-Hello-' != 'hello'

____________ TestSlugify.test_mixed_case_and_spaces ____________________
>       self.assertEqual(slugify("The Quick Brown Fox"), "the-quick-brown-fox")
E       AssertionError: 'The-Quick-Brown-Fox' != 'the-quick-brown-fox'

____________ TestSlugify.test_pure_punctuation _________________________
>       self.assertEqual(slugify("!!!"), "")
E       AssertionError: '-' != ''

____________ TestSlugify.test_unicode_nfkd_strategy ____________________
>       self.assertEqual(slugify("Café"), "cafe")
E       AssertionError: 'Caf-' != 'cafe'

======================= short test summary info =======================
FAILED test_slugify.py::TestSlugify::test_collapse_whitespace_and_punctuation
FAILED test_slugify.py::TestSlugify::test_digits_preserved
FAILED test_slugify.py::TestSlugify::test_hello_world
FAILED test_slugify.py::TestSlugify::test_leading_trailing_symbols
FAILED test_slugify.py::TestSlugify::test_mixed_case_and_spaces
FAILED test_slugify.py::TestSlugify::test_pure_punctuation
FAILED test_slugify.py::TestSlugify::test_unicode_nfkd_strategy
======================== 7 failed, 2 passed ===========================
```

unittest 同样：`Ran 9 tests … FAILED (failures=7)`

---

## 修复 `slugify.py`

```python
import re
import unicodedata


def slugify(text: str) -> str:
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")
```

---

## GREEN — 修复后（9 passed）

```
$ python -m pytest test_slugify.py -v

test_slugify.py::TestSlugify::test_already_slug PASSED                   [ 11%]
test_slugify.py::TestSlugify::test_collapse_whitespace_and_punctuation PASSED [ 22%]
test_slugify.py::TestSlugify::test_digits_preserved PASSED               [ 33%]
test_slugify.py::TestSlugify::test_empty_string PASSED                   [ 44%]
test_slugify.py::TestSlugify::test_hello_world PASSED                    [ 55%]
test_slugify.py::TestSlugify::test_leading_trailing_symbols PASSED       [ 66%]
test_slugify.py::TestSlugify::test_mixed_case_and_spaces PASSED          [ 77%]
test_slugify.py::TestSlugify::test_pure_punctuation PASSED               [ 88%]
test_slugify.py::TestSlugify::test_unicode_nfkd_strategy PASSED          [100%]

======================== 9 passed, 1 warning ==========================
```

unittest：`Ran 9 tests … OK`

---

## 验收对照

| 项 | 状态 |
| --- | --- |
| 测试文件可跑 | ✅ pytest + unittest |
| response 含修复前失败 | ✅ RED 7 failed |
| 修复后通过 | ✅ GREEN 9 passed |
| 边界：空串 | ✅ `test_empty_string` |
| 边界：纯标点 | ✅ `test_pure_punctuation` |
| 边界：首尾符号 | ✅ `test_leading_trailing_symbols` |
| 边界：多分隔符 | ✅ `test_collapse_whitespace_and_punctuation` |
| Unicode 策略写明并测到位 | ✅ NFKD，`test_unicode_nfkd_strategy` |

## 文件

- `test_slugify.py` — 9 tests
- `slugify.py` — 修复后实现
- `response.md` — 本文件
