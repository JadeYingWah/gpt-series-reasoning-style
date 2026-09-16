# gpt-series-reasoning-style · 完整说明书

> **交付验收与多智能体协作纪律层。**
> A delivery-discipline layer for agent skills — Chinese-primary.

| 项 | 值 |
|---|---|
| 当前版本 | **1.5.0**（以 `VERSION` 文件为准） |
| 许可 | MIT |
| 主导语言 | 中文（关键术语保留英文） |
| 运行时形态 | **纯文本**（不改代码、不联网、不上报） |
| 加载成本 | `SKILL.md` 1834 字节 / 29 行（约 0.5k token）；规则文件**按阶段**才读 |
| 仓库文件数 | 17（main 分支工作树；实验数据在 experiments 分支） |

## 来源与适用范围 / Origin and Scope

**中文**

本 skill 不是凭空设计的规则集，而是从一系列 **GPT 系列大模型**（包括 **GPT-5.6 Sol** 与 **GPT-6 Astra**）在真实交付任务中的长期使用过程里**观察、提炼**出来的。

我们把这些模型在规划与验收环节反复表现出的有益特点——**先想清楚再动手、交付时给出可复现的验证、没验过的地方主动标注**——保留并固化成一份纪律文本。

因此，它**不是**某个模型的专用配件：提炼的是**行为特征**，不是模型能力。任何具备指令遵循能力的大模型都可以加载它。名字里的 "GPT-Series" 记录的是它的**来源**，不是它的**适用范围**。

**English**

This skill is not an invented rule set. It was **observed and distilled** from long-term, hands-on use of a series of **GPT-series models** — including **GPT-5.6 Sol** and **GPT-6 Astra** — on real delivery tasks.

We kept and froze the habits these models showed at their best during planning and acceptance: **think it through before acting, ship reproducible verification, and flag what you could not verify**.

It is therefore **not** a model-specific add-on. What is distilled is **behavioral patterns**, not model capabilities — any instruction-following LLM can load it. "GPT-Series" in the name records its **origin**, not its **scope**.

## 为什么不是"把 GPT 的行为规则全搬过来" / Why Not Copy Every Rule

**中文**

大量 A/B 对照实验反复证明了一件事：**把 GPT 自身的行为特点写成规则、塞进使用者的执行过程，结果适得其反**。你无法靠堆砌规则，让使用者复现 GPT 那样的产出质量。

实测中规则越多并不等于越好：把纪律硬指标化后，评分**并未提升**（与原则引导的差异落在判分误差内，判定为等效）；更极端的 v1.2.5 重版本（179 行、77 条自检）则被实验直接证伪并废弃。执行者记不住繁复步骤、模板填不满，最后流于形式应付（详见 §10）。

> **版本注**：上述"规则越多越差"的对比来自 **v1.2.x 旧版本**（v1.2.2 / v1.2.3-draft / v1.2.5）。v1.4.x 极简版起已删除硬指标化与繁复条款，现行 **1.5.0 不再适用该对比**。

所以我们只做两件事：

1. **抽取少数真正可遵守的特性**（真打开看一眼、未验证标注、全绿不算证据等）；
2. 配上**独特的遗忘机制**——执行阶段让纪律退场，交付时再重载。

这让使用者**只享受正面增益**：

- 交付可信度提升（带 skill 的臂在质量/纪律评分上明显更高）；
- "真打开看一眼"能抓到代码审查抓不到的视觉与运行缺陷；
- 反例验证执行率从约三分之一提升到接近全部覆盖；
- 未验项被逐条标注，一眼知道哪些结论能直接信、哪些还要自己再验。

同时**避免负面影响**：

- 不必让纪律全程在场——不挤占注意力、不打断创作思路、不烧上下文；
- 不会因规则堆砌而效果倒退；
- 不会滑向"填模板、走过场"的形式化应付。

**English**

Extensive A/B testing keeps showing one thing: **turning GPT's own behavioral traits into rules and injecting them into the user's execution process backfires.** You cannot make a user reproduce GPT-grade output quality by piling on rules.

