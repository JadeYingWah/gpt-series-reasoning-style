# Response · SE013-slugify

## Unicode 策略（选定）

**NFKD 分解后仅保留 ASCII 字母数字**。

- `unicodedata.normalize("NFKD", text)` 把兼容字符拆成基字符 + 组合符（`é` → `e` + combining acute；`ﬁ` → `fi`）
- `.encode("ascii", "ignore")` 丢弃仍非 ASCII 的码点（组合符、西里尔等）
- 再 lower、把非 `[a-z0-9]` 连续段折叠为单个 `-`、去首尾 `-`

效果：`Café` → `cafe`，`naïve` → `naive`，`ﬁle` → `file`，`Привет` → `""`（整串被剥离）。

未选「仅 lower」策略（`café`）：URL/slug 场景更常用可移植 ASCII，且与任务示例 `cafe` 一致。

## RED（修复前）

缺陷实现（原 `slugify.py`）：

```python
s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
return s
```

缺陷：无 lower、无首尾 strip、无 Unicode 处理。

`python -m unittest test_slugify -v`

```
Ran 24 tests in 0.007s
FAILED (failures=16)
```

典型失败：

```
AssertionError: 'Hello-World-' != 'hello-world'
AssertionError: 'Hello' != 'hello'
AssertionError: '-Hello-' != 'hello'
AssertionError: '-' != ''
AssertionError: 'Caf-' != 'cafe'
AssertionError: 'na-ve' != 'naive'
```

## 修复

`slugify.py` 改为：NFKD → ascii-ignore → lower → `re.sub(r"[^a-z0-9]+", "-")` → `strip("-")`。

未删减任何失败用例；仅改实现。

## GREEN（修复后）

```
Ran 24 tests in 0.001s
OK
```

全部 24 项通过，含边界：

| 类别 | 覆盖 |
|------|------|
| 空串 / 纯空白 | `""`, `"   "`, `"\t\n"` → `""` |
| 纯标点 | `"!!!"` → `""`，`" - - - "` → `""` |
| 首尾符号 | `"!!!Hello"`, `"Hello!!!"`, `"--Hello--"` |
| 多分隔符 | `"foo---bar...baz"` → `"foo-bar-baz"` |
| Unicode | `Café`, `naïve`, `ﬁle`, `Café au Lait`, 西里尔剥离 |
| 规格主路径 | `"Hello, World!"` → `"hello-world"` |

## 验收清单

- [x] 测试文件可跑（`python -m unittest test_slugify -v`）
- [x] response 含修复前失败（16 failures）
- [x] 修复后通过（24 OK）
- [x] 边界：空串、纯标点、首尾符号、多分隔符
