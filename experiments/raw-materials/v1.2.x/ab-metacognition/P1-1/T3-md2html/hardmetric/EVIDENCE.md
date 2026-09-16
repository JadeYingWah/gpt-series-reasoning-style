# md2html.py 证据报告（T3 · hardmetric 臂）

- 执行者：general-purpose-117（单 Agent 主干形态）
- 日期：2026-09-13；环境：Windows 11 / Python 3.13.14（CPython），无 GUI
- 交付目录：`<实验根目录>\ab-metacognition\P1-1\T3-md2html\hardmetric\`
- skill：快照 `v1.2.3-draft`，按**轻量（验证聚焦版）**配置执行；引用硬性规则第一条——「宣布阶段序列不是确认。」

---

## 1. 交付物清单

| 文件 | 作用 | 性质 |
|---|---|---|
| `md2html.py` | 转换器主体，单文件零依赖（仅 `argparse`/`itertools`/`re`/`sys`） | 交付物 |
| `verify.py` | 验证套件：81 用例 × 3 条独立路径；`--impl` 可指向任意实现 | 第三方可独立复算 |
| `mutation_check.py` | 反例（变异）检查：10 个单行变异体，逐一验证会被套件抓红 | 第三方可独立复算 |
| `evidence/run-report.txt` | 81 个用例的输入/期望/实际逐条留档（由 `verify.py --report` 生成） | 证据 |
| `evidence/verify-run.log` | 本次全量验证控制台输出 | 证据 |
| `evidence/mutation-run.log` | 本次变异检查控制台输出 | 证据 |
| `evidence/demo.md`、`demo.out.html`、`demo.fragment.html` | 真实环境 CLI 验收样本 | 证据 |
| `EVIDENCE.md` | 本报告 | 证据 |

## 2. 完成标准对照（门禁中声明的可检查标准）

| 可检查标准 | 结果 | 证据 |
|---|---|---|
| `verify.py` 在干净环境退出码 0，全部用例通过 | **通过：81/81，EXIT=0** | `evidence/verify-run.log` |
| 10 个变异体中每一个都至少被 1 个用例抓红 | **通过：10/10 caught，0 survived** | `evidence/mutation-run.log` |
| `python md2html.py <file.md>` 对任务书全部 7 类边界输出合法 HTML | **通过**（7/7 点名用例 + 31/31 边界用例；结构经 `html.parser` 校验） | 第 3、5 节 |

## 3. 覆盖面枚举（验证开始前前置，逐段触达）

| 输入域分段 | 用例数 | 触达点（摘） |
|---|---:|---|
| 正常值 | 21 | h1–h6、ul/ol、围栏(带/不带语言)、行内代码、粗体、斜体、粗+斜嵌套、链接、列表项内行内、段落合并、混合文档 |
| 边界值 | 31 | 空文件、仅空行、标题↔正文无空行、无尾换行、CRLF、BOM、未闭合围栏、空围栏、4 反引号围栏、`#`×7、`#`后无空格、空标题、裸 `-`、`---`、词内 `_`/`*`、行内代码含 `*` `_` `&` `<`、链接文本含 `]`、地址含空格、`<>` 地址、空地址、1/3 层嵌套列表、列表惰性续行、列表间空行、列表降级、列表后接段落 |
| 异常值 | 9 | 未闭合反引号/粗体/斜体/链接/方括号、空强调标记、代码跨度压过链接、URL 含括号、控制字符 `\x01` |
| 安全注入 | 7 | `< > &` 转义、`<script>`（正文/代码）、`<img onerror>`、href 双引号注入（两种）、`javascript:` 透传 |
| 任务书点名场景 | 7 | 空/空行、标题相邻正文、未闭合围栏、行内代码不强调、链接 `]`+空格、嵌套列表、`< > &` 实体 |
| 回归（开发期已修缺陷） | 6 | 同段粗体+斜体（2 种标记）、多组粗斜混排、粗+斜+代码+链接同行、CJK 混排、链接与强调交错 |

