# Response — SE021-slugify (A-skill 阶段2)

## Unicode 策略（必须声明）

**选用：NFKD 分解 + 剥离组合记号（combining marks）+ lower。**

| 输入 | 期望 | 说明 |
| --- | --- | --- |
| `Café` | `cafe` | NFKD 把 `é` 拆成 `e` + U+0301，去掉记号后得 `Cafe` → lower `cafe` |
| `naïve` | `naive` | 同上 |
| `Ångström` | `angstrom` | `Å`→`A`+U+030A 去记号；`ö`→`o` |
| `中文` | `中文` | NFKD 无法折成 ASCII 的字母保留（仅 lower，无变化） |
| `ЖЖЖ` | `жжж` | 西里尔字母保留并小写化 |

理由：slug 主要用于 URL/文件名；拉丁变音折成 ASCII 兼容性最好。非拉丁文字（CJK/西里尔等）不可合理 ASCII 化，按规格「Unicode 字母保留小写形式」原样保留。

## 1. RED — 修复前跑失败

初始缺陷 seed（`seed_slugify()` 等价）：

```python
def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

实跑行为：

```
'Hello, World!' -> 'Hello-World-'
'Café'         -> 'Caf-'
''             -> ''
'!!!'          -> '-'
'  ---  '      -> '-'
'foo--bar'     -> 'foo-bar'
'  Foo  Bar  ' -> '-Foo-Bar-'
```

`python -m pytest test_slugify.py -v`：

```
test_empty_string PASSED
test_keeps_digits PASSED
其余 9 项 FAILED

FAILED test_basic_hello_world              — AssertionError: 'Hello-World-' != 'hello-world'
FAILED test_collapses_whitespace_and_punct_to_single_dash — '-Foo-Bar-' != 'foo-bar'
FAILED test_lowercase                      — 'HELLO' != 'hello'
FAILED test_mixed_unicode_and_ascii        — 'Caf-au-Lait-' != 'cafe-au-lait'
FAILED test_non_alnum_stripped_except_dash — 'a-b' != 'ab'
FAILED test_pure_punct_or_whitespace_returns_empty — '-' != ''
FAILED test_strips_leading_trailing_dashes — '-Hello-World-' != 'hello-world'
FAILED test_unicode_letters_without_decomposable_accent — '-' != '中文'
FAILED test_unicode_nfkd_deaccent          — 'Caf-' != 'cafe'

======================== 9 failed, 2 passed ========================
```

缺陷对应：

| 缺陷 | 表现 |
| --- | --- |
| 无 `.lower()` | `HELLO` / `Hello-World-` |
| 无 NFKD / deaccent | `Café` → `Caf-` |
| 无 `strip("-")` | 首尾悬挂 `-` |
| 纯标点/空白未特判 | `!!!` → `-` |
| 下划线被当分隔符 | `a_b` → `a-b`（规格要求剥离非字母数字） |
| 非 ASCII 字母被 `[a-zA-Z0-9]` 剥掉 | `中文` → `-` |

## 2. 修复 slugify.py

策略与顺序：

1. `unicodedata.normalize("NFKD", text)`
2. 去掉 `unicodedata.combining(ch)` 真的字符
3. `.lower()`
4. 先 `replace("_", "")`（下划线是非字母数字，剥离而非变成分隔符）
5. `re.sub(r"[^\w]+", "-", s)` 折叠连续非字母数字为单个 `-`（`\w` Unicode-aware，保留 CJK/西里尔等字母数字）
6. `re.sub(r"-{2,}", "-", s)` + `strip("-")` 收尾

## 3. GREEN — 修复后通过

`python -m pytest test_slugify.py -v`：

```
test_slugify.py::TestSlugify::test_basic_hello_world PASSED
test_slugify.py::TestSlugify::test_collapses_whitespace_and_punct_to_single_dash PASSED
test_slugify.py::TestSlugify::test_empty_string PASSED
test_slugify.py::TestSlugify::test_keeps_digits PASSED
test_slugify.py::TestSlugify::test_lowercase PASSED
test_slugify.py::TestSlugify::test_mixed_unicode_and_ascii PASSED
test_slugify.py::TestSlugify::test_non_alnum_stripped_except_dash PASSED
test_slugify.py::TestSlugify::test_pure_punct_or_whitespace_returns_empty PASSED
test_slugify.py::TestSlugify::test_strips_leading_trailing_dashes PASSED
test_slugify.py::TestSlugify::test_unicode_letters_without_decomposable_accent PASSED
test_slugify.py::TestSlugify::test_unicode_nfkd_deaccent PASSED

======================== 11 passed, 1 warning in 0.03s ========================
```

规格点验：

- `slugify("Hello, World!")` → `hello-world` ✓
- 连续空白/标点折叠为单个 `-` ✓
- 去掉首尾 `-` ✓
- 非字母数字（除 `-`）剥离；空串 → `""` ✓
- Unicode：NFKD 策略，`Café` → `cafe`；不可分解字母小写保留 ✓

## 4. 验收清单

- [x] 测试文件可跑（`test_slugify.py`，unittest 风格，pytest 可收集）
- [x] response 含修复前失败（§1 RED 实跑输出）
- [x] 修复后通过（§3，11 passed）
- [x] 边界：空串、纯标点、首尾符号、多分隔符（均有用例）
- [x] 未删失败用例变绿；未只改测试（同时修了 `slugify.py`）

## 文件

- `test_slugify.py` — 11 项测试
- `slugify.py` — 修复后实现
- `response.md` — 本文件
