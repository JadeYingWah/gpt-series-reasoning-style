# Response — SE003-slugify 阶段2 实现

工作目录：`<实验根目录>\ab-longrun-300\SE003-slugify\A-skill`

## 形态与门禁

- 形态：单 Agent 主干（无并行/隔离需求）。
- 风险：轻 — 单目录小 Python 模块 + 测试，完全可逆、无外部副作用。
- 门禁：用户指令「阶段2·实现。先 RED 再修 slugify.py 到 GREEN」具体完整，按轻通道 **指令即授权**，直接执行。
- 资源盘点：本地仅有任务给定的 `slugify.py` 缺陷种子与 `task.md` 规格；标准库 `unittest` / `unicodedata` / `re` 足够，无需额外依赖。

## Unicode 策略（选定并测到位）

**选 NFKD 折叠为 ASCII**，不是「仅 lower」。

理由与行为：

1. `unicodedata.normalize("NFKD", text)` 分解重音：`é` → `e` + combining acute。
2. 去掉 combining marks，只留基字母 → `Café` / `café` → `cafe`；`naïve` → `naive`；`Über` → `uber`；`résumé` → `resume`；`Ñoño` → `nono`。
3. 折叠后仅 `[A-Za-z0-9]` 为内容字符；其余（含 CJK 等不可分解为 ASCII 的字母）一律作分隔符，首尾再 strip。
4. 因此 `中文` → `""`，`hello中文world` → `hello-world`（已测）。

对照备选：若只 `lower` 不做 NFKD，则 `Café` → `café`（保留非 ASCII）。本实现不采用该策略，测试按 NFKD 断言。

## 步骤与实跑

### 1. 先写 `test_slugify.py`（未改实现）

覆盖：规格五条 + 验收边界（空串、纯标点、纯空白、首尾符号、多分隔符、已是 slug、数字、Unicode）。

### 2. RED — 对缺陷种子跑测

```text
python -m unittest test_slugify -v

test_already_slug ... ok
test_digits_preserved ... ok
test_internal_hyphen_preserved_after_collapse ... ok
test_multiple_mixed_separators ... FAIL
test_only_punctuation ... FAIL
test_only_symbols_with_spaces ... FAIL
test_only_whitespace ... FAIL
test_collapse_whitespace_and_punctuation_to_single_hyphen ... FAIL
test_empty_string ... ok
test_hello_world ... FAIL
test_non_alphanumeric_stripped ... ok
test_strip_leading_and_trailing_hyphens ... FAIL
test_accented_latin_nfkd_to_ascii ... FAIL
test_cjk_becomes_separator ... FAIL
test_unicode_mixed_with_ascii ... FAIL
======================================================================
FAIL: test_multiple_mixed_separators
AssertionError: 'Hello-World-Again' != 'hello-world-again'
FAIL: test_only_punctuation
AssertionError: '-' != ''
FAIL: test_only_symbols_with_spaces
AssertionError: '-' != ''
FAIL: test_only_whitespace
AssertionError: '-' != ''
FAIL: test_collapse_whitespace_and_punctuation_to_single_hyphen
AssertionError: 'a-b-c-' != 'a-b-c'
FAIL: test_hello_world
AssertionError: 'Hello-World-' != 'hello-world'
FAIL: test_strip_leading_and_trailing_hyphens
AssertionError: '-Hello-' != 'hello'
FAIL: test_accented_latin_nfkd_to_ascii
AssertionError: 'Caf-' != 'cafe'
FAIL: test_cjk_becomes_separator
AssertionError: '-' != ''
FAIL: test_unicode_mixed_with_ascii
AssertionError: 'Caf-au-Lait-' != 'cafe-au-lait'
----------------------------------------------------------------------
Ran 15 tests in 0.005s
FAILED (failures=10)
```

缺陷对照（原实现）：

```python
s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
return s
```

- 未 lower → `Hello-World-`
- 未 strip 首尾 `-` → `Hello-World-`、`-Hello-`
- 无 NFKD → `é` 被剥成 `Caf-`
- 纯分隔符输入留下孤悬 `-`

### 3. 修复 `slugify.py`

```python
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower())
    return s.strip("-")
```

未删改任何失败用例；只修实现。

### 4. GREEN — 修复后同套测试

```text
python -m unittest test_slugify -v

test_already_slug ... ok
test_digits_preserved ... ok
test_internal_hyphen_preserved_after_collapse ... ok
test_multiple_mixed_separators ... ok
test_only_punctuation ... ok
test_only_symbols_with_spaces ... ok
test_only_whitespace ... ok
test_collapse_whitespace_and_punctuation_to_single_hyphen ... ok
test_empty_string ... ok
test_hello_world ... ok
test_non_alphanumeric_stripped ... ok
test_strip_leading_and_trailing_hyphens ... ok
test_accented_latin_nfkd_to_ascii ... ok
test_cjk_becomes_separator ... ok
test_unicode_mixed_with_ascii ... ok
----------------------------------------------------------------------
Ran 15 tests in 0.003s
OK
```

## 验收清单

- [x] 测试文件可跑：`python -m unittest test_slugify -v`
- [x] response 含修复前失败：上文 RED，10 failures
- [x] 修复后通过：上文 GREEN，15/15 OK
- [x] 边界：空串、纯标点、首尾符号、多分隔符（另有纯空白、CJK、已是 slug、数字）

## 交付物

| 文件 | 说明 |
|------|------|
| `test_slugify.py` | 15 个用例，unittest |
| `slugify.py` | 已修复（NFKD + lower + collapse + strip） |
| `response.md` | 本文件 |

未改动 `task.md`、`load-proof.md`。范围仅 A-skill 目录。