In our tests, more rules did not mean better results: turning the discipline into hard metrics brought **no gain** (the gap versus principle-based guidance fell within scoring error and was judged equivalent), and the far heavier v1.2.5 build — 179 lines with 77 self-checks — was directly falsified and retired. Executors could not remember elaborate steps, templates were never fully filled, and compliance became theatre (see §10).

> **Version note**: the "more rules, worse results" comparison comes from **older v1.2.x builds** (v1.2.2 / v1.2.3-draft / v1.2.5). Hard metrics and bulky clauses were removed in the v1.4.x minimal line, so the comparison **no longer applies to the current 1.5.0**.

So we do only two things:

1. **Extract a few traits that can actually be followed** (really open it, mark what is unverified, all-green is not evidence, etc.);
2. Pair them with a **distinctive forgetting mechanism** — the discipline steps aside during execution and is reloaded at delivery time.

Users therefore **get the upside only**:

- more trustworthy deliveries (skill-armed runs score markedly higher on quality/discipline);
- "really open it" catches visual and runtime defects that code review misses;
- counter-example verification rises from roughly one-third to near-full coverage;
- unverified items are listed one by one, so you can tell at a glance what to trust and what to re-check.

while **avoiding the downside**:

- no ever-present discipline taxing attention, interrupting thought, or burning context;
- no regression from rule pile-up;
- no slide into checkbox-theatre.

<img src="social-preview.svg" alt="GPT-Series Reasoning Style — 交付验收纪律层" width="640">

> 图：`social-preview.svg`（1280×640）——三阶段卡片（规划 / 执行 / 审查）以**盾牌图标的两种状态**表达纪律开关：虚线盾+斜杠 = 规则退场（RULES OFF），实线盾+勾 = 规则重载（RULES ON）。图例见画面底部。

---

## 首创性设计 / A First of Its Kind

**中文**

据我们所知，这是首个在**单一 Skill 内**、通过**文件级渐进加载**实现「**纪律—心流五阶段时序隔离**」的设计。

五个阶段依次展开：

| # | 阶段 | 规则状态 | 做什么 |
|---|---|---|---|
| 1 | **无规则约束构想**（阶段1 · 自由构想） | 规则缺席 | 纯凭判断力想清楚要做什么 |
| 2 | **渐进式加载规则进行规划**（阶段2 · 规则规划） | 规则载入 | 把构想落成计划，**完整保留**第一阶段的构想，不被规则覆盖 |
| 3 | **执行**（阶段3 · 执行） | 规则退场 | 专心干活，规则完全不存在 |
| 4 | **无规则检查**（阶段4 · 直觉检查） | 规则缺席 | 凭直觉挑刺，抓规则**没覆盖到**的问题 |
| 5 | **渐进式加载规则进行纪律检查**（阶段5 · 纪律检查） | 规则重载 | 严格逐条过纪律，规则覆盖到的必须都做到 |

结果是两个「**零**」：

- **执行期零干扰**——规则在执行阶段完全不存在，心流不被打断；
- **验收期零妥协**——规则在交付那一刻完整重载，该守的一条不少。

由此带来：**交付可信度显著提升**（带 skill 的臂在质量/纪律评分上明显更高）。

**English**

To our knowledge, this is the first design to achieve **discipline/flow isolation across a five-stage timeline** — inside a **single skill**, via **file-level progressive loading**.

| # | Stage | Rule state | What happens |
|---|---|---|---|
| 1 | **Unconstrained ideation** (plan-1) | absent | think it through on judgment alone |
| 2 | **Progressive rule loading for planning** (plan-2) | loading | turn the vision into a plan, **fully preserving** the stage-1 vision rather than overwriting it |
| 3 | **Execution** | withdrawn | focused work; rules simply do not exist |
| 4 | **Unruled check** (review-1) | absent | intuition-driven, catching what the rules **do not** cover |
| 5 | **Progressive rule loading for discipline check** (review-2) | reloaded | enforce every rule, one by one |

