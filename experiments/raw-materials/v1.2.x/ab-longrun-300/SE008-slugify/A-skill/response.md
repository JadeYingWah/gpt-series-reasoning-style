# SE008-slugify · 阶段2 实现报告

## Unicode 策略

**选择：NFKD 归一化 + 剥离组合标记（combining marks）**

- `unicodedata.normalize("NFKD", text)` 将带变音符的拉丁字母分解为基字符 + 组合符（如 `é` → `e` + U+0301）
- 随后丢弃 Unicode 类别为 `Mn` 的组合标记
- 结果：`Café` → `cafe`，`Über` → `uber`，`naïve` → `naive`，`señor` → `senor`
- 无基字符分解的非 ASCII 字符（如 CJK、西里尔）按分隔符处理

理由：slug 的常见用途是 URL / 文件名，ASCII 输出兼容性最好。

## 实现流水

### 1. RED — 测试写完后先对缺陷实现跑失败

原始 `slugify.py`：

```python
def slugify(text: str) -> str:
    # DEFECT: no lower, no strip, collapse broken
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

缺陷：未 lower、未 strip 首尾 `-`、无 Unicode 处理。

```text
$ python -m pytest test_slugify.py -v
...
FAILED test_slugify.py::TestSlugify::test_basic_hello_world - AssertionError: 'Hello-World-' != 'hello-world'
FAILED test_slugify.py::TestSlugify::test_collapse_multiple_separators - AssertionError: '-a-b-' != 'a-b'
FAILED test_slugify.py::TestSlugify::test_leading_trailing_symbols - AssertionError: '-Hello-' != 'hello'
FAILED test_slugify.py::TestSlugify::test_mixed_case_collapses - AssertionError: 'HeLLo-WoRLD' != 'hello-world'
FAILED test_slugify.py::TestSlugify::test_non_letter_non_digit_stripped - AssertionError: '50-off-' != '50-off'
FAILED test_slugify.py::TestSlugify::test_numbers_kept - AssertionError: 'Item-42' != 'item-42'
FAILED test_slugify.py::TestSlugify::test_only_punctuation - AssertionError: '-' != ''
FAILED test_slugify.py::TestSlugify::test_single_character - AssertionError: 'A' != 'a'
FAILED test_slugify.py::TestSlugify::test_unicode_nfkd_strategy - AssertionError: 'Caf-' != 'cafe'
======================== 9 failed, 4 passed, 1 warning in 0.10s =========================
```

### 2. 修复 `slugify.py`

流水：NFKD → 丢弃 Mn → lower → 非 `[a-z0-9]` 折叠为 `-` → strip 首尾 `-`。

### 3. GREEN — 修复后全量通过

```text
$ python -m pytest test_slugify.py -v
...
test_slugify.py::TestSlugify::test_already_slug_unchanged PASSED         [  7%]
test_slugify.py::TestSlugify::test_basic_hello_world PASSED              [ 15%]
test_slugify.py::TestSlugify::test_collapse_multiple_separators PASSED   [ 23%]
test_slugify.py::TestSlugify::test_empty_string PASSED                   [ 30%]
test_slugify.py::TestSlugify::test_leading_trailing_symbols PASSED       [ 38%]
test_slugify.py::TestSlugify::test_mixed_case_collapses PASSED           [ 46%]
test_slugify.py::TestSlugify::test_non_letter_non_digit_stripped PASSED  [ 53%]
test_slugify.py::TestSlugify::test_numbers_kept PASSED                   [ 61%]
test_slugify.py::TestSlugify::test_only_punctuation PASSED               [ 69%]
test_slugify.py::TestSlugify::test_preserves_hyphen_between_words PASSED [ 76%]
test_slugify.py::TestSlugify::test_single_character PASSED               [ 84%]
test_slugify.py::TestSlugify::test_underscore_treated_as_separator PASSED [ 92%]
test_slugify.py::TestSlugify::test_unicode_nfkd_strategy PASSED          [100%]
======================== 13 passed, 1 warning in 0.02s ========================
```

## 验收清单

- [x] 测试文件可跑（`test_slugify.py`，13 用例）
- [x] response 含修复前失败（见 RED 段）
- [x] 修复后通过（13 passed）
- [x] 边界：空串、纯标点、首尾符号、多分隔符
- [x] Unicode 策略已写明并测到位（NFKD → `cafe`）

## 未删失败用例

RED 阶段全部 9 个失败用例均保留并转绿；未通过删测试变绿。
