# SE009-slugify · 阶段2 实现报告（A-skill）

工作目录：`<实验根目录>\ab-longrun-300\SE009-slugify\A-skill`

## 1. Unicode 策略（选定并测到位）

**策略：NFKD 分解 + 剥离组合符 + ASCII 折叠**

| 步骤 | 说明 | 示例 |
|------|------|------|
| NFKD | 兼容分解，把带重音字母拆成基字母 + 组合符 | `Café` → `Caf` + U+0301 |
| 去组合符 | 丢弃 `unicodedata.combining(c) != 0` 的字符 | `Caf` |
| lower + ASCII | 小写后，仅保留 `[a-z0-9]`；无 ASCII 折叠的字符（如 CJK）视为分隔符 | `cafe` |
| 折叠 | 非字母数字连续串 → 单个 `-` | `Café Crème!` → `cafe-creme` |
| 去首尾 | `strip("-")` | `---hello---` → `hello` |

**取舍说明**

- 选 NFKD 而非「仅 lower」：slug 通常要进 URL / 文件名，`café` 里的非 ASCII 会带来编码与可读性问题；`cafe` 更稳。
- CJK 无 NFKD ASCII 映射，按策略**丢弃**（连续 CJK 折叠为分隔符）。`中文` → `""`；`日本語 test` → `test`。若业务要保留 CJK，需另加拼音/音译层——本规格未要求，不在本次范围。
- 已知边界（未测、有意接受）：`ø` / `ß` 等不走 NFKD 到 ASCII 的字符会被当作分隔符丢掉。

## 2. RED — 修复前失败输出

缺陷种子（原 `slugify.py`）：

```python
def slugify(text: str) -> str:
    # DEFECT: no lower, no strip, collapse broken
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

命令：

```text
python -m unittest test_slugify -v
```

输出摘要（7 FAIL / 5 ok）：

```text
test_already_slug ... ok
test_collapse_punctuation ... ok
test_collapse_whitespace ... ok
test_empty_string ... ok
test_hello_world ... FAIL
test_mixed_separators ... ok
test_numbers_kept ... FAIL
test_pure_punctuation ... FAIL
test_strip_leading_trailing ... FAIL
test_unicode_cjk_dropped_or_folded ... FAIL
test_unicode_mixed_with_ascii ... FAIL
test_unicode_nfkd_ascii_fold ... FAIL

======================================================================
FAIL: test_hello_world
AssertionError: 'Hello-World-' != 'hello-world'

FAIL: test_numbers_kept
AssertionError: 'Python-3-12' != 'python-3-12'

FAIL: test_pure_punctuation
AssertionError: '-' != ''

FAIL: test_strip_leading_trailing
AssertionError: '-hello-' != 'hello'

FAIL: test_unicode_cjk_dropped_or_folded
AssertionError: '-' != ''

FAIL: test_unicode_mixed_with_ascii
AssertionError: 'Caf-Cr-me-' != 'cafe-creme'

FAIL: test_unicode_nfkd_ascii_fold
AssertionError: 'Caf-' != 'cafe'

----------------------------------------------------------------------
Ran 12 tests in 0.003s

FAILED (failures=7)
```

缺陷对照：

| 缺陷 | 现象 |
|------|------|
| 无 lower | `Hello-World` / `Python-3-12` |
| 无 strip 首尾 `-` | `Hello-World-`、`-hello-`、纯标点 → `-` |
| 无 Unicode 折叠 | `Café` → `Caf-`，中文 → `-` |

## 3. 修复内容（`slugify.py`）

```python
def slugify(text: str) -> str:
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in decomposed if not unicodedata.combining(c))
    lowered = ascii_text.lower()
    slug = _NON_ALNUM.sub("-", lowered)   # [^a-z0-9]+ -> '-'
    return slug.strip("-")
```

仅改实现，**未删/未改任何失败用例**。

## 4. GREEN — 修复后通过输出

```text
python -m unittest test_slugify -v

test_already_slug ... ok
test_collapse_punctuation ... ok
test_collapse_whitespace ... ok
test_empty_string ... ok
test_hello_world ... ok
test_mixed_separators ... ok
test_numbers_kept ... ok
test_pure_punctuation ... ok
test_strip_leading_trailing ... ok
test_unicode_cjk_dropped_or_folded ... ok
test_unicode_mixed_with_ascii ... ok
test_unicode_nfkd_ascii_fold ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.001s

OK
```

## 5. 验收清单

- [x] 测试文件可跑（`python -m unittest test_slugify -v`）
- [x] response 含修复前失败（见 §2）
- [x] 修复后通过（见 §4，12/12）
- [x] 边界：空串、纯标点、首尾符号、多分隔符（`test_empty_string` / `test_pure_punctuation` / `test_strip_leading_trailing` / `test_mixed_separators` / `test_collapse_*`）
- [x] Unicode 策略写明并测到位（§1 + 3 个 unicode 用例）
- [x] 未删失败用例变绿；只修了 `slugify.py`

## 6. 交付文件

| 文件 | 动作 |
|------|------|
| `test_slugify.py` | 新建（RED 先写） |
| `slugify.py` | 修复 |
| `response.md` | 本文件 |