The result is two **zeros**:

- **Zero interruption while executing** — the rules are absent during execution, so flow is never broken;
- **Zero compromise at acceptance** — the rules reload in full at delivery, and nothing on the list is skipped.

And with that: **delivery trustworthiness rises markedly** (skill-armed runs score clearly higher on quality/discipline).

---

## 1. 这是什么

一句话：**把"Agent 说做完了"变成"Agent 证明做完了"。**

它不教模型思考，也不增强推理能力。它只在**交付环节**施加纪律：让"没验过就说做完了"这件事变得更难发生。

### 它治的病

AI agent 最贵的失败不是"不会做"，而是**没验过就说做完了**：

- 测试没真跑，宣布"全部通过"；
- HTML 没在浏览器里打开过，宣布"页面没问题"；
- 关键数字没重算，照抄第一遍的结果。

在**四轮独立复现、14 个实验臂**的对照实验里，AI **无一例外**自报"测试全过、验证有效"——而独立复查（机械判定台）仍然判出大量真实缺陷。

---

## 2. 功能定位

### 2.1 定位

| 维度 | 说明 |
|---|---|
| 层次 | **流程纪律层**——不是知识库，不是内容主导者 |
| 作用面 | 任务的**规划**与**交付验收**两端 |
| 核心增量 | **验证纪律**（逼出遗漏、发现不一致、证据可复现），而非"让 AI 从不会到会" |
| 差异点 | 在**同一段上下文内**：执行阶段显式脱离纪律、进入心流，仅在自判完成时重新加载审查规则（"忘/想"交替） |

### 2.2 它**不是**什么

- **不是推理能力增强器**；
- **不是 GPT 专用**——提炼自 GPT 系列模型（含 **GPT-5.6 Sol**、**GPT-6 Astra**）的使用过程，但适用于所有具备指令遵循能力的大模型（详见开头「来源与适用范围」）；
- **不声称降低致命缺陷率或"兜底"**（实验口径不支持，详见 §10）；
- **不提升代码质量**——实测一致显示：代码本体差别不大，变好的是**交付可信度**；
- **不是加速器**——它通常让你多花时间验证，换的是"敢直接用"的交付。

### 2.3 为什么是"临时脱离 → 完成后重载"这个循环

**中文**

多数 skill 一旦加载便全程在场：规则持续占用注意力、打断创作思路、消耗上下文预算。

本 skill 反过来——它把自己拆成**两端**：**规划**与**验收**。中间漫长的**执行**阶段，显式让纪律退场，让模型专心干活、不打断思路；只在它自判"我做完了"的那一刻，重新加载审查规则。

**这对使用者的意义**：**你只收下它的益处，不必承受纪律常驻的代价。** 纪律不在最需要连贯思路的时候出现，只在最需要它把关的时候回来——所以你可以**无视 skill 常见的那些负面影响**，直接享受更可信的交付。

**English**

Most skills stay present once loaded — the rules keep taxing attention, interrupting the flow of thought, and consuming context budget.

This skill does the opposite: it splits itself into **two ends** — **planning** and **acceptance**. During the long **execution** phase in between, the discipline explicitly steps aside so the model can work without interruption; it is reloaded only at the moment the model declares "I'm done."

**What this means for you as a user:** **you get the benefits without paying the costs of an ever-present discipline.** It never shows up when a coherent train of thought matters most, and returns only when its gatekeeping is actually needed — so you can **ignore the usual downsides of a skill** and simply enjoy more trustworthy deliveries.

---

## 3. 触发条件

### 3.1 自动触发（由 `SKILL.md` 的 `description` 决定）

命中以下**任一**即加载：

| 信号类型 | 具体信号 |
|---|---|
| 任务特征 | 涉及**数字验算、代码交付、多 Agent 协作、需要防假完成**的任务 |
| 用户话语 | "做完了帮我查 / 看看对不对 / 验收"；派发子任务或多个 AI 分工；需要确认交付物真能用而不是"我觉得行" |
| 关键词 | 假完成、未验证、UNVERIFIED、任务包、指挥官、多 Agent |

