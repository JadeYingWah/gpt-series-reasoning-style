# response.md · SE014-slugify

## Unicode 策略（选定）

**NFKD 分解 + 剥离组合变音符 + lower**。`Café` → `cafe`（不是 `café`）。
理由：NFKD 把 `é` 拆成 `e` + combining acute，再剔除 combining 类字符，可得到纯 ASCII slug，对 URL 更友好。策略已写入测试并实测覆盖。

---

## RED（修复前）

```
python -m pytest test_slugify.py -v
```

```
FAILED test_slugify.py::TestSlugify::test_alnum_and_hyphen_only
  AssertionError: 'Hello-World-' != 'hello-world'
FAILED test_slugify.py::TestSlugify::test_collapse_runs
  AssertionError: '-multi-spaces-and-dashes-' != 'multi-spaces-and-dashes'
FAILED test_slugify.py::TestSlugify::test_hello_world
  AssertionError: 'Hello-World-' != 'hello-world'
FAILED test_slugify.py::TestSlugify::test_lower
  AssertionError: 'HELLO-World' != 'hello-world'
FAILED test_slugify.py::TestSlugify::test_pure_punctuation
  AssertionError: '-' != ''
FAILED test_slugify.py::TestSlugify::test_strip_edges
  AssertionError: '-lead-' != 'lead'
FAILED test_slugify.py::TestSlugify::test_unicode_mixed
  AssertionError: 'Caf-au-Lait-' != 'cafe-au-lait'
FAILED test_slugify.py::TestSlugify::test_unicode_nfkd
  AssertionError: 'Caf-' != 'cafe'

test_empty_string PASSED
test_numbers PASSED

8 failed, 2 passed
```

### 原实现缺陷

```python
s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
return s
```

1. 未 `.lower()` — 大写保留
2. 未 `.strip("-")` — 首尾残留 `-`
3. 纯标点输入产出 `"-"` 而非 `""`
4. 非 ASCII 字母（`é`）被当非 alnum 剥离且不做 NFKD，导致 `Café` → `Caf-`

---

## 修复

`slugify.py`：

```python
def slugify(text: str) -> str:
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s
```

处理顺序：NFKD → 去 combining → lower → 非 `[a-z0-9]` 替换为 `-` → strip 首尾 `-`。

---

## GREEN（修复后）

```
python -m pytest test_slugify.py -v
```

```
test_slugify.py::TestSlugify::test_alnum_and_hyphen_only PASSED
test_slugify.py::TestSlugify::test_collapse_runs PASSED
test_slugify.py::TestSlugify::test_empty_string PASSED
test_slugify.py::TestSlugify::test_hello_world PASSED
test_slugify.py::TestSlugify::test_lower PASSED
test_slugify.py::TestSlugify::test_numbers PASSED
test_slugify.py::TestSlugify::test_pure_punctuation PASSED
test_slugify.py::TestSlugify::test_strip_edges PASSED
test_slugify.py::TestSlugify::test_unicode_mixed PASSED
test_slugify.py::TestSlugify::test_unicode_nfkd PASSED

10 passed
```

---

## 验收清单

- [x] 测试文件可跑（pytest 10/10）
- [x] response 含修复前失败（见 RED 段）
- [x] 修复后通过（见 GREEN 段）
- [x] 边界：空串、纯标点、首尾符号、多分隔符

## 规格对照

| 规格 | 实现 |
|------|------|
| `slugify("Hello, World!")` → `"hello-world"` | ✓ |
| 连续空白/标点折叠为单个 `-` | ✓ `re.sub(r"[^a-z0-9]+", "-", s)` |
| 去掉首尾 `-` | ✓ `s.strip("-")` |
| 非字母数字（除 `-`）剥离；空串返回 `""` | ✓ |
| Unicode 字母保留小写（NFKD 策略） | ✓ `Café` → `cafe` |