**ALL GREEN 盲区自查声明**：81/81 全绿，但覆盖面不等于完备性。已识别的未覆盖/弱覆盖项：
1. **块级组合爆炸**（围栏出现在列表项内、引用块内嵌列表等）——未覆盖，属于任务书范围外块类型（引用块/表格/图片未实现）。
2. **非 UTF-8 编码输入**（GBK/UTF-16）——未覆盖，输入统一按 UTF-8 解码，`errors="replace"`；见 UNVERIFIED。
3. **超深嵌套/超长输入的性能与递归深度**——未覆盖（仅测到 3 层）。
4. **与 CommonMark 参考实现的差分一致性**——未做，见 UNVERIFIED。
5. 上述盲区中 1–3 已登记进第 8 节 UNVERIFIED 清单。

## 4. 验证方法（三条独立路径 + 反例）

- **PATH A（CLI 子进程）**：把每个用例写入临时文件（临时目录在系统 temp，不在交付目录内），执行 `python <impl> <file> --fragment`，与期望串**精确全等**比较。
- **PATH B（模块直调）**：`import md2html; convert(md, fragment=True)` 直连比较，并与 PATH A 交叉比对（防止只有 CLI 或只有库接口有问题）。
- **PATH C（结构校验）**：对**完整文档**输出用 `html.parser` 自建栈做标签配平校验，并校验 DOCTYPE / charset / `<title>` / 结尾 `</html>`。
- **反例（必做）**：`mutation_check.py` 把 `md2html.py` 源码做**单行替换**生成变异体（写入 temp，不污染交付目录），再对变异体跑 `verify.py`，要求退出码非 0 且至少 1 条用例变红；变异体若存活即判定套件存在盲区，脚本返回 1。

| 变异体 | 注入的一行错误 | 是否抓到 | 抓到时的表现（变红用例） |
|---|---|---|---|
| M1-no-amp-escape | 不再转义 `&` | 是 | inline-code-with-html, escape-angle-amp, spec-unclosed-fence, spec-escape-entities |
| M2-parse-inline-in-fence | 围栏代码内也做行内解析 | 是 | spec-unclosed-fence |
| M3-italic-before-bold | 强调顺序反了（先斜体） | 是 | bold, link-inside-bold, list-item-inline, spec-inline-code-emphasis, regress-*（+3） |
| M4-no-paragraph-merge | 每行一个 `<p>`，不合并 | 是 | paragraph-merge |
| M5-drop-unclosed-fence | 未闭合围栏被丢弃 | 是 | unclosed-fence, spec-unclosed-fence |
| M6-heading-up-to-7 | `#{1,7}`（7 个 # 也当标题） | 是 | heading-7-hash-is-text |
| M7-no-attr-escape | href 属性不转义 `"` | 是 | attr-quote-injection, attr-quote-injection-angle-url |
| M8-code-span-emphasis | 行内代码内也做强调解析 | 是 | inline-code-with-star-and-underscore, spec-inline-code-emphasis |
| M9-slot-id-collision | 所有占位符槽共用 id（**即开发期真实缺陷的复现**） | 是 | 6 条 regress-* 全部变红 |
| M10-no-gt-escape | 不再转义 `>` | 是 | mixed-document, inline-code-with-html, escape-angle-amp, script-tag-in-text, script-tag-in-fence, img-onerror-in-text（+2） |

## 5. 真实环境验收（亲手执行，非 UNVERIFIED）

本机实际执行的命令与结果（非交互 harness，CLI 即交互面）：

```
python md2html.py demo.md                 -> 完整 HTML（<title> 取自首个 h1），EXIT=0   见 evidence/demo.out.html
python md2html.py demo.md --fragment      -> 仅 body 片段                              见 evidence/demo.fragment.html
python md2html.py demo.md -o out.html     -> 写文件成功，EXIT=0
python md2html.py edge.md --fragment      -> 未闭合围栏: <pre><code>unterminated &lt;b&gt; &amp; **x** `y`
                                             still inside</code></pre>，EXIT=0        （内容原样，未做行内解析）
python md2html.py empty.md                -> 空文件输出合法空文档，EXIT=0
python md2html.py nope.md                 -> stderr 报错，EXIT=1（错误路径也已验证）
```

