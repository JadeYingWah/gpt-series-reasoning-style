# 任务 SE016-slugify · slugify 库与测试

工作目录：本文件所在文件夹。

## 初始代码 `slugify.py` 已存在（故意有缺陷）

## 交付

1. `test_slugify.py`：unittest/pytest，**先对当前实现跑出失败**
2. `response.md` 记录 RED 输出 → 修复 `slugify.py` → GREEN 输出
3. 规格：
   - `slugify("Hello, World!")` → `"hello-world"`
   - 连续空白/标点折叠为单个 `-`
   - 去掉首尾 `-`
   - 非字母数字（除 `-`）剥离；空串输入返回 `""`
   - Unicode 字母保留小写形式（如 `Café` → `cafe` 若做 NFKD，或 `café` 若仅 lower——**必须在 notes 写明你选的策略并测到位**）

## 验收清单

- [ ] 测试文件可跑
- [ ] response 含修复前失败
- [ ] 修复后通过
- [ ] 边界：空串、纯标点、首尾符号、多分隔符

## 禁止

- 不得删失败用例变绿；不得只改测试