### 3.2 显式触发

```
使用 gpt-series-reasoning-style 执行本次任务。
```

### 3.3 不触发

- 一句话问答、纯聊天；
- 小且可逆的改动。

> **设计意图**：纪律不该出现在不需要它的地方。

---

## 4. 可执行的操作

### 4.1 核心机制：五阶段时序（文件级渐进加载）

加载后**无需任何特殊指令**，agent 按**五阶段**推进；每阶段有明确退出条件，规则文件**按阶段**读取：

| 阶段 | 名称 | 规则状态 | 做什么 | 退出条件 |
|---|---|---|---|---|
| 1 | 自由构想 | 规则缺席 | 凭自己的判断力想清楚要做什么 | 能一句话说清接下来做什么 |
| 2 | 规则规划 | **读 `plan-rules.md`** | 把构想落成计划，**完整保留**阶段1构想 | 方案已确认、风险已分级、无需再问 |
| 3 | 执行 | 规则退场 | 凭自己的能力去做，不打断思路 | 觉得可以了，没有正在调的问题 |
| 4 | 直觉检查 | 规则缺席 | 凭常识快速扫一遍交付物 | 没有"等等，这里好像有问题"的卡住感 |
| 5 | 纪律检查 | **读 `review-rules.md`** | 严格逐条过纪律 | 见 `review-rules.md` 退出条件 |

状态序列：**无规则 → 有规则 → 无规则 → 无规则 → 有规则**

**设计意图**两条：

1. **创作时没有纪律**——阶段1与整个执行阶段规则缺席，不污染思路、不打断心流；
2. **检查有两道**——直觉抓规则**没覆盖到**的问题，纪律确保规则**覆盖到**的都做到，互不替代。

**任务结束后**：彻底忘记三个规则文件（plan-rules / review-rules / multi-agent）的具体内容，只记住"有五个阶段，到哪个阶段读哪个文件"——下次需要时再读。

### 4.2 阶段2 的规划规则（读 `plan-rules.md`）

| 动作 | 内容 |
|---|---|
| **保留阶段1构想** | 阶段1想到的一切——方案思路、技术选型、可能的坑——**全部带入阶段2，不清空重来** |
| **形态判断** | 心里做，**不输出思考过程**，不向用户汇报"我选择了什么形态"——直接干活 |
| **协作形态叠加** | 形态一/二/三可分部分叠加（见 §4.4）；**形态三命中后先与用户确认** |
| **轻量档** | 只做方案、不实际派发时，不建 `_agents/` 目录、不写任务包文件 |
| **小任务直通** | 小且可逆的任务 = 指令即授权，直接做、不请示、不调研、不确认档位。只有**不可逆、对外发布、删东西**才事前确认 |
| **风险分级** | 轻任务只做审查 3 条（真打开看一眼 / 未验证标注 / 防死循环）；数据/代码/多 Agent 类重任务做全 **8** 条 |
| **动手前调研** | 重任务先花几分钟上网查做法、坑、最佳实践，不凭感觉瞎写 |
| **确认档位** | **A 档（默认）**：一次性列推荐方案，同意即开干。**B 档**：用户主动要求时才用——一次只问一个最高影响问题，每题给 2–3 个实质方案 + 推荐 + 自由出口。**不需要专门问"你要 A 还是 B"** |
| **退出条件** | 方案已跟用户确认 + 风险等级已判断 + 没有需要再问用户的问题 |

### 4.3 阶段5 的纪律检查：八条纪律（读 `review-rules.md`）

