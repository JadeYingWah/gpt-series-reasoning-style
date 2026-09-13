# Response · SE005-slugify 阶段2

工作目录：`<实验根目录>\ab-longrun-300\SE005-slugify\A-skill`

## Unicode 策略（NFKD fold）

选 **NFKD + 去结合符 + 仅保留 `[a-z0-9]`**，其余字符视为分隔符，折叠为单个 `-`，再剥首尾 `-`。

| 输入 | 输出 | 说明 |
|------|------|------|
| `Café` | `cafe` | 组合锐音符被剥掉 |
| `naïve` | `naive` | 同上 |
| `Straße` | `stra-e` | NFKD 不把 ß 折成 ss；ß 作分隔符 |
| `你好世界 hello` | `hello` | CJK 无 ASCII fold，被剥离 |

若选「仅 lower」则 `Café → café`；本实现明确不采用该策略。

## 流程：先 RED 再修

1. 写好 `test_slugify.py`（19 个用例，覆盖规格与边界）
2. 对**故意有缺陷**的 `slugify.py` 实跑 → RED
3. 修 `slugify.py`
4. 再跑 → GREEN

### 修复前实现（缺陷种子）

```python
def slugify(text: str) -> str:
    # DEFECT: no lower, no strip, collapse broken
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return s
```

缺陷点：不 lower、不剥首尾 `-`、无 NFKD、空/纯标点会剩 `-`。

---

## RED 输出（修复前实跑）

命令：`python -m unittest test_slugify -v`

```
test_alnum_join ... ok
test_collapse_many_separators ... ok
test_collapse_mixed_punct_and_space ... FAIL
test_collapse_spaces ... ok
test_digits_kept ... FAIL
test_empty_string ... ok
test_hello_world ... FAIL
test_only_punctuation ... FAIL
test_only_symbols ... FAIL
test_only_whitespace ... FAIL
test_simple_words ... ok
test_strip_both ... FAIL
test_strip_leading_symbols ... FAIL
test_strip_trailing_symbols ... FAIL
test_unicode_cjk_stripped ... FAIL
test_unicode_mixed ... FAIL
test_unicode_nfd_fold_cafe ... FAIL
test_unicode_nfd_fold_german_ess ... FAIL
test_unicode_nfd_fold_naive ... FAIL
----------------------------------------------------------------------
Ran 19 tests in 0.004s
FAILED (failures=14)
```

代表性断言失败：

```
AssertionError: 'Hello-World-' != 'hello-world'
AssertionError: 'a-b-c-' != 'a-b-c'
AssertionError: '-' != ''                  # 纯标点 / 纯空白
AssertionError: 'Caf-' != 'cafe'           # 组合符被当分隔符，且未 lower
AssertionError: '-Hello' != 'hello'        # 未剥首尾
```

说明：5 个用例在坏实现上碰巧通过（如 `foo--bar` 的折叠、空串），其余 14 个按规格失败。未删除/放宽任何失败用例。

---

## 修复

`slugify.py` 改为 NFKD fold 流水线：normalize → 去 Mn → lower → 非 `[a-z0-9]` 折 `-` → 剥首尾 `-`。

---

## GREEN 输出（修复后实跑）

命令：`python -m unittest test_slugify -v`

```
test_alnum_join ... ok
test_collapse_many_separators ... ok
test_collapse_mixed_punct_and_space ... ok
test_collapse_spaces ... ok
test_digits_kept ... ok
test_empty_string ... ok
test_hello_world ... ok
test_only_punctuation ... ok
test_only_symbols ... ok
test_only_whitespace ... ok
test_simple_words ... ok
test_strip_both ... ok
test_strip_leading_symbols ... ok
test_strip_trailing_symbols ... ok
test_unicode_cjk_stripped ... ok
test_unicode_mixed ... ok
test_unicode_nfd_fold_cafe ... ok
test_unicode_nfd_fold_german_ess ... ok
test_unicode_nfd_fold_naive ... ok
----------------------------------------------------------------------
Ran 19 tests in 0.000s
OK
```

## 验收清单

- [x] 测试文件可跑（`test_slugify.py`，unittest，19 例）
- [x] response 含修复前失败（上表 14 FAIL）
- [x] 修复后通过（OK）
- [x] 边界：空串、纯标点、首尾符号、多分隔符、Unicode fold

## 禁止项自检

- 未删失败用例变绿
- 未只改测试：实现从缺陷种子重写为 NFKD fold 流水线
