# Response — SE004-slugify

## Unicode strategy（选定并测到位）

**策略：NFKD + 去掉 combining marks（Mn）+ lower，再折叠分隔符。**

- `Café` → NFKD 得 `Cafe` + 组合音符 → 去掉 marks → `Cafe` → lower → `cafe`
- 只保留 ASCII `[a-z0-9]`；其余（含 CJK、emoji、标点、空白）折叠为单个 `-`，首尾 `-` 去掉。
- 因此 CJK 如 `中文` 被剥成 `""`（与「非字母数字剥离」一致；若未来要保留 Unicode 字母，可改用 `str.isalnum()` 分支，但本阶段明确选择 ASCII-only slug，测到位）。

实现：`slugify.py` 使用 `unicodedata.normalize("NFKD", …)` + `not unicodedata.combining(c)` + `re.sub(r"[^a-z0-9]+", "-", …).strip("-")`。

## RED — 修复前

初始实现：

```python
def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

缺陷：不 lower、不去首尾 `-`、不折叠连续分隔符（`re.sub` 其实会折叠，但整串仅标点会留下单个 `-`）、不处理 Unicode 音符。

### 命令与失败输出

```
$ python -m unittest test_slugify -v
```

```
test_already_slugish ... ok
test_collapse_runs_of_whitespace_and_punctuation ... ok
test_empty_string ... ok
test_hello_world ... FAIL
test_mixed_content ... FAIL
test_non_alnum_stripped ... FAIL
test_only_punctuation ... FAIL
test_strip_leading_and_trailing_separators ... FAIL
test_unicode_cjk_passthrough_as_non_alnum ... FAIL
test_unicode_nfkd_strategy ... FAIL
======================================================================
FAIL: test_hello_world
AssertionError: 'Hello-World-' != 'hello-world'
FAIL: test_mixed_content
AssertionError: '-My-Caf-Menu-2024-' != 'my-cafe-menu-2024'
FAIL: test_non_alnum_stripped
AssertionError: 'C-Python' != 'c-python'
FAIL: test_only_punctuation
AssertionError: '-' != ''
FAIL: test_strip_leading_and_trailing_separators
AssertionError: '-Hello-' != 'hello'
FAIL: test_unicode_cjk_passthrough_as_non_alnum
AssertionError: '-' != ''
FAIL: test_unicode_nfkd_strategy
AssertionError: 'Caf-' != 'cafe'
----------------------------------------------------------------------
Ran 10 tests in 0.003s
FAILED (failures=7)
```

测试文件：`test_slugify.py`（10 用例，覆盖空串、纯标点、首尾符号、多分隔符、Unicode、混合内容）。

## 修复 — `slugify.py`

见当前 `slugify.py`：NFKD → 去 combining marks → lower → `[^a-z0-9]+` 折叠为 `-` → `strip("-")`。

## GREEN — 修复后

```
$ python -m unittest test_slugify -v
```

```
test_already_slugish ... ok
test_collapse_runs_of_whitespace_and_punctuation ... ok
test_empty_string ... ok
test_hello_world ... ok
test_mixed_content ... ok
test_non_alnum_stripped ... ok
test_only_punctuation ... ok
test_strip_leading_and_trailing_separators ... ok
test_unicode_cjk_passthrough_as_non_alnum ... ok
test_unicode_nfkd_strategy ... ok
----------------------------------------------------------------------
Ran 10 tests in 0.002s
OK
```

## 验收清单

- [x] 测试文件可跑
- [x] response 含修复前失败（上文 RED）
- [x] 修复后通过（上文 GREEN）
- [x] 边界：空串、纯标点、首尾符号、多分隔符
- [x] 未删失败用例；未只改测试——修的是 `slugify.py`

## 范围

只改/新增本目录：`test_slugify.py`、`slugify.py`、`response.md`。
