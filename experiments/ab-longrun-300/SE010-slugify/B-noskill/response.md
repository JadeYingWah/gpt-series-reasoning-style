# SE010-slugify · RED → GREEN 记录

## Unicode 策略（notes）

选用 **NFKD 归一化 + 剥离组合记号**：`Café` → `cafe`，`Über` → `uber`，`Ångström` → `angstrom`。
目的是产出纯 ASCII URL slug；带组合变音的字母折叠为基字母，其余非字母数字（除 `-`）剥离。

---

## RED：修复前测试结果

对初始缺陷实现运行 `python -m pytest test_slugify.py -v`：

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0 -- C:\Python314\python.exe
rootdir: <实验根目录>\ab-longrun-300\SE010-slugify\B-noskill
plugins: anyio-4.10.0, asyncio-0.24.0, cov-5.0.0, mock-3.14.0, timeout-2.3.1
collected 12 items

test_slugify.py::TestSlugify::test_already_slug PASSED                   [  8%]
test_slugify.py::TestSlugify::test_basic_hello_world FAILED              [ 16%]
test_slugify.py::TestSlugify::test_collapse_whitespace_and_punctuation PASSED [ 25%]
test_slugify.py::TestSlugify::test_digits_preserved PASSED               [ 33%]
test_slugify.py::TestSlugify::test_empty_string PASSED                   [ 41%]
test_slugify.py::TestSlugify::test_mixed_case_lowered FAILED             [ 50%]
test_slugify.py::TestSlugify::test_pure_punctuation_returns_empty FAILED [ 58%]
test_slugify.py::TestSlugify::test_single_word FAILED                    [ 66%]
test_slugify.py::TestSlugify::test_strip_leading_trailing_hyphens FAILED [ 75%]
test_slugify.py::TestSlugify::test_strip_non_alnum_except_hyphen PASSED  [ 83%]
test_slugify.py::TestSlugify::test_unicode_letters_kept_when_no_decomposition FAILED [ 91%]
test_slugify.py::TestSlugify::test_unicode_nfkd_cafe FAILED              [100%]

=========================== short test summary info ===========================
FAILED test_slugify.py::TestSlugify::test_basic_hello_world - AssertionError: 'Hello-World-' != 'hello-world'
FAILED test_slugify.py::TestSlugify::test_mixed_case_lowered - AssertionError: 'MiXeD-CaSe' != 'mixed-case'
FAILED test_slugify.py::TestSlugify::test_pure_punctuation_returns_empty - AssertionError: '-' != ''
FAILED test_slugify.py::TestSlugify::test_single_word - AssertionError: 'Python' != 'python'
FAILED test_slugify.py::TestSlugify::test_strip_leading_trailing_hyphens - AssertionError: '-hello-' != 'hello'
FAILED test_slugify.py::TestSlugify::test_unicode_letters_kept_when_no_decomposition - AssertionError: '-ber' != 'uber'
FAILED test_slugify.py::TestSlugify::test_unicode_nfkd_cafe - AssertionError: 'Caf-' != 'cafe'
========================= 7 failed, 5 passed in 0.16s =========================
```

### 初始缺陷（`slugify.py` 修复前）

```python
def slugify(text: str) -> str:
    # DEFECT: no lower, no strip, collapse broken
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

失败原因归纳：
1. 不做 lower → `Hello-World-` / `Python` / `MiXeD-CaSe`
2. 不剥首尾 `-` → `-hello-` / `Hello-World-`
3. 纯标点留下孤立 `-` → `"!!!"` → `"-"` 而非 `""`
4. Unicode 字母被正则剥掉 → `Café` → `Caf-`，`Über` → `-ber`

---

## 修复

见 `slugify.py`：NFKD 归一化 + 去组合记号 + lower + `[^a-z0-9]+` → `-` + `strip("-")`。

## GREEN：修复后测试结果

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0 -- C:\Python314\python.exe
rootdir: <实验根目录>\ab-longrun-300\SE010-slugify\B-noskill
plugins: anyio-4.10.0, asyncio-0.24.0, cov-5.0.0, mock-3.14.0, timeout-2.3.1
collected 12 items

test_slugify.py::TestSlugify::test_already_slug PASSED                   [  8%]
test_slugify.py::TestSlugify::test_basic_hello_world PASSED              [ 16%]
test_slugify.py::TestSlugify::test_collapse_whitespace_and_punctuation PASSED [ 25%]
test_slugify.py::TestSlugify::test_digits_preserved PASSED               [ 33%]
test_slugify.py::TestSlugify::test_empty_string PASSED                   [ 41%]
test_slugify.py::TestSlugify::test_mixed_case_lowered PASSED             [ 50%]
test_slugify.py::TestSlugify::test_pure_punctuation_returns_empty PASSED [ 58%]
test_slugify.py::TestSlugify::test_single_word PASSED                    [ 66%]
test_slugify.py::TestSlugify::test_strip_leading_trailing_hyphens PASSED [ 75%]
test_slugify.py::TestSlugify::test_strip_non_alnum_except_hyphen PASSED  [ 83%]
test_slugify.py::TestSlugify::test_unicode_letters_kept_when_no_decomposition PASSED [ 91%]
test_slugify.py::TestSlugify::test_unicode_nfkd_cafe PASSED              [100%]

======================== 12 passed, 1 warning in 0.04s ========================
```

## 验收清单

- [x] 测试文件可跑（`python -m pytest test_slugify.py`）
- [x] response 含修复前失败（7 failed / 5 passed）
- [x] 修复后通过（12 passed）
- [x] 边界：空串、纯标点、首尾符号、多分隔符
