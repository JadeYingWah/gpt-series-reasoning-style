# SE022-slugify · Phase 2 Response

## Unicode 策略（选定并测到位）

**选择：NFKD + 去掉 combining marks（组合附标）**

- `unicodedata.normalize("NFKD", text)` 把预组合字符拆成基字符 + 附标
  （例如 `é` → `e` + U+0301 COMBINING ACUTE ACCENT）
- 丢弃所有 `unicodedata.combining(c) != 0` 的字符
- 再 `.lower()`

结果：

| 输入 | 输出 | 说明 |
| --- | --- | --- |
| `Café` | `cafe` | é → e + 附标 → e |
| `naïve` | `naive` | ï → i |
| `ÜBER` | `uber` | Ü → U → u |
| `résumé` | `resume` | 两个 é 都折叠 |
| `日本語` | `日本語` | 无附标，原样保留（小写无变化） |
| `Москва` | `москва` | 西里尔字母 lower 后保留 |

不采用「仅 lower」策略，因为那样 `Café` → `café`，URL slug 中带变音符号
不利于可移植性和 SEO 规范化。NFKD + drop marks 是 python-slugify /
unicode-slugify 等主流库的默认行为。

---

## RED — 修复前测试输出

种子缺陷（`slugify.py` 原实现）：

```python
def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

| 缺陷 | 表现 |
| --- | --- |
| 无 `.lower()` | `Hello` → `Hello` |
| 无 NFKD / deaccent | `Café` → `Caf-` |
| 无 `strip("-")` | `--hello--` → `-hello-` |
| 空串/纯标点未特判 | `!!!` → `-` |
| 仅匹配 ASCII `[a-zA-Z0-9]` | `日本語` → `-` |

### pytest 实跑（修复前）

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0
rootdir: <实验根目录>\ab-longrun-300\SE022-slugify\A-skill
plugins: anyio-4.24.0, asyncio-0.26.0, cov-6.3.0
collected 11 items

test_slugify.py::TestSlugify::test_basic_hello_world FAILED              [  9%]
test_slugify.py::TestSlugify::test_collapses_whitespace_and_punct PASSED [ 18%]
test_slugify.py::TestSlugify::test_empty_input PASSED                    [ 27%]
test_slugify.py::TestSlugify::test_lowercases FAILED                     [ 36%]
test_slugify.py::TestSlugify::test_multiple_separators_between_words PASSED [ 45%]
test_slugify.py::TestSlugify::test_numbers_kept PASSED                   [ 54%]
test_slugify.py::TestSlugify::test_pure_punctuation FAILED               [ 63%]
test_slugify.py::TestSlugify::test_strips_leading_trailing_separators FAILED [ 72%]
test_slugify.py::TestSlugify::test_strips_non_alnum FAILED               [ 81%]
test_slugify.py::TestSlugify::test_unicode_letters_retained_when_no_deaccent_needed FAILED [ 90%]
test_slugify.py::TestSlugify::test_unicode_nfkd_deaccent FAILED          [100%]

=========================== short test summary info ===========================
FAILED test_slugify.py::TestSlugify::test_basic_hello_world - AssertionError: 'Hello-World-' != 'hello-world'
FAILED test_slugify.py::TestSlugify::test_lowercases - AssertionError: 'Hello' != 'hello'
FAILED test_slugify.py::TestSlugify::test_pure_punctuation - AssertionError: '-' != ''
FAILED test_slugify.py::TestSlugify::test_strips_leading_trailing_separators - AssertionError: '-hello-' != 'hello'
FAILED test_slugify.py::TestSlugify::test_strips_non_alnum - AssertionError: 'hello-world-' != 'hello-world'
FAILED test_slugify.py::TestSlugify::test_unicode_letters_retained_when_no_deaccent_needed - AssertionError: '-' != '日本語'
FAILED test_slugify.py::TestSlugify::test_unicode_nfkd_deaccent - AssertionError: 'Caf-' != 'cafe'
=================== 7 failed, 4 passed, 1 warning in 0.12s ====================
```

关键断言差异（节选）：

- `slugify("Hello, World!")` → 实际 `'Hello-World-'` ≠ 期望 `'hello-world'`
- `slugify("Hello")` → 实际 `'Hello'` ≠ 期望 `'hello'`
- `slugify("!!!")` → 实际 `'-'` ≠ 期望 `''`
- `slugify("--hello--")` → 实际 `'-hello-'` ≠ 期望 `'hello'`
- `slugify("hello@world!")` → 实际 `'hello-world-'` ≠ 期望 `'hello-world'`
- `slugify("日本語")` → 实际 `'-'` ≠ 期望 `'日本語'`
- `slugify("Café")` → 实际 `'Caf-'` ≠ 期望 `'cafe'`

---

## 修复 — `slugify.py` 最终实现

```python
"""slugify — NFKD deaccent, collapse non-alnum to '-', strip edges."""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD so Café → Cafe (+ combining acute), then drop marks
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    # Keep Unicode letters/digits only; everything else becomes a separator
    s = "".join(c if c.isalnum() else "-" for c in s)
    # Collapse runs and strip edge separators
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")
```

修复要点：

1. **空串短路** — `if not text: return ""`
2. **NFKD + drop combining marks** — 变音符号折叠到 ASCII 基字符
3. **`.lower()`** — 统一小写
4. **`c.isalnum()`** — 保留所有 Unicode 字母/数字（含 CJK、西里尔），
   不用 `\w`（`\w` 含下划线 `_`，会被误保留）
5. **`re.sub(r"-{2,}", "-", s)` + `strip("-")`** — 折叠连续分隔符、去首尾

---

## GREEN — 修复后测试输出

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0
rootdir: <实验根目录>\ab-longrun-300\SE022-slugify\A-skill
plugins: anyio-4.24.0, asyncio-0.26.0, cov-6.3.0
collected 11 items

test_slugify.py::TestSlugify::test_basic_hello_world PASSED              [  9%]
test_slugify.py::TestSlugify::test_collapses_whitespace_and_punct PASSED [ 18%]
test_slugify.py::TestSlugify::test_empty_input PASSED                    [ 27%]
test_slugify.py::TestSlugify::test_lowercases PASSED                     [ 36%]
test_slugify.py::TestSlugify::test_multiple_separators_between_words PASSED [ 45%]
test_slugify.py::TestSlugify::test_numbers_kept PASSED                   [ 54%]
test_slugify.py::TestSlugify::test_pure_punctuation PASSED               [ 63%]
test_slugify.py::TestSlugify::test_strips_leading_trailing_separators PASSED [ 72%]
test_slugify.py::TestSlugify::test_strips_non_alnum PASSED               [ 81%]
test_slugify.py::TestSlugify::test_unicode_letters_retained_when_no_deaccent_needed PASSED [ 90%]
test_slugify.py::TestSlugify::test_unicode_nfkd_deaccent PASSED          [100%]

======================== 11 passed, 1 warning in 0.03s ========================
```

---

## 验收清单

- [x] 测试文件可跑 — `test_slugify.py`，11 用例
- [x] response 含修复前失败 — RED 段 7 failed / 4 passed
- [x] 修复后通过 — GREEN 段 11 passed
- [x] 边界：空串 `""` → `""`
- [x] 边界：纯标点 `"!!!"` / `"---"` / `" ,.; "` → `""`
- [x] 边界：首尾符号 `"--hello--"` → `"hello"`
- [x] 边界：多分隔符 `"one--two___three"` → `"one-two-three"`
- [x] Unicode 策略写明并测到位 — NFKD + drop marks；`Café` → `cafe`