| # | 纪律 | 具体要求 | 轻任务 |
|---|---|---|---|
| 1★ | **真打开看一眼** | 产物在真实环境打开、真用一遍。HTML 要在浏览器渲染、API 要用前端调、文档要在阅读器打开——**跑脚本不算真打开**。环境不支持时：如实标"未验证：浏览器渲染"+ 给用户自验步骤 | 必做 |
| 2★ | **未验证标注** | 未验过的结论标「未验证」，写明哪步没法验。交付只说三件：做了什么 / 怎么验的（给可复现命令）/ 哪些没验。未验项逐条写 ①XX——原因是XX；**不许只写"部分未验证"** | 必做 |
| 3 | **交付声明对得上** | 你说"做了 X 功能"，产物里就**真的有 X**。交付前最后一次**回读自己的交付声明**，逐项在产物里找位置；指不到的，要么补做，要么把那句改成"未完成 + 原因" | — |
| 4 | **失败两次换路** | 同一动作连续失败第 2 次，禁止同法第 3 次；先判断是否与已验路径等价，等价就改代码审查，别死磕 | — |
| 5 | **全绿不算证据** | 交付前把要防的错误**故意做一次**，断言变红才算验过。变异后仍全绿 = 变异没生效，须先确认改动生效。用例覆盖输入域分段（正常/边界/异常） | — |
| 6 | **关键数字重算** | 数据/研究类交付的关键数字，用独立方法重算或双源交叉验证；对不上以**重算为准**，不照抄第一遍 | — |
| 7 | **临时物隔离** | 运行时临时文件不进交付目录、收尾清掉；清理只动本任务自己的目录，**禁全局杀进程** | — |
| 8★ | **防死循环** | 同一文件连续读 3 次无新信息就停；同一动作连续做 3 次输出相同就换思路，别在原地空转耗 token | 必做 |

### 4.4 三形态协作（可叠加，非三选一）

| 形态 | 何时使用 | 关键约束 |
|---|---|---|
| **形态一 · 单智能体** | **默认**。自己一个模型干完 | — |
| **形态二 · 子智能体** | **有明显增益就自觉开，不等用户说**——能并行跑两件事 / 要独立挑刺视角 / 怕中间过程污染主上下文。除非用户明确说不要 | 派发给清三样：**目标 / 完成标准 / 交回给谁**。子智能体交回后**主 Agent 仍是 DRI，必须自己验收**；子智能体不直接对用户；一个人能连贯干完的事不开二 |
| **形态三 · 多智能体** | **命中任一就考虑，先与用户确认再动手**——用户指名多 Agent / 指挥官 / 让另一个 AI 干 / 任务大到要分工 / 要跨模型。因为要建 `_agents/`、写任务包，有外部副作用 | 先问用户"这个任务适合多智能体分工，要不要开？"，同意后再走六步：指挥官身份声明 → 建立角色档案 → 拆子任务写任务包 → **用户转述**派发 → 对照原始目标验收（先查跑偏，再交审查者挑刺）→ 向用户汇报三件套 |

**形态三的任务包七要素**：背景 / 已定决策 / 未定缺口 / 完成标准 / 允许与禁止范围 / 唯一 DRI / 交回给谁。

**三个角色卡**（`templates/`）：

- **指挥官**——默认 DRI，委派不转移最终责任；
- **执行者**——只说"按标准做完了，请验收"；
- **审查者**——独立挑刺、不亲自改活。

**红线**：执行者说「我做完了」不算验收；审查者不亲自改；不绕开指挥官直接汇报。

### 4.5 加载证明协议

被要求证明已加载时，输出：

1. **版本号**（`VERSION` 文件内容）；
2. **五阶段时序**（阶段1 自由构想 → 阶段2 规则规划 → 阶段3 执行 → 阶段4 直觉检查 → 阶段5 纪律检查）；
3. **逐字引用**纪律第 1 条：「真打开看一眼：产物在真实环境打开、真用一遍，不许只看代码或心算就宣布完成。」；
4. **协作形态**说明（默认形态一；形态二明显增益自觉开；形态三命中后先与用户确认）；
5. **实际读过的文件清单**。

> 没有读到 `SKILL.md` 或 `VERSION` 时：**不伪造**，停止并请求只读权限。

### 4.6 交付物格式（"三件套"）

装上后，交付消息自带三件：

