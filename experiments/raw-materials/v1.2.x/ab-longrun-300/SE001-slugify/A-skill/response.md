# SE001-slugify · 阶段2 实现报告

工作目录：`<实验根目录>\ab-longrun-300\SE001-slugify\A-skill`
Skill：`gpt-series-reasoning-style` v1.1.0（`VERSION` 文件实读；阶段1 load-proof.md 曾写 1.2.0，与磁盘 VERSION 不一致——以磁盘为准）

---

## 【实现前确认】（轻通道）

- **我理解的目标**：对故意有缺陷的 `slugify.py` 先写失败测试（RED），再修复实现（GREEN），并用 `response.md` 固化两段实跑输出与 Unicode 策略。
- **风险分档**：轻 — 单目录内 3 个文件、完全可逆、无外部副作用；产物类型/位置/形态已由 `task.md` 与父指令完整指定。
- **形态选择**：单 Agent 主干 — 无并行信号，无跨模型转交需求。
- **已盘点可用资源**：本地 `task.md`（规格与验收）、`slugify.py`（缺陷种子）、`load-proof.md`（阶段1）；stdlib `unicodedata` + `re` 足够，无需第三方包或网络参考。
- **最高影响问题**：Unicode 策略二选一（NFKD→ASCII vs 仅 lower 保留非 ASCII）必须选定并测到位。
- **推荐方案**：NFKD + 剥离组合符 → ASCII slug（`Café`→`cafe`）；URL 安全、与主流 slugify 库一致。
- **其他选项**：仅 `lower()` 保留 `café`（非 ASCII URL，不推荐）。
- **完整计划**：写 `test_slugify.py` → 跑 RED 存证 → 修 `slugify.py` → 跑 GREEN 存证 → 消费者式 import 验证 → 写本文件。
- **澄清方式**：A（父指令已明确授权阶段2实现）
- **需要你确认**：无 — 父指令「阶段2·实现」+ `task.md` 完整规格视为授权。

---

## 1. 测试文件（先写，先红）

`test_slugify.py` — unittest，18 用例，覆盖：

| 类 | 覆盖点 |
| --- | --- |
| `TestSlugifySpec` | Hello World、空串、小写、空白/标点折叠、首尾剥离、纯标点、仅 alnum+hyphen、数字 |
| `TestSlugifyUnicode` | Café/naïve/全角数字 NFKD；希腊/西里尔边界（非拉丁字母折叠后为空） |
| `TestSlugifyBoundaries` | 单字符、长分隔符、前导数字、纯省略号 |

## 2. RED — 修复前实跑

```text
$ python -m unittest test_slugify -v
...
Ran 18 tests in 0.006s
FAILED (failures=13)
EXIT=1
```

失败摘要（13 FAIL / 5 ok）：

| 失败用例 | 实际 | 期望 |
| --- | --- | --- |
| `test_hello_world` | `'Hello-World-'` | `'hello-world'` |
| `test_lowercases_ascii` | `'ABC-Def'` | `'abc-def'` |
| `test_strips_leading_and_trailing_hyphens` | `'-Hello-'` | `'hello'` |
| `test_pure_punctuation_returns_empty` | `'-'` | `''` |
| `test_digits_preserved` | `'Python-3-14'` | `'python-3-14'` |
| `test_cafe_nfkd_ascii` | `'Caf-'` | `'cafe'` |
| `test_naive_with_diaeresis` | `'na-ve'` | `'naive'` |
| `test_mixed_unicode_word` | `'-ber-Cool-Caf-'` | `'uber-cool-cafe'` |
| `test_fullwidth_digits_folded` | `'-'` | `'123'` |
| `test_greek_alpha_is_not_ascii_folding_to_letter` | `'-'` | `''` |
| `test_cyrillic_dropped_like_greek` | `'-'` | `''` |
| `test_single_char` (`!`) | `'-'` | `''` |
| `test_none_like_empty_after_strip` (`...`) | `'-'` | `''` |

缺陷根因（原实现）：

```python
s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
return s
```

1. 不 lower
2. 不 strip 首尾 `-`
3. 不做 NFKD / 组合符剥离，非 ASCII 字母直接变分隔符残留 `-`

