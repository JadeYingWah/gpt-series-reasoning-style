# SE011-slugify · TDD 实施记录

工作目录：`<实验根目录>\ab-longrun-300\SE011-slugify\A-skill`

## Unicode 策略（选定）

**NFKD + 仅保留 ASCII `[a-z0-9]`**。

- `unicodedata.normalize("NFKD", text)`：使带音标的拉丁字母可分解（`Café` → `Cafe` + combining acute）。
- `.lower()` 小写化。
- `.encode("ascii", "ignore")` 丢弃 combining mark 与无法分解的非 ASCII（如 CJK）。
- 因此：`Café` → `cafe`；`naïve` → `naive`；`中文` → `""`。
- 备选策略「仅 lower 保留 Unicode 字母」会得到 `café`，本实现未采用，测试锁定 NFKD 行为。

## 1. RED — 修复前失败

先编写 `test_slugify.py`（9 个用例），对初始有缺陷的 `slugify.py` 实跑：

```
test_basic_hello_world FAILED
test_collapse_whitespace_and_punct PASSED
test_digits_kept PASSED
test_empty_and_pure_separators FAILED
test_lowercases FAILED
test_mixed_content FAILED
test_single_word PASSED
test_strip_leading_trailing_dashes FAILED
test_unicode_nfkd_strategy FAILED

FAILED test_slugify.py::TestSlugify::test_basic_hello_world - AssertionError: 'Hello-World-' != 'hello-world'
FAILED test_slugify.py::TestSlugify::test_empty_and_pure_separators - AssertionError: '-' != ''
FAILED test_slugify.py::TestSlugify::test_lowercases - AssertionError: 'ABC' != 'abc'
FAILED test_slugify.py::TestSlugify::test_mixed_content - AssertionError: 'Hello-World-Caf-123' != 'hello-world-cafe-123'
FAILED test_slugify.py::TestSlugify::test_strip_leading_trailing_dashes - AssertionError: '-hello-' != 'hello'
FAILED test_slugify.py::TestSlugify::test_unicode_nfkd_strategy - AssertionError: 'Caf-' != 'cafe'
6 failed, 3 passed
```

缺陷定位：

| 缺陷 | 表现 |
|------|------|
| 未 lower | `ABC` → `ABC` |
| 未 strip 首尾 `-` | `---hello---` → `-hello-`；`Hello, World!` → `Hello-World-` |
| 无 NFKD | `Café` → `Caf-` |
| 纯标点变 `-` | `!!!` → `-` |

## 2. 修复 `slugify.py`

```python
def slugify(text: str) -> str:
    s = unicodedata.normalize("NFKD", text)
    s = s.lower()
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s
```

未删改任何失败用例；只改实现。

## 3. GREEN — 修复后通过

```
test_slugify.py::TestSlugify::test_basic_hello_world PASSED
test_slugify.py::TestSlugify::test_collapse_whitespace_and_punct PASSED
test_slugify.py::TestSlugify::test_digits_kept PASSED
test_slugify.py::TestSlugify::test_empty_and_pure_separators PASSED
test_slugify.py::TestSlugify::test_lowercases PASSED
test_slugify.py::TestSlugify::test_mixed_content PASSED
test_slugify.py::TestSlugify::test_single_word PASSED
test_slugify.py::TestSlugify::test_strip_leading_trailing_dashes PASSED
test_slugify.py::TestSlugify::test_unicode_nfkd_strategy PASSED

9 passed, 1 warning in 0.03s
```

## 验收清单

- [x] 测试文件可跑（`python -m pytest test_slugify.py -v`）
- [x] response 含修复前失败（见 RED）
- [x] 修复后通过（9/9）
- [x] 边界：空串、纯标点、首尾符号、多分隔符