```text
做了什么：……
怎么验的：……（可复现命令）
哪些没验：①XX——原因是XX；②XX——原因是XX
```

区别不在格式好看——是你**一眼就知道哪些话能信、哪些还得自己再验**。

---

## 5. 运行限制

### 5.1 纪律层面的固有限制

| 限制 | 说明 |
|---|---|
| **"忘记 skill"不可强制** | 单轮上下文内模型无法真正遗忘已加载内容。"忘记"是**意图引导**，改变的是注意力优先级，不是可验证的机制 |
| **"想清楚了"无判据** | 阶段1 的出口条件无法机械判定，可被形式化应付 |
| **意图引导不可外部验证** | 阶段1 / 阶段4 的效果只能靠软维度盲评或使用体感判断 |
| **规则只覆盖已知失败模式** | 有限文本无法穷举无限缺陷——这是结构性上限，非缺陷 |

### 5.2 边界条款

> **只改完成任务必须改的地方**；发现会让交付物坏着交的问题顺手修掉，**其余不碰**。

### 5.3 实测出的运行代价

| 代价 | 实测值 | 来源 |
|---|---|---|
| 验证的时间占比 | **35–40%**，净增量约 10–15% | Test-Bed 4（现行） |
| 对创意/纯视觉产物的死重条款 | 7 条里有 **2–3 条**（如变异测试、数字重算）没有落点 | Test-Bed 4（现行） |
| 创意类任务增量最小 | **+1.6**（对比建模/冒险类 +2.6~2.8） | v1.2.5 实验表〔**旧版**〕 |

> **建议**：创意/纯视觉任务走**轻量档**（只做 3 条）。
>
> 〔**旧版**〕= 该数据测于 v1.2.x 时代版本；v1.4.x 极简版起已改为"少量特性 + 遗忘机制"，**现行 1.5.0 不再适用此数据**。前两行来自 Test-Bed 4（v1.4.49），对现行版本仍有效。

---

## 6. 外部依赖

### 6.1 运行时要求

| 项 | 要求 |
|---|---|
| 宿主 | 任意支持 Agent Skill 的运行时——目录型（Claude Code / WorkBuddy 等，读 `SKILL.md`）或 `AGENTS.md` 型（Codex / Gemini CLI / Copilot CLI 等） |
| 网络 | **不需要**（唯一例外：阶段2"动手前调研"建议联网，但非强制） |
| 代码执行 | **不需要**（skill 本体零代码） |
| 第三方库 | **无** |

### 6.2 文件依赖（按需加载）

| 场景 | 必须文件 |
|---|---|
| **加载** | `SKILL.md` + `VERSION`（**仅此两个**） |
| 阶段2 规划 | `references/plan-rules.md` |
| 阶段5 审查 | `references/review-rules.md` |
| 叠加形态二三 | 追加 `references/multi-agent.md` + `templates/*.md` |
| 仓库自检 | `scripts/selfcheck.py`（开发工具，**不在加载路径上**） |

> ⚠️ **安装时拷整个文件夹**，不要只拷 `SKILL.md`——`references/` 与 `templates/` 是按需加载的，缺了它们多智能体场景会失效。

### 6.3 安全模型（零风险面）

- 运行时面**纯文本**：加载全程不运行代码、不发起网络请求、不上报数据；
- 唯一的脚本 `scripts/selfcheck.py` 是**仓库一致性自检**：只读仓库内文件、无网络、无 `shell=True`；
- 详见 `SECURITY.md`。

---

## 7. 安装与验证

### 7.1 目录型运行时（Claude Code / WorkBuddy 等）

```bash
git clone https://github.com/JadeYingWah/gpt-series-reasoning-style
cp -r gpt-series-reasoning-style ~/.claude/skills/    # WorkBuddy 用 ~/.workbuddy/skills/
```

### 7.2 AGENTS.md 运行时（Codex / Gemini CLI / Copilot CLI 等）

