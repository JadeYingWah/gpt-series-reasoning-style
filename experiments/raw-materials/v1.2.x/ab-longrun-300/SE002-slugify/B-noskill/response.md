# SE002-slugify · B-noskill · response.md

## 策略说明（Unicode）

**选择 NFKD 策略**：`unicodedata.normalize("NFKD", text)` 后剥离 combining marks（Mn），再 `lower()`。

- `Café` → `cafe`
- `naïve` → `naive`
- `Über` → `uber`（ü 分解为 u + combining diaeresis，去掉 diaeresis 后为 u；**不是** ss）
- `Crème Brûlée` → `creme-brulee`
- 非拉丁（CJK 等）经 NFKD 后仍非 `[a-z0-9]`，折叠为分隔符并被 strip，如 `你好` → `""`，`hello 你好 world` → `hello-world`

未选用「仅 lower」策略（那样会得到 `café` 且含非 ASCII 字符）。

---

## RED（修复前）

原始实现（缺陷）：

```python
def slugify(text: str) -> str:
    # DEFECT: no lower, no strip, collapse broken
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

主要缺陷：
1. 不 lower
2. 不 strip 首尾 `-`
3. 纯标点/纯空白变成 `"-"` 而非 `""`
4. Unicode 字母被直接当成非字母数字剥掉，变成交替的 `-`

### RED 输出（pytest）

```
platform win32 -- Python 3.14.5, pytest-8.4.2
collected 17 items

test_slugify.py::TestBasic::test_hello_world FAILED                      [  5%]
test_slugify.py::TestBasic::test_already_slug PASSED                     [ 11%]
test_slugify.py::TestBasic::test_lowercases FAILED                       [ 17%]
test_slugify.py::TestCollapseAndStrip::test_collapse_whitespace PASSED   [ 23%]
test_slugify.py::TestCollapseAndStrip::test_collapse_punctuation_run PASSED [ 29%]
test_slugify.py::TestCollapseAndStrip::test_mixed_separators PASSED      [ 35%]
test_slugify.py::TestCollapseAndStrip::test_strip_leading_trailing FAILED [ 41%]
test_slugify.py::TestEdgeCases::test_empty_string PASSED                 [ 47%]
test_slugify.py::TestEdgeCases::test_pure_punctuation FAILED             [ 52%]
test_slugify.py::TestEdgeCases::test_leading_trailing_symbols FAILED     [ 58%]
test_slugify.py::TestEdgeCases::test_multiple_separators_between_words PASSED [ 64%]
test_slugify.py::TestEdgeCases::test_digits_kept FAILED                  [ 70%]
test_slugify.py::TestUnicodeNfkd::test_cafe FAILED                       [ 76%]
test_slugify.py::TestUnicodeNfkd::test_nacl FAILED                       [ 82%]
test_slugify.py::TestUnicodeNfkd::test_german_ish FAILED                 [ 88%]
test_slugify.py::TestUnicodeNfkd::test_mixed_unicode_sentence FAILED     [ 94%]
test_slugify.py::TestUnicodeNfkd::test_non_latin_stripped FAILED         [100%]

============================== short test summary info ==============================
FAILED test_slugify.py::TestBasic::test_hello_world - AssertionError: assert 'Hello-World-' == 'hello-world'
FAILED test_slugify.py::TestBasic::test_lowercases - AssertionError: assert 'Hello' == 'hello'
FAILED test_slugify.py::TestCollapseAndStrip::test_strip_leading_trailing - AssertionError: assert '-hello-' == 'hello'
FAILED test_slugify.py::TestEdgeCases::test_pure_punctuation - AssertionError: assert '-' == ''
FAILED test_slugify.py::TestEdgeCases::test_leading_trailing_symbols - AssertionError: assert '-lead-and-trail-' == 'lead-and-trail'
FAILED test_slugify.py::TestEdgeCases::test_digits_kept - AssertionError: assert 'Item-42' == 'item-42'
FAILED test_slugify.py::TestUnicodeNfkd::test_cafe - AssertionError: assert 'Caf-' == 'cafe'
FAILED test_slugify.py::TestUnicodeNfkd::test_nacl - AssertionError: assert 'na-ve' == 'naive'
FAILED test_slugify.py::TestUnicodeNfkd::test_german_ish - AssertionError: assert '-ber' == 'uber'
FAILED test_slugify.py::TestUnicodeNfkd::test_mixed_unicode_sentence - AssertionError: assert 'Cr-me-Br-l-e' == 'creme-brulee'
FAILED test_slugify.py::TestUnicodeNfkd::test_non_latin_stripped - AssertionError: assert '-' == ''
============================== 11 failed, 6 passed, 1 warning in 0.15s ==============================
```

---

## 修复

`slugify.py` 改为：

1. NFKD normalize
2. 去掉 combining marks
3. lower
4. `[^a-z0-9]+` → `-`
5. `.strip("-")`

空输入直接返回 `""`。

---

## GREEN（修复后）

```
platform win32 -- Python 3.14.5, pytest-8.4.2
collected 17 items

test_slugify.py::TestBasic::test_hello_world PASSED                      [  5%]
test_slugify.py::TestBasic::test_already_slug PASSED                     [ 11%]
test_slugify.py::TestBasic::test_lowercases PASSED                       [ 17%]
test_slugify.py::TestCollapseAndStrip::test_collapse_whitespace PASSED   [ 23%]
test_slugify.py::TestCollapseAndStrip::test_collapse_punctuation_run PASSED [ 29%]
test_slugify.py::TestCollapseAndStrip::test_mixed_separators PASSED      [ 35%]
test_slugify.py::TestCollapseAndStrip::test_strip_leading_trailing PASSED [ 41%]
test_slugify.py::TestEdgeCases::test_empty_string PASSED                 [ 47%]
test_slugify.py::TestEdgeCases::test_pure_punctuation PASSED             [ 52%]
test_slugify.py::TestEdgeCases::test_leading_trailing_symbols PASSED     [ 58%]
test_slugify.py::TestEdgeCases::test_multiple_separators_between_words PASSED [ 64%]
test_slugify.py::TestEdgeCases::test_digits_kept PASSED                  [ 70%]
test_slugify.py::TestUnicodeNfkd::test_cafe PASSED                       [ 76%]
test_slugify.py::TestUnicodeNfkd::test_nacl PASSED                       [ 82%]
test_slugify.py::TestUnicodeNfkd::test_german_ish PASSED                 [ 88%]
test_slugify.py::TestUnicodeNfkd::test_mixed_unicode_sentence PASSED     [ 94%]
test_slugify.py::TestUnicodeNfkd::test_non_latin_stripped PASSED         [100%]

============================== 17 passed, 1 warning in 0.04s ===============================
```

---

## 验收清单

- [x] 测试文件可跑（`python -m pytest test_slugify.py -v`）
- [x] response 含修复前失败（见 RED 段）
- [x] 修复后通过（17 passed）
- [x] 边界：空串、纯标点、首尾符号、多分隔符
  - `""` → `""`
  - `"..."` / `"?!@#$%"` / `" \t\n "` → `""`
  - `"***lead and trail***"` → `lead-and-trail`
  - `"a---b---c"` / `"one,, two -- three!! four"` → 折叠为单 `-`

未删除任何失败用例；仅修改了 `slugify.py` 实现（测试在 RED 与 GREEN 期间保持不变）。
