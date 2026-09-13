# SE001-slugify · B-noskill response

## Unicode 策略（notes）

采用 **NFKD 分解 + 仅保留 ASCII 字母数字**。

- `Café` → NFKD 将 `é` 分解为 `e` + 组合重音符 → 重音被剥离 → `"cafe"`
- 不保留非 ASCII 字母（如中文会变成空，整串若无 ASCII 则返回 `""`）

## RED（修复前）

命令：`python -m pytest test_slugify.py -v`

```
test_already_slug PASSED
test_collapse_whitespace_and_punct FAILED  # '-many-separators-' != 'many-separators'
test_digits_preserved FAILED               # 'Version-2-0-Release-' != 'version-2-0-release'
test_empty_input PASSED
test_hello_world FAILED                    # 'Hello-World-' != 'hello-world'
test_pure_punctuation FAILED               # '-' != ''
test_strip_leading_trailing_hyphen FAILED  # '-lead-and-trail-' != 'lead-and-trail'
test_unicode_lower_policy_nFKD FAILED      # 'Caf-' != 'cafe'

6 failed, 2 passed
```

### 初始实现缺陷

```python
s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
return s
```

1. 未 `lower()`
2. 未 strip 首尾 `-`
3. 未做 Unicode NFKD（`é` 被直接丢弃）
4. 空串/纯标点路径偶然正确或错误（纯标点得到 `"-"`）

## 修复

```python
def slugify(text: str) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFKD", text)
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")
```

## GREEN（修复后）

```
8 passed, 1 warning in 0.03s
```

全部用例通过：hello-world、空串、多分隔符折叠、首尾符号剥离、纯标点、NFKD Unicode、已是 slug、数字保留。

## 验收清单

- [x] 测试文件可跑
- [x] response 含修复前失败
- [x] 修复后通过
- [x] 边界：空串、纯标点、首尾符号、多分隔符
