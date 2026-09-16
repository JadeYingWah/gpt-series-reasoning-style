# 阶段2 · 实现响应（RED → 修复 → GREEN）

## Unicode 策略声明

**选用 NFKD 分解 + 剥离组合标记（Mn）**，再 lower、折叠非 `[a-z0-9]`、去首尾 `-`。

| 输入 | 输出 | 说明 |
|------|------|------|
| `Café` | `cafe` | NFKD 把 é 分解为 e + U+0301，丢掉 combining mark |
| `Cafe\u0301`（NFD 形式） | `cafe` | 同上，已是分解形式 |
| `über` | `uber` | ü → u + diaeresis，丢掉 diaeresis |
| `你好 世界` | `""` | CJK 无 ASCII 折叠，整段非 `[a-z0-9]`，strip 后空串 |
| `Hello 世界 World` | `hello-world` | CJK 段折成 `-` 再 strip |

未选「仅 lower」策略：那会保留 `café` 中的 `é`，需在正则里放行 Unicode 字母，slug 对 URL 不够友好。

## 修复前（RED）

```bash
python -m pytest test_slugify.py -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-6.3.0
rootdir: <实验根目录>\ab-longrun-300\SE007-slugify\A-skill
collecting ... collected 19 items

test_slugify.py::TestSlugifyBasic::test_already_slug PASSED              [  5%]
test_slugify.py::TestSlugifyBasic::test_empty_string PASSED              [ 10%]
test_slugify.py::TestSlugifyBasic::test_hello_world FAILED               [ 15%]
test_slugify.py::TestSlugifyBasic::test_leading_trailing_hyphen FAILED   [ 21%]
test_slugify.py::TestSlugifyBasic::test_leading_trailing_punctuation FAILED [ 26%]
test_slugify.py::TestSlugifyBasic::test_leading_trailing_whitespace FAILED [ 31%]
test_slugify.py::TestSlugifyCollapse::test_mixed_case_lowered FAILED     [ 36%]
test_slugify.py::TestSlugifyCollapse::test_mixed_separators PASSED       [ 42%]
test_slugify.py::TestSlugifyCollapse::test_mixed_whitespace_and_punct FAILED [ 47%]
test_slugify.py::TestSlugifyCollapse::test_multiple_spaces PASSED        [ 52%]
test_slugify.py::TestSlugifyCollapse::test_numbers_kept PASSED           [ 57%]
test_slugify.py::TestSlugifyCollapse::test_only_punctuation FAILED       [ 63%]
test_slugify.py::TestSlugifyCollapse::test_only_whitespace FAILED        [ 68%]
test_slugify.py::TestSlugifyCollapse::test_underscores_stripped_to_sep PASSED [ 73%]
test_slugify.py::TestSlugifyUnicode::test_cafe_nfd FAILED                [ 78%]
test_slugify.py::TestSlugifyUnicode::test_chinese_stripped FAILED        [ 84%]
test_slugify.py::TestSlugifyUnicode::test_german_umlaut FAILED           [ 89%]
test_slugify.py::TestSlugifyUnicode::test_mixed_latin_cjk FAILED         [ 94%]
test_slugify.py::TestSlugifyUnicode::test_nfd_form FAILED                [100%]

============================== short test summary info ==========================
FAILED test_slugify.py::TestSlugifyBasic::test_hello_world - AssertionError: 'Hello-World-' != 'hello-world'
FAILED test_slugify.py::TestSlugifyBasic::test_leading_trailing_hyphen - AssertionError: '-hello-' != 'hello'
FAILED test_slugify.py::TestSlugifyBasic::test_leading_trailing_punctuation - AssertionError: '-hello-' != 'hello'
FAILED test_slugify.py::TestSlugifyBasic::test_leading_trailing_whitespace - AssertionError: '-hello-' != 'hello'
FAILED test_slugify.py::TestSlugifyCollapse::test_mixed_case_lowered - AssertionError: 'FooBar-BAZ' != 'foobar-baz'
FAILED test_slugify.py::TestSlugifyCollapse::test_mixed_whitespace_and_punct - AssertionError: 'hello-world-' != 'hello-world'
FAILED test_slugify.py::TestSlugifyCollapse::test_only_punctuation - AssertionError: '-' != ''
FAILED test_slugify.py::TestSlugifyCollapse::test_only_whitespace - AssertionError: '-' != ''
FAILED test_slugify.py::TestSlugifyUnicode::test_cafe_nfd - AssertionError: 'Caf-' != 'cafe'
FAILED test_slugify.py::TestSlugifyUnicode::test_chinese_stripped - AssertionError: '-' != ''
FAILED test_slugify.py::TestSlugifyUnicode::test_german_umlaut - AssertionError: '-ber' != 'uber'
FAILED test_slugify.py::TestSlugifyUnicode::test_mixed_latin_cjk - AssertionError: 'Hello-World' != 'hello-world'
FAILED test_slugify.py::TestSlugifyUnicode::test_nfd_form - AssertionError: 'Cafe-' != 'cafe'
=========================== 13 failed, 6 passed, 1 warning in 0.11s ===========
```

