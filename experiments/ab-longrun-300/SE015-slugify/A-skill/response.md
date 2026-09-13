# Response — SE015-slugify (A-skill)

## 形态与门禁

- 形态：单 Agent 主干（任务范围小、指令明确，无需子 Agent / 指挥官）。
- 风险分档：轻（单目录、纯本地、可逆、无外部副作用）。
- 用户指令「阶段2·实现 / 先 RED 再修到 GREEN / 只写 A-skill」视为轻通道授权；本文件即执行证据。

## 交付物

| 文件 | 作用 |
|------|------|
| `test_slugify.py` | 12 个 unittest 用例（含验收清单边界） |
| `slugify.py` | 修复后实现 |
| `response.md` | 本文件：RED → 修复 → GREEN 与 Unicode 策略 |

## Unicode 策略（选定并测到位）

**策略：NFKD + 剥离组合标记（Mn）+ Unicode lower**

流水线：

1. `unicodedata.normalize("NFKD", text)` — 把带重音的拉丁字母分解为基字 + 组合标记（`é` → `e` + U+0301）。
2. 丢弃所有 `unicodedata.combining(ch)` 非 0 的字符。
3. `str.lower()`（Unicode 感知）。
4. 按「连续非字母数字」切分，用单个 `-` 连接。字母数字判定用 `str.isalnum()`，因此 **无 NFKD 折叠的 Unicode 字母（CJK 等）会保留**。
5. 空输入或全分隔符输入 → `""`。

对照表（与 task 规格一致）：

| 输入 | 输出 | 策略分支 |
|------|------|----------|
| `"Hello, World!"` | `"hello-world"` | 基本折叠 + lower |
| `"Café"` | `"cafe"` | NFKD 折叠重音 |
| `"CAFÉ"` | `"cafe"` | NFKD + lower |
| `"naïve test"` | `"naive-test"` | NFKD + 分隔折叠 |
| `"你好世界"` | `"你好世界"` | isalnum 保留 CJK |
| `"你好 世界!"` | `"你好-世界"` | CJK + 分隔折叠 |
| `""` / `"   "` / `"!!!"` / `"---"` | `""` | 边界 |

> 未选「仅 lower、保留 `café`」策略：URL slug 场景更常用可移植的 ASCII 折叠；策略本身在测试中固化，不会悄悄漂移。

## RED — 修复前实跑

命令：

```text
python -m unittest test_slugify -v
```

结果：`Ran 12 tests … FAILED (failures=9)`

关键失败摘录（完整错误由 unittest 输出）：

```text
FAIL: test_basic_punctuation_and_case
AssertionError: 'Hello-World-' != 'hello-world'

FAIL: test_digits_and_alnum_mix
AssertionError: 'abc-123-XYZ' != 'abc-123-xyz'

FAIL: test_mixed_case_lowered
AssertionError: 'HeLLo' != 'hello'

FAIL: test_only_hyphens
AssertionError: '-' != ''

FAIL: test_pure_punctuation
AssertionError: '-' != ''

FAIL: test_strip_leading_trailing_hyphens
AssertionError: '-hello-' != 'hello'

FAIL: test_unicode_letters_kept_as_alnum
AssertionError: '-' != '你好世界'

FAIL: test_unicode_nfkd_strategy
AssertionError: 'Caf-' != 'cafe'

FAIL: test_whitespace_only
AssertionError: '-' != ''

Ran 12 tests in 0.006s
FAILED (failures=9)
```

初始缺陷（`slugify.py` 原注释）：无 lower、无 strip、collapse 对连续分隔符之外的场景不正确、不处理 Unicode。

通过的 3 个用例仅覆盖「已部分正确」的折叠路径（如 `"foo bar---baz!!qux"`、空串、`"hello-world"`），不构成规格符合。

## 修复 — `slugify.py`

实现采用上述 NFKD 流水线；未删改任何测试用例，只重写实现。

## GREEN — 修复后实跑

命令：

```text
python -m unittest test_slugify -v
```

结果：

```text
test_already_slug (test_slugify.TestSlugifySpec.test_already_slug) ... ok
test_basic_punctuation_and_case (test_slugify.TestSlugifySpec.test_basic_punctuation_and_case) ... ok
test_collapse_mixed_separators (test_slugify.TestSlugifySpec.test_collapse_mixed_separators) ... ok
test_digits_and_alnum_mix (test_slugify.TestSlugifySpec.test_digits_and_alnum_mix) ... ok
test_empty_input (test_slugify.TestSlugifySpec.test_empty_input) ... ok
test_mixed_case_lowered (test_slugify.TestSlugifySpec.test_mixed_case_lowered) ... ok
test_only_hyphens (test_slugify.TestSlugifySpec.test_only_hyphens) ... ok
test_pure_punctuation (test_slugify.TestSlugifySpec.test_pure_punctuation) ... ok
test_strip_leading_trailing_hyphens (test_slugify.TestSlugifySpec.test_strip_leading_trailing_hyphens) ... ok
test_unicode_letters_kept_as_alnum (test_slugify.TestSlugifySpec.test_unicode_letters_kept_as_alnum)
Unicode letters that have no NFKD fold (e.g. CJK) are kept. ... ok
test_unicode_nfkd_strategy (test_slugify.TestSlugifySpec.test_unicode_nfkd_strategy)
Strategy: NFKD + strip combining marks (Mn) → Café becomes cafe. ... ok
test_whitespace_only (test_slugify.TestSlugifySpec.test_whitespace_only) ... ok
----------------------------------------------------------------------
Ran 12 tests in 0.001s
OK
```

## 验收清单对照

- [x] 测试文件可跑：`python -m unittest test_slugify -v`
- [x] response 含修复前失败：见 RED 段
- [x] 修复后通过：`Ran 12 tests … OK`
- [x] 边界覆盖：空串、纯标点、首尾符号、多分隔符、仅 `-`、Unicode（NFKD 折叠 + CJK 保留）
- [x] 未删失败用例变绿；未只改测试

## 范围克制

仅改动/新增 `A-skill` 下的 `test_slugify.py`、`slugify.py`、`response.md`。未触碰 `task.md`、`load-proof.md` 或目录外文件。