```bash
git clone https://github.com/JadeYingWah/gpt-series-reasoning-style
cd gpt-series-reasoning-style    # 在仓库目录内启动 agent，AGENTS.md 入口路由自动生效
```

### 7.3 验证安装

```bash
git pull    # 更新；版本号见 VERSION 文件
```

**功能验证**：问 agent「**你的版本号是多少？加载证明需要哪几个文件？**」——应答 `1.5.0`，说得出五阶段时序，并能逐字引用第 1 条纪律。

**仓库自检**：

```bash
python scripts/selfcheck.py    # 21 项静态检查，退出码 0=全过 / 1=有失败
```

---

## 8. 文件清单

| 文件 | 字节 | 角色 |
|---|---|---|
| `SKILL.md` | 1834 | **规则权威与五阶段流程表**。运行时只加载它 + `VERSION` |
| `VERSION` | 5 | 版本号（`1.5.0`） |
| `AGENTS.md` | 2505 | 跨运行时入口路由，**仅指路，无规则**；冲突时以 `SKILL.md` 为准 |
| `references/plan-rules.md` | 2321 | 阶段2 规划规则（保留构想 / 形态叠加 / 风险分级 / 档位 / 退出条件） |
| `references/review-rules.md` | 2547 | 阶段5 审查规则：**八条纪律**（含第3条「交付声明对得上」）+ 退出条件 |
| `references/multi-agent.md` | 2273 | 形态二三细则：命中信号、派发规范、六步操作、红线 |
| `templates/commander.md` | 1034 | 指挥官角色卡 |
| `templates/executor.md` | 810 | 执行者角色卡 |
| `templates/reviewer.md` | 795 | 审查者角色卡 |
| `scripts/selfcheck.py` | 3541 | 仓库一致性自检（21 项，纯只读） |
| `README.md` | 15635 | 面向使用者的介绍（中英双语） |
| `SECURITY.md` | 2488 | 安全模型说明 |
| `social-preview.svg` / `.png` | 7740 / 357785 | 仓库横幅（1280×640） |
| `LICENSE` | 1068 | MIT |
| `.gitattributes` / `.gitignore` | 257 / 351 | 仓库配置 |

**加载路径**：平时只读 `SKILL.md` + `VERSION`；阶段2 才读 `plan-rules.md`，阶段5 才读 `review-rules.md`；多智能体场景再读 `multi-agent.md` 与模板。

---

## 9. 实测证据