判定要点均已亲自核对：中文标题/正文、`<strong>粗体</strong>`、`<code>行内代码 *不强调*</code>`、嵌套 `<ul>`、`href="https://example.com/a%20b"`、代码块内 `&amp; 1 &lt; 2` 原样保留。

## 6. 开发期发现并修复的真实缺陷（P1）

- **现象**：`这是 **粗体**、*斜体* 与 …` 输出为 `这是 <em>斜体</em>、<em>斜体</em>`——粗体片段被斜体内容顶替。
- **发现方式**：**真实环境 CLI 冒烟**（非单元测试；此时 `verify.py` 74/74 全绿），说明「全绿」并不等于无缺陷——这正是反例/覆盖面纪律的必要性。
- **根因**：`_emphasis` 与内层 `_italic` 各自维护占位符槽位，但槽位编号都从 0 开始，嵌套渲染时外层 `<strong>…</strong>` 与内层 `<em>…</em>` 的占位符 token 相同，内层 restore 时把外层槽位一起替换掉。
- **修复**：引入 `_Slots` 类，占位符 token 携带**全局唯一的槽集 id**（`\x00<sid>:<idx>\x00`），嵌套渲染互不干扰。
- **防复发**：新增 6 条回归用例（第 3 节「回归」段）+ 变异体 M9 专门复现该缺陷，M9 必须变红。

## 7. 简化项 / 声明降级清单（不是免检通行证）

已实现且经测试；以下为**声明的降级**，全部写在 `md2html.py` 的模块 docstring（D1–D9）：

- **D1** 围栏代码内容原样输出（不做行内解析），仅转义 `& < >`（否则不是合法 HTML）。
- **D2** 未闭合围栏一直吃到文件末尾。
- **D3** 代码跨度优先于链接识别：`[`a`](u)` → `<code>a</code>` + 字面量 `](u)`。
- **D4** 链接地址支持一级成对括号；空格百分号编码为 `%20`；支持 `[t](<a b>)` 形式。
- **D5** `_` 在词内不产生强调（`snake_case` 保持字面量）；`*` / `**` 允许词内。
- **D6** 单独成行的 `-`（无内容）不是列表项，按段落处理。
- **D7** 列表项后的非空非项行为该项的惰性续行；空行结束列表。
- **D8** 嵌套列表按缩进支持（任意深度），不建模 loose/tight；**降级点**：缩进回退时开启新的兄弟列表而非合并回父列表。
- **D9** 正文仅转义 `& < >`，属性位置额外转义 `"`。
- **未实现（任务书未要求，主动声明）**：setext 标题、引用块、表格、分割线、图片、引用式链接、自动链接、原始 HTML 块。
- **已知限制（非缺陷，但请知悉）**：链接地址**不做协议白名单**，`[t](javascript:alert(1))` 会原样输出（有对应用例固化该行为）；若用于不可信输入，需在上层过滤协议。
- **理论边界**：占位符 token 使用 NUL，输入文本若**精确包含** `\x00<数字>:<数字>\x00` 形式的串可能被误替换；正常文本与 Markdown 不含 NUL，未做处理（记录备查）。

## 8. UNVERIFIED 清单

1. **宿主能力**（二次确认 / 审查门禁 / 验收流程）未证实 → 按保守假设视为不具备，保留 skill 纪律。`UNVERIFIED`
2. **任务类型判断的网络搜索依据**：任务书明令禁止联网，改用任务书显式规格清单作为判据。`UNVERIFIED`（网络侧）
3. **与 CommonMark 参考实现 / 其他 md 库的差分一致性**：未做，本臂仅按任务书规格自证。`UNVERIFIED`
4. **非 UTF-8 编码输入**（GBK/UTF-16 等）：未验证，统一按 UTF-8 + `errors="replace"` 解码。`UNVERIFIED`
5. **浏览器/IDE 中的实际渲染与样式**：无 GUI，未渲染验证；仅做 `html.parser` 结构配平校验。`UNVERIFIED`
6. **超深嵌套（>3 层）/ 大文件的递归与性能**：未覆盖。`UNVERIFIED`

## 9. 第三方独立复算说明