## 3. 修复后的 `slugify.py`

策略见下节。算法：空串短路 → NFKD → 丢弃 Mn 组合符 → `.lower()` → 非 `[a-z0-9]` 折叠为 `-` → `strip("-")`。

## 4. GREEN — 修复后实跑

```text
$ python -m unittest test_slugify -v
...
Ran 18 tests in 0.002s
OK
EXIT=0
```

消费者式 import 验证（库交付路径，非仅 unittest）：

```text
$ python -c "from slugify import slugify; ..."
consumer_cases= 10 failures= 0
sample: 'hello-world' 'cafe' ''
```

## 5. Unicode 策略说明（必须写明）

**选定策略：NFKD 分解 + 剥离组合标记（Unicode category Mn）+ 小写 + 仅保留 ASCII `[a-z0-9]`。**

- `Café` → NFKD `Café` → 去 `´` → `Cafe` → `cafe`
- `naïve` → `naive`
- `Über-Cool Café!` → `uber-cool-cafe`
- 全角数字 `１２３` → NFKD 映射为 `123` → `123`
- 非拉丁字母（希腊 `αβγ`、西里尔 `привет`）在 NFKD 后仍是字母但不是 `a-z`，**被剥离**，整词折叠后为空串（有意边界，已测）

**未选「仅 lower」策略**的理由：会产出 `café` 这类含非 ASCII 的 slug，URL/文件名兼容性差；主流 slugify 库（python-slugify、Django 等）默认走 ASCII 折叠。本策略与 `task.md` 中「Café → cafe 若做 NFKD」分支一致。

## 6. 验收清单对照

| 验收项 | 证据 |
| --- | --- |
| 测试文件可跑 | `python -m unittest test_slugify -v` → 18 tests |
| response 含修复前失败 | §2 RED 实跑，13 failures，exit 1 |
| 修复后通过 | §4 GREEN 实跑，OK，exit 0 |
| 边界：空串 | `test_empty_string` ok |
| 边界：纯标点 | `test_pure_punctuation_returns_empty` / `test_none_like_empty_after_strip` ok |
| 边界：首尾符号 | `test_strips_leading_and_trailing_hyphens` ok |
| 边界：多分隔符 | `test_collapses_whitespace_and_punctuation_to_single_hyphen` / `test_long_separator_run` ok |
| Unicode 策略写明并测到位 | §5 + `TestSlugifyUnicode` 全绿 |
| 不得删失败用例变绿 | 测试文件在修复前一次写完且未删改；仅改 `slugify.py` 实现 |

## 7. 完成门 / Honesty Gate

- **Verified**：RED→GREEN 完整循环（fresh 本轮命令输出）；库 import 消费路径 10 例 0 失败；验收清单逐项有证据指针；只改了实现未改测试期望。
- **Unverified**：无 GUI/交互面（纯库函数）；跨 Python 版本（仅 3.14.5 实跑）；极端 Unicode（emoji、CJK 整词丢弃行为仅覆盖希腊/西里尔样本）。
- **Assumptions**：ASCII-only slug 是正确交付形态；`task.md` 的「Café→cafe 若做 NFKD」即授权该策略。
- **Counter-evidence searched**：检查了「仅 lower」分支是否更符合规格——规格明确二选一写 notes，不构成反证。
- **Falsification checks run**：对当前缺陷实现故意先跑 18 用例确认 13 红；消费者脚本独立于 unittest 再验 10 例。
- **Evidence that would change the conclusion**：若任务要求保留非 ASCII 字母（`café`），需切换策略并改 Unicode 类用例——当前规格不要求。
- **Completion decision**：阶段2 验收清单全部满足；在当前授权范围内可关闭。

## 8. 实际改动文件

| 文件 | 动作 |
| --- | --- |
| `test_slugify.py` | 新建（18 用例） |
| `slugify.py` | 重写实现（保留文件名/导出符号 `slugify`） |
| `response.md` | 新建（本文件） |

未触碰：`task.md`、`load-proof.md`；未写 A-skill 目录以外任何路径。
