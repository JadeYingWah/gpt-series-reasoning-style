# Response — SE006-slugify

## Unicode 策略（必须声明）

**选择：NFKD 分解 + 丢弃非 ASCII**（`Café` → `cafe`，不是 `café`）。

理由：生成纯 ASCII slug，对 URL / CDN / 遗留系统最可移植。NFKD 先把 `é` 分解为 `e` + combining accent，再 `encode("ascii", "ignore")` 丢掉组合符号。

已在 `test_unicode_nfkd_strategy` 与 `test_mixed_unicode_and_ascii` 中测到位。

---

## 初始缺陷

原 `slugify.py` 仅做 `re.sub(r"[^a-zA-Z0-9]+", "-", text)`：

- 未 lower → `"Hello-World-"`
- 未 strip 首尾 `-` → 尾标点变成尾部 `-`
- 纯标点 → `"-"` 而非 `""`
- Unicode 字母被直接剥掉且不在 NFKD 层处理 → `"Caf-"`

---

## RED（修复前，5 failed / 5 passed）

```
test_slugify.py::TestSlugify::test_alphanumeric_preserved PASSED         [ 10%]
test_slugify.py::TestSlugify::test_basic_hello_world FAILED              [ 20%]
test_slugify.py::TestSlugify::test_collapse_whitespace_and_punctuation PASSED [ 30%]
test_slugify.py::TestSlugify::test_empty_string PASSED                   [ 40%]
test_slugify.py::TestSlugify::test_hyphen_preserved_inside PASSED        [ 50%]
test_slugify.py::TestSlugify::test_mixed_unicode_and_ascii FAILED        [ 60%]
test_slugify.py::TestSlugify::test_numbers_only PASSED                   [ 70%]
test_slugify.py::TestSlugify::test_only_punctuation_returns_empty FAILED [ 80%]
test_slugify.py::TestSlugify::test_strip_leading_trailing_separators FAILED [ 90%]
test_slugify.py::TestSlugify::test_unicode_nfkd_strategy FAILED          [100%]

FAIL: test_basic_hello_world
AssertionError: 'Hello-World-' != 'hello-world'

FAIL: test_mixed_unicode_and_ascii
AssertionError: 'Caf-au-Lait-' != 'cafe-au-lait'

FAIL: test_only_punctuation_returns_empty
AssertionError: '-' != ''

FAIL: test_strip_leading_trailing_separators
AssertionError: '-hello-' != 'hello'

FAIL: test_unicode_nfkd_strategy
AssertionError: 'Caf-' != 'cafe'

========================= 5 failed, 5 passed =========================
```

---

## 修复

`slugify.py` 改为：

1. `unicodedata.normalize("NFKD", text)` — 分解变音符号
2. `encode("ascii", "ignore").decode("ascii")` — 丢弃非 ASCII
3. `text.lower()`
4. `re.sub(r"[^a-z0-9]+", "-", s)` — 连续非字母数字折叠为单个 `-`
5. `s.strip("-")` — 去掉首尾 `-`

---

## GREEN（修复后，10 passed）

```
test_slugify.py::TestSlugify::test_alphanumeric_preserved PASSED         [ 10%]
test_slugify.py::TestSlugify::test_basic_hello_world PASSED              [ 20%]
test_slugify.py::TestSlugify::test_collapse_whitespace_and_punctuation PASSED [ 30%]
test_slugify.py::TestSlugify::test_empty_string PASSED                   [ 40%]
test_slugify.py::TestSlugify::test_hyphen_preserved_inside PASSED        [ 50%]
test_slugify.py::TestSlugify::test_mixed_unicode_and_ascii PASSED        [ 60%]
test_slugify.py::TestSlugify::test_numbers_only PASSED                   [ 70%]
test_slugify.py::TestSlugify::test_only_punctuation_returns_empty PASSED [ 80%]
test_slugify.py::TestSlugify::test_strip_leading_trailing_separators PASSED [ 90%]
test_slugify.py::TestSlugify::test_unicode_nfkd_strategy PASSED          [100%]

======================== 10 passed, 1 warning in 0.02s ========================
```

---

## 验收清单

- [x] 测试文件可跑（`python -m pytest test_slugify.py`）
- [x] response 含修复前失败（RED 段）
- [x] 修复后通过（GREEN 段）
- [x] 边界：空串、纯标点、首尾符号、多分隔符

## 禁止项确认

- 未删失败用例
- 未只改测试；`slugify.py` 已同步修复