- **环境要求**：Python 3.9+（用到 `from __future__ import annotations` 与 `str | None` 注解——**仅在注解中，运行时安全；实测 3.13**），无第三方包、无网络、无环境变量依赖、不读写交付目录以外的位置（临时文件落在系统 temp 并自清理）。
- **命令**：
  ```
  cd <交付目录>
  python verify.py --report evidence/run-report.txt     # 预期：81/81 passed，EXIT=0（约 30s）
  python mutation_check.py                              # 预期：10/10 caught，EXIT=0（约 60s）
  python md2html.py evidence/demo.md                    # 预期：完整 HTML 文档，EXIT=0
  ```
- **预期一致性**：`evidence/verify-run.log` / `evidence/mutation-run.log` / `evidence/demo.out.html` 应与复算结果逐字一致（用例期望是硬编码常量，与实现无关）；`verify.py --report` 会重新生成 `run-report.txt`，其中每个用例的 `expected` 段应与本报告中留档的期望一致。
- **鉴别力而非体积**：证据以「能否抓到注入的错误」计（第 4 节 10 个变异体全红），不以满足断言数量计。

## 10. 任务参照系（Task Constitution）变更历史

- **初始**：一句话目标——「单文件零依赖 md→html，覆盖 8 项功能 + 7 类边界，附可复算验证与证据报告」；可检查完成标准＝「verify 退出码 0 全绿 + 变异体全被抓红 + CLI 对 7 类边界输出合法 HTML」；流程严格度＝代码类从严；任务类型＝代码类（禁网，依据为任务书规格清单）。
- **变更 1（覆盖率修订）**：修复 P1 缺陷后，在覆盖面枚举中**新增「回归（已修缺陷）」输入域分段并补 6 条用例**。原因：原枚举按「语法要素」分段，未包含「同行内块中粗体+斜体共存」的**组合维度**，属组合爆炸型盲区；不补则套件对该缺陷零鉴别力。
- **变更 2（边界项新增）**：第 6 节缺陷暴露后补做真实 CLI 冒烟，随后补 BOM 前缀用例（真实文件常见）并统一在 `convert()` 内剥离 BOM，使 CLI 与库调用两路径一致。
- 目标、质量标准、任务类型**未变更**。

## 11. 轻量配置「跳过项」对照（声明 vs 实际）

| 声明跳过的模块 | 实际执行情况 |
|---|---|
| 完整资源盘点 → 一句话摘要 | 已执行（门禁中）：可用资源仅 Python 标准库；**网络搜索与可装 skill 因任务书禁止联网而不可用**（非「当前够用」式弃用）；标准库 `html` 模块已评估并弃用——其 `escape` 默认转义 `"`，与本任务「只转义 `< > &`」规格不符，改为手写 `escape_text`。 |
| 任务参照系 → 一句话 | 已执行，且保留了变更历史（第 10 节）。 |
| 循环审查 2 轮 → 1 轮 | 已执行 1 轮；该轮产出：BOM 统一处理 + 1 条新用例。**注**：第 6 节的 P1 缺陷由真实环境冒烟发现，说明本任务确有「轻量 1 轮」之外的额外验证投入（未克扣）。 |
| 宿主对齐不等待确认 | 已执行（非交互 harness，输出声明后继续执行）。 |
| 实操闭环（无 GUI 标 UNVERIFIED） | CLI 类任务以真实命令行执行替代（第 5 节，已亲自执行并留存输出）；纯浏览器渲染部分标 `UNVERIFIED`（第 8 节第 5 项）。 |
| 三条底线（证据报告 / UNVERIFIED / 真实环境验收） | **未跳过**：本报告、第 8 节清单、第 5 节亲手执行命令。 |

## 12. 目录结构

```
hardmetric/
├── md2html.py              实现（单文件零依赖）
├── verify.py               验证套件（81 用例 × 3 路径，可 --impl 指向他处）
├── mutation_check.py       变异反例检查（10 个单行变异体）
├── EVIDENCE.md             本报告
└── evidence/
    ├── run-report.txt      81 用例输入/期望/实际留档
    ├── verify-run.log      全量验证输出
    ├── mutation-run.log    变异检查输出
    ├── demo.md             真实环境验收输入
    ├── demo.out.html       完整文档输出
    └── demo.fragment.html  body 片段输出
```
