# SE010-slugify · RED → GREEN 记录（A-skill）

## Unicode 策略（notes）

选用 **NFKD 归一化 + 剥离组合记号 + 仅保留 ASCII `[a-z0-9-]`**。

| 输入 | 输出 | 说明 |
|------|------|------|
| `Café` | `cafe` | `é` = `e` + combining acute → 去记号后为 `e` |
| `Über` | `uber` | `Ü` 分解为 `U` + combining diaeresis |
| `Ångström` | `angstrom` | `Å`/`ö` 同理折叠为基字母 |
| `中文 English` | `english` | CJK 无兼容 ASCII 分解 → 剥离 |

目的：产出纯 ASCII URL slug。任务规格允许「`Café` → `cafe` 若做 NFKD，或 `café` 若仅 lower」——本实现选 NFKD 路径，并在测试中钉死。

---

## RED：修复前测试结果

对初始缺陷实现运行 `python -m pytest test_slugify.py -v --tb=line`：

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: <实验根目录>\ab-longrun-300\SE010-slugify\A-skill
plugins: anyio-4.14.2, asyncio-0.26.0, cov-6.3.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 13 items

test_slugify.py::TestSlugifySpec::test_already_slug_unchanged PASSED     [  7%]
test_slugify.py::TestSlugifySpec::test_consecutive_whitespace_and_punctuation_collapse PASSED [ 15%]
test_slugify.py::TestSlugifySpec::test_digits_preserved FAILED           [ 23%]
test_slugify.py::TestSlugifySpec::test_empty_string PASSED               [ 30%]
test_slugify.py::TestSlugifySpec::test_hello_world FAILED                [ 38%]
test_slugify.py::TestSlugifySpec::test_mixed_script_non_decomposable_letter_dropped FAILED [ 46%]
test_slugify.py::TestSlugifySpec::test_non_alnum_stripped_except_hyphen PASSED [ 53%]
test_slugify.py::TestSlugifySpec::test_pure_punctuation_returns_empty FAILED [ 61%]
test_slugify.py::TestSlugifySpec::test_single_word_lowered FAILED        [ 69%]
test_slugify.py::TestSlugifySpec::test_strip_leading_and_trailing_hyphens FAILED [ 76%]
test_slugify.py::TestSlugifySpec::test_unicode_nfkd_angstrom FAILED      [ 84%]
test_slugify.py::TestSlugifySpec::test_unicode_nfkd_cafe FAILED          [ 92%]
test_slugify.py::TestSlugifySpec::test_unicode_nfkd_ueber FAILED         [100%]

================================== FAILURES ===================================
C:\Python314\Lib\unittest\case.py:750: AssertionError: 'Chapter-12-Part-3' != 'chapter-12-part-3'
C:\Python314\Lib\unittest\case.py:750: AssertionError: 'Hello-World-' != 'hello-world'
C:\Python314\Lib\unittest\case.py:750: AssertionError: '-English' != 'english'
C:\Python314\Lib\unittest\case.py:750: AssertionError: '-' != ''
C:\Python314\Lib\unittest\case.py:750: AssertionError: 'Python' != 'python'
C:\Python314\Lib\unittest\case.py:750: AssertionError: '-hello-' != 'hello'
C:\Python314\Lib\unittest\case.py:750: AssertionError: '-ngstr-m' != 'angstrom'
C:\Python314\Lib\unittest\case.py:750: AssertionError: 'Caf-' != 'cafe'
C:\Python314\Lib\unittest\case.py:750: AssertionError: '-ber' != 'uber'
============================== warnings summary ===============================
test_slugify.py::TestSlugifySpec::test_already_slug_unchanged
  <用户目录>\AppData\Roaming\Python\Python314\site-packages\pytest_asyncio\plugin.py:1216: DeprecationWarning: 'asyncio.get_event_loop_policy' is deprecated and slated for removal in Python 3.16
    return asyncio.get_event_loop_policy()

-- Docs: https://docs.pytest.org/en/stable/warnings.html
=================== 9 failed, 4 passed, 1 warning in 0.04s ====================
```

### 初始缺陷（`slugify.py` 修复前）

```python
def slugify(text: str) -> str:
    # DEFECT: no lower, no strip, collapse broken
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

失败原因归纳：

1. 不做 lower → `Hello-World-` / `Python` / `Chapter-12-Part-3`
2. 不剥首尾 `-` → `-hello-` / `Hello-World-`
3. 纯标点留下孤立 `-` → `"!!!"` → `"-"` 而非 `""`
4. Unicode 字母被 `[^a-zA-Z0-9]` 正则剥掉 → `Café` → `Caf-`，`Über` → `-ber`，`Ångström` → `-ngstr-m`
5. CJK 前导残留连字符 → `"中文 English"` → `"-English"`

---

## 修复

`slugify.py`：NFKD 归一化 → 去组合记号 → lower → `[^a-z0-9]+` 折叠为 `-` → `strip("-")`。

## GREEN：修复后测试结果

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: <实验根目录>\ab-longrun-300\SE010-slugify\A-skill
plugins: anyio-4.14.2, asyncio-0.26.0, cov-6.3.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 13 items

test_slugify.py::TestSlugifySpec::test_already_slug_unchanged PASSED     [  7%]
test_slugify.py::TestSlugifySpec::test_consecutive_whitespace_and_punctuation_collapse PASSED [ 15%]
test_slugify.py::TestSlugifySpec::test_digits_preserved PASSED           [ 23%]
test_slugify.py::TestSlugifySpec::test_empty_string PASSED               [ 30%]
test_slugify.py::TestSlugifySpec::test_hello_world PASSED                [ 38%]
test_slugify.py::TestSlugifySpec::test_mixed_script_non_decomposable_letter_dropped PASSED [ 46%]
test_slugify.py::TestSlugifySpec::test_non_alnum_stripped_except_hyphen PASSED [ 53%]
test_slugify.py::TestSlugifySpec::test_pure_punctuation_returns_empty PASSED [ 61%]
test_slugify.py::TestSlugifySpec::test_single_word_lowered PASSED        [ 69%]
test_slugify.py::TestSlugifySpec::test_strip_leading_and_trailing_hyphens PASSED [ 76%]
test_slugify.py::TestSlugifySpec::test_unicode_nfkd_angstrom PASSED      [ 84%]
test_slugify.py::TestSlugifySpec::test_unicode_nfkd_cafe PASSED          [ 92%]
test_slugify.py::TestSlugifySpec::test_unicode_nfkd_ueber PASSED         [100%]

============================== warnings summary ===============================
test_slugify.py::TestSlugifySpec::test_already_slug_unchanged
  <用户目录>\AppData\Roaming\Python\Python314\site-packages\pytest_asyncio\plugin.py:1216: DeprecationWarning: 'asyncio.get_event_loop_policy' is deprecated and slated for removal in Python 3.16
    return asyncio.get_event_loop_policy()

-- Docs: https://docs.pytest.org/en/stable/warnings.html
======================== 13 passed, 1 warning in 0.04s ========================
```

## 验收清单

- [x] 测试文件可跑（`python -m pytest test_slugify.py`）
- [x] response 含修复前失败（9 failed / 4 passed）
- [x] 修复后通过（13 passed）
- [x] 边界：空串、纯标点、首尾符号、多分隔符
- [x] 未删失败用例变绿；未只改测试
