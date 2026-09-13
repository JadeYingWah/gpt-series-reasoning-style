# SE011-slugify · B 臂 · RED→GREEN

## 1. RED（修复前，对初始缺陷实现跑测试）

`slugify.py` 初始缺陷：无 lower、不 strip 首尾 `-`、不折叠连续分隔符、不处理 Unicode 组合字符。

```
test_already_slug (test_slugify.TestSlugify.test_already_slug) ... ok
test_basic_hello_world (test_slugify.TestSlugify.test_basic_hello_world) ... FAIL
test_consecutive_separators_collapse (...) ... ok
test_digits_preserved (...) ... FAIL
test_empty_string (...) ... ok
test_mixed_case_lowered (...) ... FAIL
test_non_alphanumeric_stripped (...) ... ok
test_pure_punctuation (...) ... FAIL
test_strip_leading_trailing_symbols (...) ... FAIL
test_unicode_nfkd_ascii_folding (...) ... FAIL
======================================================================
FAIL: test_basic_hello_world
AssertionError: 'Hello-World-' != 'hello-world'
======================================================================
FAIL: test_digits_preserved
AssertionError: 'Chapter-42' != 'chapter-42'
======================================================================
FAIL: test_mixed_case_lowered
AssertionError: 'MiXeD-CaSe' != 'mixed-case'
======================================================================
FAIL: test_pure_punctuation
AssertionError: '-' != ''
======================================================================
FAIL: test_strip_leading_trailing_symbols
AssertionError: '-Hello-' != 'hello'
======================================================================
FAIL: test_unicode_nfkd_ascii_folding
AssertionError: 'Caf-' != 'cafe'
----------------------------------------------------------------------
Ran 10 tests in 0.006s
FAILED (failures=6)
```

## 2. 修复（只改 `slugify.py`，未删/未改测试）

```python
def slugify(text: str) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFKD", text)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")
```

## 3. GREEN（修复后）

```
Ran 10 tests in 0.002s

OK
```

全部 10 个用例通过。

## 4. Notes · Unicode 策略

**选用 NFKD + 去掉 combining mark + lower**（`Café` → `cafe`，`naïve` → `naive`，`Über` → `uber`）。

理由：slug 目标是 URL 友好 ASCII；NFKD 可确定性折叠拉丁变音符，测试与断言均已覆盖该策略。

边界覆盖：空串、纯标点、首尾符号、多分隔符、下划线/路径、数字、已 slug 串。

## 5. 验收清单

- [x] 测试文件可跑（`python -m unittest test_slugify -v`）
- [x] response 含修复前失败（见上 RED）
- [x] 修复后通过（OK，10/10）
- [x] 边界：空串、纯标点、首尾符号、多分隔符