**缺陷根因**（原实现只有一行 `re.sub(r"[^a-zA-Z0-9]+", "-", text)`）：

1. 无 `.lower()` — 大小写保留
2. 无 `.strip("-")` — 首尾分隔符残留
3. 正则不含 Unicode 字母 — `é`/`ü` 直接被剥成 `-`
4. 空/纯标点输入折叠成 `"-"` 而非 `""`

## 修复

`slugify.py` 重写为五步：NFKD → 丢 combining marks → lower → 折叠非 `[a-z0-9]` → strip `-`。

## 修复后（GREEN）

```bash
python -m pytest test_slugify.py -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.4.2, pluggy-6.3.0
rootdir: <实验根目录>\ab-longrun-300\SE007-slugify\A-skill
collecting ... collected 19 items

test_slugify.py::TestSlugifyBasic::test_already_slug PASSED              [  5%]
test_slugify.py::TestSlugifyBasic::test_empty_string PASSED              [ 10%]
test_slugify.py::TestSlugifyBasic::test_hello_world PASSED               [ 15%]
test_slugify.py::TestSlugifyBasic::test_leading_trailing_hyphen PASSED   [ 21%]
test_slugify.py::TestSlugifyBasic::test_leading_trailing_punctuation PASSED [ 26%]
test_slugify.py::TestSlugifyBasic::test_leading_trailing_whitespace PASSED [ 31%]
test_slugify.py::TestSlugifyCollapse::test_mixed_case_lowered PASSED     [ 36%]
test_slugify.py::TestSlugifyCollapse::test_mixed_separators PASSED       [ 42%]
test_slugify.py::TestSlugifyCollapse::test_mixed_whitespace_and_punct PASSED [ 47%]
test_slugify.py::TestSlugifyCollapse::test_multiple_spaces PASSED        [ 52%]
test_slugify.py::TestSlugifyCollapse::test_numbers_kept PASSED           [ 57%]
test_slugify.py::TestSlugifyCollapse::test_only_punctuation PASSED       [ 63%]
test_slugify.py::TestSlugifyCollapse::test_only_whitespace PASSED        [ 68%]
test_slugify.py::TestSlugifyCollapse::test_underscores_stripped_to_sep PASSED [ 73%]
test_slugify.py::TestSlugifyUnicode::test_cafe_nfd PASSED                [ 78%]
test_slugify.py::TestSlugifyUnicode::test_chinese_stripped PASSED        [ 84%]
test_slugify.py::TestSlugifyUnicode::test_german_umlaut PASSED           [ 89%]
test_slugify.py::TestSlugifyUnicode::test_mixed_latin_cjk PASSED         [ 94%]
test_slugify.py::TestSlugifyUnicode::test_nfd_form PASSED                [100%]

============================== warnings summary ===============================
(1 unrelated asyncio deprecation warning)
======================== 19 passed, 1 warning in 0.03s ========================
```

## 验收清单

- [x] 测试文件可跑（`test_slugify.py`，19 cases）
- [x] response 含修复前失败（13 failed / 6 passed）
- [x] 修复后通过（19 passed）
- [x] 边界：空串、纯标点、首尾符号、多分隔符（均有用例）
- [x] Unicode 策略写明（NFKD + strip Mn）并测到位（Café / NFD / ü / CJK / 混排）

## 文件

| 文件 | 动作 |
|------|------|
| `test_slugify.py` | 新建 |
| `slugify.py` | 修复 |
| `response.md` | 新建（本文件） |