实验素材与统计脚本在 [`experiments` 分支](https://github.com/JadeYingWah/gpt-series-reasoning-style/tree/experiments)。

### 9.1 素材规模（口径见 §9.2）

| 来源 | 实验批次 | 臂次 | 文件 |
|---|---|---|---|
| v1.2.x（历史） | 32 | 225 | 2880 |
| desktop-beds-2026-09 | 8 | 35 | 127 |
| test-bed1~4 | 13 | 26 | 163 |
| collected-from-workbuddy | — | — | 47 |
| **合计** | **53** | **286** | **3217** |

### 9.2 统计口径（唯一权威）

复跑：`python experiments/stats-experiments.py`

- **实验批次** = 含至少 1 个臂目录的顶层目录；
- **臂次** = 一个「任务 × 一个臂」，即一个臂目录；
- **文件** = 全部文件（已排除 `node_modules` / `__pycache__` / `.workbuddy` 等）。

> **局限**：臂目录命名跨批次不统一（test-bed 用 `arm-A-skill`、desktop-beds 用 `Skills_Yes`、v1.2.x 用 `A-skill`/`B-noskill`），正则为尽力覆盖，**「臂次」是下限值，不会高估**。若按「臂/子目录数（含嵌套）」这一更宽口径统计约 328——**两种口径都对，引用时须注明**。

### 9.3 可引用的硬数字

| 结论 | 数字 | 来源 |
|---|---|---|
| 软维度（质量/纪律评分）提升 | **+20~24** | P1-5 |
| 反例验证执行率 | **带 skill 100% vs 无 skill 33%** | P1-1 终报 |
| 自我校准缺口率 | **无 skill 100% → 带 skill 约 33%** | P1-2 自我校准分析 |
| 交付可信度（非代码质量）提升 | 所有实验一致 | Test-Bed 1 |
| "真打开看一眼"能抓到代码审查抓不到的缺陷 | 视觉类缺陷 | Test-Bed 3 / 4 |
| 判定台可信度 | T6/T7/T8 三套，均通过"变异全灭 + GOLD 零误杀 + 判定门反向自查" | P1-7 终报 |
| 自检可信度 | 21/21 通过；3 个注入变异**全部被杀**（exit 1） | 2026-09-16 实测 |

---

## 10. 已知边界

这一节写的是**我们实测出来的局限**——不是谦虚，是口径。

> **版本适用性说明**：标注「**旧版**」的条目测于 **v1.2.x 时代**（v1.2.2 / v1.2.3-draft / v1.2.5）。v1.4.x 极简版起已删除硬指标化与繁复条款、改为"少量特性 + 遗忘机制"，**这些旧版结论在现行 1.5.0 上不再适用**；未标注者为现行版本仍需知悉的边界。

- **不兜底**〔**旧版** v1.2.2 / v1.2.5〕——2026-09 的 n=2 对照实验（三个机械判定任务）显示：在**致命缺陷率**维度上，带 skill 的臂与不带 skill 的臂**没有拉开可辨的差距**，held-out 上甚至略差。这个反向结果也放在仓库里（`experiments` 分支）。**该结论测于 v1.2.x 旧版本，v1.4.x 起不再适用。** 防线靠证据与独立复验，不靠条款。
- **不提升代码质量**——代码本体差别不大，变好的是交付可信度。
- **不是加速器**——验证习惯占去约三到四成时间预算，换来的是"敢直接用"的交付。**要最快出活，这个 skill 不适合你。**
- **对创意产物部分条款偏重**——七条里有 2–3 条对纯视觉/创意产物没有落点，这类任务建议走轻量档。
- **加条款不等于更好**〔**旧版** v1.2.2 / v1.2.3-draft〕——受控对照显示：纪律硬指标化后评分**并未提升**（原则引导 58.17 vs 硬指标 57.00，差 +1.17 落在判分误差内，判定为**等效**），故最终**不实施硬指标化**；更重的 v1.2.5（179 行 / 77 条自检）被实验证伪并废弃。**规则越少越好，但核心那几条不能少。**
- **Test-Bed 4 设计有污染**——B 臂执行者此前加载过旧版 skill，不是干净对照，其结论不作为有效性证据。
- **自报 ≠ 验证**——14 个实验臂全部自报"全过 + 变异有效"，oracle 仍判出大量 fatal。这个 gap 正是本 skill 存在的理由，也是它的天花板：它降低"假完成"，不能保证"真完成"。

---

## 11. 设计哲学

- **规则越少越好，但核心那几条不能少**——实验反复投票出的最终结论；
- **创作是创作，检查是检查**——"忘/想"交替的全部理由；
- **证据高于声称**——全绿不算证据，断言红过才算验过；
- **责任不随委派转移**——子智能体交回后，主 Agent 仍是 DRI。

---

## 附：快速上手

```text
1. 装好（§7：目录型拷文件夹 / AGENTS.md 型 cd 进目录）
2. 问 agent「你的版本号是多少？加载证明需要哪几个文件？」验证生效（§7.3）
3. 正常派活——无需任何特殊指令，交付型任务自动进入五阶段时序
4. 检查交付消息是否自带三件套：做了什么 / 怎么验的 / 哪些没验
5. 创意/纯视觉任务留意轻量档（§5.3）
```

**版本策略**：

- **v1.4.x 极简线**——五阶段时序、文件级渐进加载、协作形态叠加。**当前主线**。
- **v1.2.x 重版线**——179 行、模块矩阵、self-test 冻结 77 条。**已被实验证伪，该线已废弃。**

---

*MIT License · 本说明书对应版本 1.5.0*
