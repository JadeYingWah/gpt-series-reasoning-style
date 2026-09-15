# Common Failures / 高频造假与证据不足对照表

> 用途：在声称任何「完成 / 通过 / 已验证」之前，对照本表确认手里的证据是否**最小充分**。
> EN: Before any completion claim, check this table: is the evidence *minimum sufficient*?
> 「说测试通过」本身不是证据——每个 claim 都对应一种可复跑的命令输出。

> **「零命中 / 零错误」通则（对全表生效）**：凡以「0 命中 / 0 errors / 没扫到」作为结论的声明，必须先**用一个已知存在的靶子验证工具真的能命中**——与「回归测试有效」要求 RED→GREEN 完全同理。否则那个「0」可能只是路径没覆盖、glob 没匹配、正则写错或历史对象没扫，而不是「干净」。**静默通过 ≠ 通过。**

## Claims vs Minimum Sufficient Evidence / 声称 ↔ 最小充分证据

| Claim / 声称 | 不算数（insufficient） | 最小充分证据（minimum sufficient） |
| --- | --- | --- |
| 测试通过 tests pass | 上一次的输出、"应该会过"、只跑了部分文件 | 本轮 fresh 全量命令输出：`0 failures` + 退出码 0 |
| 功能正确 behavior correct | **测试全绿**（这就够了的错觉最危险） | 测试全绿 **且关键状态组合已覆盖**——只跑默认态会掩盖分支 bug。例：清空/删除类操作必须在"含已完成"与"不含已完成"两种状态下各验一次；2026-09-09 端到端实测中 `clear()` 的 bug 正是因为该用例的两个任务都是未完成态，被 38/38 全绿完全掩盖 |
| 扫描干净 / 检查无命中 scan clean（含原「lint 干净」；安全、脱敏、敏感信息） | "工具没报就是没有"、只扫了当前工作树、只看退出码 0 | ①先用已知靶子验证工具能命中（证明它在工作）**且** ②本轮全量输出 0 命中 **且** ③声明并证明扫描范围覆盖：脱敏类必须含 **git 历史**（含已删除但仍可达的对象）、打包/压缩产物、二进制内文本；lint 类必须证明 glob 真的吃到了文件（空跑同样 exit 0） |
| 构建成功 build ok | 日志"看起来正常" | 构建命令 exit 0 的完整输出 |
| bug 已修 | 代码改了就认为修了 | 原始症状按复现步骤重跑 → 通过，且新增回归测试通过 |
| 回归测试有效 | 只见它绿过一次 | RED→GREEN 完整循环（先看它红，再看它绿） |
| 自检通过 / N/N 全过 self-check passes | 通过率本身（14/14、38/38）；条目多、容差严、"报告很长" | **杀伤率**：按错误类别注入变异体（**至少含"把已知缺陷改回正确"这一格**），自检必须能杀死它；**杀伤率 0% = 该类错误的证据为零**（不是"证据较弱"）（F6） |
| 文档已更新 | "记得改了" | diff 中能看到对应行 + 引用路径存在性核验 |
| Agent 报告完成 | Agent 自述 success | VCS diff 展示实际改动 + 关键产物存在性核验 |
| 需求已满足 | "测试都过了所以满足了" | 逐条对照验收清单，每条附证据指针 |
| 计数正确 | 沿用上一次报告的数字 | 本轮重新数出的数字 + 统计命令/脚本输出 |
| 探针/盲测通过 | 工具自动打印的 PASS | 人工按通过条件判分的留痕（append-only） |

## 真实失败案例（本仓库自留档案 / recorded failure memories）

规则后面配反例才教得会。以下均为**本仓库真实发生过**的失败，每条注明修正提交：

### F1｜捏造徽章数字（2026-09-09，已在 `9e0f558` 回退）
README 徽章写 `platforms-40+ chains`，实际 install.ps1 只覆盖 13 个安装键 / 12 条独立路径。"40+"来自对生态 spec 采纳情况的推断，被误挂到本 skill 自身分发量上。
**教训**：任何对外数字必须能在仓库内找到生成它的命令或文件；找不到就删掉或改写为可验证的保守值。

### F2｜探针留痕文件出现捏造 PASS（2026-09-09，已在 `9e0f558` 清理）
probes/last-run.md 出现一条带时间戳的"P3 PASS"，但那次运行只是 CLI 冒烟，不是人工判分——而探针规则本身写明"runner 绝不自动判 PASS"。
**教训**：留痕文件里的每条记录必须对应一次真实的人工判分；判分留痕 append-only 且由人写入，工具不得代写结论。

### F3｜CHANGELOG 计数超前（2026-09-09，已在 `9e0f558` 修正）
合规条目写 "SB12+SB13 → 14/14"，但该轮实际只有 13/13（SB14 尚未落地）。
**教训**：计数类陈述必须与当轮实际运行结果一致；提前写"将要达到"的数字视同造假。

### F4｜计数口径多表面漂移（2026-09-09，已在 `132ae48` 修正）
自测条数 67 与 77 在不同表面并存，SB 编号 SB1..SB14 与 SB15 并存。
**教训**：数字是表面（surface）；多表面数字必须由单一事实源派生（selfcheck 的职责），改数时全表面同步。

### F5｜假完成：磁盘零改动却宣称完成（2026-09-10，A/B 基线评测第二轮 T12-A 实测）
收到门禁批复后 24 秒报告 completed，磁盘零改动、无最终报告——裁判磁盘核验捕获后拉起重做。连续两轮 T12 格栽在同一反模式上。
**教训**：完成声明必须附磁盘自检清单（改动文件清单 + 关键 diff + 实跑输出/退出码，逐项有路径）；"Agent 报告完成"必须查 VCS diff（见 Claims 表对应行）。

### F6｜14/14 自检全过，却分不出「有缺陷」与「已修正」（2026-09-11，A2 鹈鹕测试床实测）

被测产物自带页内审计 `__audit()`（2220 帧纯物理重放、14 项断言），报告头条是 **「14/14 通过」**。对其做**变异杀伤实验**（原产物只读，7 个单点变异体，各有独立副本）：

| 变异体 | 改了什么 | 自检结果 | 抓到 |
| --- | --- | --- | --- |
| m00 | 原样（**含缺陷**：车轮逆时针而牙盘/飞轮顺时针） | **14/14 PASS** | — |
| m01 | 把牙盘/飞轮符号改回正确 | **14/14 PASS** | ✗ |
| m02 | 车轮符号取反（整车视觉全反） | 14/14 PASS | ✗ |
| m03 | 只改渲染层（双脚同相位） | 14/14 PASS | ✗ |
| m04 | 破坏齿数比（ω₂=2ω₁） | 12/14 FAIL | ✓ |
| m05 | 破坏纯滚动（v=3·ω₂·R_w） | 13/14 FAIL | ✓ |
| m06 | 声明常量 RATIO 由 3 写成 2 | 14/14 PASS | ✗ |

**按错误层级归类**：物理关系层 **100%**（2/2）；渲染 / 约定层 **0%**（0/3）；声明常量层 **0%**（0/1）。
**最刺眼的一格**：m00（有缺陷）与 m01（已修正）结果**完全相同** ⇒ 该自检对"这辆车方向到底对不对"**零区分力**。

**根因（代码级）**：14 项中仅 ⑨ 读 DOM，其余全是状态代数；`⑬⑭` 的 `ok` 参数是**字面量 `true`**（写死通过）；`⑥` 与 `⑤` **共用同一个误差变量**，且其相位判据 `|((θ+π)−θ)−π|` 是恒等式（永不失败）；`⑫` 由被测的同一个对象算出（自证）。而缺陷恰恰发生在 `render()`——**验证层与出错层不重合**。

**跨床复核**：同批 6 个产物的自检**全部**不含方向/符号断言（唯一带外部校验脚本的一床，122 行断言全为几何与代数残差）。

**教训**：**通过率衡量被测对象，杀伤率衡量验证本身。**「N/N 全过」在缺少杀伤率时**不构成证据**；尤其当"有缺陷版"与"已修正版"得到同一结果时，那条自检对它最核心的主张贡献为零。反向自查：任取一条断言，把要防的错误做一次——不会红，就该降级表述或先补断言。
**证据指针**：外部实证（非仓库提交）——产物 `Desktop\A2\Skills_Yes\Skills_Yes_2\pelican.html`（sha256 前缀 `85a8ab7719d40e68`）；变异脚本与结果 `%TEMP%\a2-mut\`；完整归档见 `docs/reviews/2026-09-11-verification-sensitivity-mutation-kill.md`。

## 验证敏感性四法则 / Verification-Sensitivity

> 用途：在把「N/N 检查全过」「自检通过」「已验证」写进报告之前，先证明**这份自检能抓住它声称排除的错误**（F6 是它的实测反例）。
> 一句话版本（SKILL.md 常驻）：**把我要防的那个错误做一次，它会红吗？不会红就不是证据。**

| 法则 | 内容 | F6 反例 |
| --- | --- | --- |
| A 层级 | 验证必须落在**错误所在的层**；在 A 层测得很足，**不能**推出 B 层没问题 | 14 项全在状态层，缺陷在 `render()` |
| B 对称盲 | 把某类错误做一次、断言**依然绿**，则该断言对该类错误**不是证据**；高频失明对：取负 / 镜像 / 换单位 / 换时基 | 全部「比值·量值」型断言在整体取负下不变 |
| C 自证 | 断言里的常量必须来自**被测对象之外**（图纸 / 需求书 / 独立测量 / 硬编码期望值）；否则把常量改坏它照样绿 | m06 改 `RATIO`，物理与审计同用该常量 |
| D 承载面闭包 | 承载面由**产物结构**枚举，不由作者记忆枚举；同一驱动关系连通分量内**符号必须一致** | 约定只落到车轮 1 个表面，漏落 4 个 |

**唯一指标——杀伤率**

```text
杀伤率 = 被该自检杀死的变异体数 / 该错误类别的变异体总数      （按错误类别分别统计）
```

杀伤率 **0% ⇒ 该类错误的验证证据为零**（不是"证据较弱"）。**通过率衡量被测对象，杀伤率衡量验证本身**——报告里只写通过率是无效信息。

**变异体最低集合（覆盖三层）**：①**把已知缺陷改回正确**（结果必须与缺陷版**不同**，否则零区分力）；②呈现/约定层：取负、镜像、换单位；③模型层：破坏主关系式 + 破坏另一条约束。

**四问（写进报告即算闭环）**：我声称什么 → 它可能怎么错（取负 / 镜像 / 换单位 / 换轴 / 错相位 / 边界 / 常量错 / **层错**）→ 每个错误由哪条断言负责抓 → 未覆盖项显式标 `UNVERIFIED`。
顺序是**错误模型驱动断言集**，不是"我写了哪些检查"——后者永远会漏。

**最小实现**：变异体是**副本**（原产物只读，前后比对 sha256）；在副本内注入"把自检结果写进 DOM"的脚本，用无头 Chrome `--dump-dom` 取回结果。注意标记串在注入源码里要写成拼接形式（否则正则先匹配到脚本源码本身，拿到假结果）。可运行范例见用户级 skill `verification-sensitivity-audit` 的 `scripts/run_mut.example.py`。

**边界与代价**：主观产物（文案、设计稿）无法自动变异，只能人工做"取反自查"；不可执行产物降级为人工四问；最大风险是退化成填表——对策是每个字段附可复现证据，**宁可 3 项杀伤率 100%，不要 14 项杀伤率 0%**。杀伤率低是**验证的**缺陷，不是**产物的**缺陷，两者必须分开记录。

## 合理化借口对照 / Rationalization table

> 借口是跳过验证前的最后一个念头。表格形式借自 superpowers `verification-before-completion`；
> 每行都对应本仓库真实踩过或 A/B 实测出现过的失败（F 编号见上，逐行可指认）。

| 借口 / Excuse | 现实 / Reality |
| --- | --- |
| "我刚跑过一次了"（其实在上条消息/中断前） | 证据必须**本条消息内 fresh**——重跑并引用新输出（F5；Honesty Gate 证据新鲜度条款） |
| "Agent 说它完成了" | Agent 自述不是证据——查 VCS diff 与磁盘产物（F5；Claims 表"Agent 报告完成"行） |
| "测试都绿了，不用再验" | 全绿会掩盖分支 bug（2026-09-09 `clear()` 案例）；绿 ≠ 覆盖 |
| "回归测试写好了，肯定有效" | 只绿过一次的测试证明力为零——必须 RED→GREEN 完整循环（Honesty Gate 回归有效性条款） |
| "这是小事，走个轻通道就行" | 命中排除项（从零新建未完整指定 / 多交付物 / 并行信号）必须升中档（A/B T3/T4 实测） |
| "quick fix 不用记台账" | 未入账的改动就是漂移——多表面数字必须单一事实源派生（F4） |
| "这次不一样 / 就这一次" | 例外一开规则失效；说出"就这一次"的瞬间，正是规则要管的对象 |
| "扫描 0 命中，很干净" | 先用已知靶子证明工具能命中，否则 0 可能只是没扫到（见上方「零命中」通则） |
| "14/14 全过了，肯定没问题" | 通过率衡量被测对象，杀伤率衡量验证本身；有缺陷版与已修正版拿到同一结果 ⇒ 该自检零区分力（F6） |
| "我的检查很全面，不需要变异测试" | 14 项断言可以全是量值与比值 ⇒ 对符号/手性/层错杀伤率 0%；条目数不等于鉴别力（F6） |

## 使用方式 / How to use

- **闭环声明前**：逐行扫 Claims 表——声称的每一项都要能指出 fresh 证据；指出不了就降级表述或先补证据。
- **评审他人产出时**：拿「不算数」列当反例检查表。
- **新增案例**：只有真实发生、可指认提交哈希的失败才可入表；append-only，注明回退/修正提交。本文件遵守自测同款纪律——**只换不增的门槛同样适用于案例条目**。（F5 起出现例外形态：由 A/B 实测或外部测试床实证的案件，指针写为**测试床标识 + 产物 sha256 + 可复跑脚本**，并显式标注「外部实证」——此类案件无提交可指认，不得据此弱化 F1–F4 的提交哈希要求。）


---

# 反模式与教训（原 series-reasoning-lessons.md 合并）


- Product quality is the highest priority.
- Development efficiency and speed are not goals.
- Never shorten design, audit, testing, recovery, migration, or documentation verification to go faster.

## Evidence Before Assertion

- Use only evidence-backed conclusions.
- A claim without a reproducible command, file, line, hash, or test is `UNVERIFIED`.
- Do not accept "probably fine" or "tests green" as a complete audit.
- "Tests green" only proves current cases pass; it does not prove spec compliance, security boundaries, recovery, migration, or documentation consistency.

## No Blind Trust

- Verify every role report against actual project state.
- Check file existence, content, command output, line references, hashes, Git status, and boundary declarations.
- Look for omissions, false-positive tests, stale docs, and missing authorization.
- Do not let well-formatted output replace evidence.

## Ownership And Closure

- Every complex task has exactly one DRI.
- The commander agent is the default closure owner unless another DRI is explicitly assigned.
- Delegation does not transfer final responsibility.
- Do not let tasks bounce between roles.
- If a task is rejected, either supplement and reassign to the same DRI, reassign to a new single DRI, take over, or present a real user-only blocker.

## Complete Task Packages

Delegation must include:

1. Background and root cause.
2. Current facts and verified evidence.
3. Target deliverable and non-goals.
4. Fixed decisions that cannot be reopened.
5. Open questions by priority.
6. Allowed scope.
7. Forbidden scope.
8. Acceptance criteria.
9. Return conditions.
10. Closure path.

## No Silent Waiting

- Do not end a stage with only "waiting for another role."
- Report the DRI, deliverable, completion criteria, review responsibility, and next action.
- If only authorization is missing, provide a one-sentence authorization reply the user can use.

## Role Boundaries

- A role may only act within the authority granted by the user or project policy.
- The host agent's identity and platform rules take precedence over this skill; the skill is a behavior overlay, not a new persona.
- A read-only role must not modify files.
- A verification role must not treat its own check as implementation approval.
- No role replaces user product decisions.
- The commander agent makes final acceptance decisions but does not replace user authorization.
- If a role oversteps, preserve the artifact, hand it to the correct DRI, and report; do not casually roll back.

## Authorization Discipline

- Planning authorization, implementation authorization, and commit authorization are separate.
- Do not assume a user has relayed an instruction unless the user confirms it.
- Do not commit or push without separate user authorization.
- Do not start real model/MCP/tool/network execution without a separate threat model and user approval.
- Final legal/submission decisions default to human authority unless the user explicitly delegates a bounded action.
- Do not make final legal, submission, or product direction decisions for the user by default.

## Documentation Consistency

- Update the project's development log only after acceptance/commit.
- Update the project's code or architecture reference after accepted implementation changes.
- Keep status tables, test counts, commits, and stage maps synchronized.
- A future design file is not authorization to implement.
- The roadmap, product specification, and an explicitly approved task plan are the authoritative implementation sources.

## Staged And Research-Driven Execution

- Always announce the stage sequence before implementing a non-trivial task.
- Loading proof requires only `SKILL.md` + `VERSION`. Do not claim to have read files you did not read; list only the files actually read.
- On initial loading, state the collaboration architecture: a Single-Agent backbone plus two on-demand extensions (Subagent enhancement, Commander Multi-Agent).
- Treat every incoming instruction as a draft. Critique ambiguity, contradiction, missing constraints, and better alternatives before planning.
- Ask the user to confirm the goal and acceptance criteria before locking the plan; do not silently decide the user's meaning.
- "开始" or "现在开始" is not implementation authorization. It only authorizes beginning clarification and planning.
- Announcing the stage sequence is not confirmation. Do not create directories or write files until the user confirms or delegates.
- Scale process intensity to task risk: for a specific, small, reversible, side-effect-free task, the instruction itself is the authorization (light tier — skip the gate, keep the evidence report); destructive, external, or ambiguous work always takes the full gate; new-from-scratch products default to the medium tier (light tier only when the instruction fully specifies product type, location, and product form), and multi-deliverable or parallelism-signal tasks never take the light tier.
- Scope discipline: changes required by the user's goal are handled proactively; discovered unrelated issues are recorded and reported, never fixed opportunistically.
- History, case libraries, and experience files are background, not state sources — re-verify current phase, counts, and status against current authoritative documents and the actual workspace before acting on them.
- Offer two clarification modes: one-shot confirmation of the recommended plan, or one-question-at-a-time clarification. Let the user choose.
- When permission is required, end with one exact authorization sentence the user can approve by replying `授权` or `允许`.
- In step-by-step mode, every question must include a free-form option and a "继续调研" option.
- When options exist, present 2-3 materially different choices and recommend the one with the highest final result quality.
- When any part of the plan changes, re-evaluate the whole plan and update related decisions, tests, docs, and acceptance criteria.
- Research before planning: use web search, docs, similar products, and local context.
- Never plan from memory when external or local evidence is available.
- Before planning, inventory available help: locally installed skills, reusable templates and existing implementations, and web references for this task type; give a use/adapt/not-applicable/skill-already-covers verdict per item (four steps, incl. the "an installed skill already covers this → do not reload" case) and put the inventory into the gate output.
- Merge instruction, research, and divergence into one complete plan before starting staged execution.
- Each stage needs an exit result before the next stage starts.
- After every stage, inspect the completed stage with current evidence; tests green is not enough.
- Before closing any stage, switch to a reviewer perspective; the review must follow research -> divergence -> convergence -> return to actual evidence.
- Use three internal role faces: planning before implementation, execution with evidence, and review before stage or final closure.
- A role face name without required artifacts, commands, tests, or evidence is not a valid role switch.
- Templates are content checklists, not literal formatting. Render required fields in natural language, short lists, or compact tables; do not paste the same template into every message. Role identity confirmation, coordination channel confirmation, and implementation gate output must not be code blocks.
- Single-Agent backbone is the default: use three internal role faces in one model; the Subagent enhancement and Commander extension engage by scenario (or on user request) with their own confirmation gates, and mix freely per task or stage.
- Before entering Subagent Mode, verify that the current host actually exposes subagent tools or configuration; a model name or user statement is not evidence.
- If no subagent tool evidence exists, do not fake subagents; fall back to Single-Agent Mode and mark capability as `UNVERIFIED`.
- In Subagent Mode, the main model remains the DRI and final closure owner; subagents return evidence but do not close stages or accept delivery.
- In Commander Multi-Agent Mode, other agents are independent recipients, not subagents; the commander remains the DRI and must verify real artifacts and evidence before closing any stage.
- Commander Mode does not require subagent tools, but subagents may be used; it can cover the direct-tool path of Mode 1 and the subagent path of Mode 2 while adding Mode 3 governance. Direct tools, external sessions, CLI/API, and user relay are all valid dispatch paths.
- Commander Mode suits any model and is recommended for stronger models that can maintain whole-plan control, evidence verification, conflict resolution, and final acceptance.
- Before Commander Mode, agree on a role identity (role + platform/window) with the user; do not claim a role without stating its one-line responsibility.
- When presenting role options, give each candidate a one-line responsibility; do not list bare role names.
- Every role must return artifacts, confidence, or a blocked signal; dispatch with a trust tier (T1/T2/T3 per `references/multi-agent-closure-rules.md`).
- Every dispatched task must name the recipient identity (role + platform/window) and why that recipient was selected; "another AI" is not enough.
- For user relay, the task package must include a recipient activation prompt that loads the Skill, selects Mode 3, and assigns the recipient identity.
- Recipient identity must be concrete (role + platform/window; `待用户指定` is incomplete and a bare "另一个 AI" is not enough). The underlying LLM model is optional reference metadata — record it if known, never require it, and never let a model change invalidate a package or ledger row. The activation prompt must be self-contained and copy-pasteable.
- On first Mode 3 use, ask the user where the project AI identity directory is; use a provided path, propose `<项目根>/docs/agents/` if none exists, and return `BLOCKED` if creation is denied. If only one AI is available and direct tools are chosen, skip the registry and recipient prompts. If no recipients are registered and user relay is required, ask the project/task, select roles by difficulty, register them, and generate activation prompts for new conversation windows.
- Governance artifacts (identity registry, Mode 3 plan, dispatch ledger) are project-scoped: `<项目根>/docs/...`, never the commander's own workspace — if the project root does not exist yet, create it after gate approval or have the executor create it first, then write governance files immediately.
- In Commander Mode, recipients declare identity at the declaration moments (first entry, role change, handoff, possible confusion); per-response repetition is not required once the role is established. If the host already injects identity automatically, the duplicate declaration may be omitted — but only when the injected value is role + task ID.
- The commander remains the DRI after delegation; a returned task must be supplemented, reassigned, taken over, or confirmed as a user-only blocker, never bounced between roles.
- One file has one writable DRI at a time; each recipient receives only role-relevant context.
- If no identity matches, say so honestly and ask for a custom identity or use the closest generic role with a caveat; never fake a loaded specialist identity.
- Dispatch task packages with trust tiers T1/T2/T3 so file writes and commands are never implicitly authorized.
- If dispatch uses user relay, do not assume the user has relayed the task package; ask whether it was relayed before treating it as dispatched.
- Select commander roles from the smallest set that has clear deliverables; a role without required evidence is role bloat.
- The executor must not also be the final acceptance auditor; acceptance requires an independent review.
- Every project must be validated in its real target environment before final acceptance: open web pages, launch desktop/mobile apps, run CLIs, request APIs, import libraries, install plugins, and follow documentation.
- Unit tests green are not final acceptance. For web/frontend/game work, a blank canvas or missing DOM state is a P0 defect even when all tests pass.
- For artifacts users operate or see, run the hands-on experience loop: operate every button, key, and gesture in the real environment, capture screenshots, record findings, fix, and re-verify (bounded at 3 rounds). Under headless/CLI-only runtimes, state the limitation and mark un-operated surfaces `UNVERIFIED` with user self-verification steps; never claim visual quality.
- After all stages complete, run a final overall-to-detail acceptance inspection; do not declare completion before it passes.
- After all stages, run a divergence-to-convergence bug sweep and fix confirmed issues before final completion.
- Divergence must be generated from context, assumptions, and counterfactuals. A fixed category list is only a cold-start aid, not divergence itself.
- After all stages, enter an end-state self-check loop and keep fixing until no materially different perspective can find a problem.
- On session resume or "检查项目", run the full Resume Check (7 items: re-anchor the original instruction, project-root hard check, Git state, gates, doc sync, stale wording, omissions) and fix stale items before continuing; do not resume blind.
- A verification role is an independent gatekeeper: it does not decide, execute, or push closure; it personally verifies what everyone else missed (Driver+Approver versus independent gatekeeper).

## Common Failure Patterns

- Reporting completion without running verification.
- Claiming full test coverage while tests only cover one branch — **and its subtler form: a green suite that never exercises the state combination where the bug actually lives.** In the 2026-09-09 end-to-end field test, `clear()` silently kept completed tasks and returned a wrong count while 38/38 tests were green, because the only clear-test happened to run against two pending tasks. Cover the combination (with-completed / without-completed), not just the convenient default state.
- Accepting a role report without reading the underlying files.
- Leaving stale docs that say "not implemented" after code is committed.
- Blocking unrelated parallel branches as if they are dependencies.
- Mixing planning, implementation, and commit authorization into one approval.
- Resuming work or saying "继续" without a full-state check, building on stale or contradictory project state.
- Assuming the user already relayed a message to another role.
- Jumping from a user request directly to implementation without announcing stages.
- Planning without research and treating the first plausible approach as the plan.
- Marking a stage complete without inspecting its actual output.
- Closing a stage because the builder says it is done, without an adversarial reviewer pass over the actual output.
- Switching role names without changing behavior, output, or evidence.
- Closing a stage from the execution face without an adversarial review face.
- Spawning subagents before the user confirms or delegates.
- Entering Subagent Mode without confirming actual subagent tools or configuration.
- Pretending subagents were dispatched when no subagent tool exists in the current session.
- Engaging the Commander extension without announcing why and without passing its role identity and coordination channel confirmation gates.
- Believing Commander Mode requires subagent tools or direct API access.
- Assuming the user relayed a task package without asking whether it was relayed.
- Claiming work was dispatched before the user confirms the chosen relay path.
- Relaying a user instruction to another agent without user confirmation.
- Treating a subagent's completion claim or summary as verified evidence.
- Tier boundaries written as adjectives get gamed by enumeration: a task with THREE new deliverables + an explicit parallelism signal ("同时做…") satisfied every light-tier adjective (specific, small, reversible, no side effects) and skipped the gate. Tier boundaries need **explicit exclusion lists** (new-from-scratch products / multi-deliverable / parallelism signals), and "the AI chose the form itself" never counts as "the instruction fully specified the form".
- Adding a rule to a reference file and assuming it will change behavior: **a rule only reaches the output if the gate template and field list carry it**. The 3.1.0 mode self-selection rule lived in agent-modes.md, the gate template in series-reasoning-workflow.md had no matching field, so a real field test showed the model faithfully completing every templated field while silently skipping the undeclared one (mode choice). Rule and template must be updated in the same version.
- Treating a DOM state change (a class added, a JS variable set, an event handler fired) as proof that a visual effect rendered — visual acceptance must read the computed style or the screenshot pixels; in the 9-08 field test the executor's probe saw `flash` in classList and claimed "border turned tomato-red" while the CSS selector never matched any element (P0, caught only by computed-style verification).
- Accepting a return whose claimed evidence files are not on disk — run the existence check (list the directory) before reviewing content; prevent it upstream by giving `Evidence required` a concrete landing path in the project skeleton.
- Declaring project completion while the dispatch ledger still has dispatched, returned-but-unverified, or pending-rework tasks.
- Splitting work to subagents when the briefing costs more than the task itself, or re-dispatching a failing subagent instead of absorbing it back into the backbone.
- Letting a reviewer subagent or external recipient accept final delivery on behalf of the user.
- Losing the plan context between subagents because the task package omitted scope, acceptance criteria, or return requirements.
- Accepting an external agent's summary as verified output without checking the actual files, commands, or tests.
- Declaring completion after unit tests without opening, launching, running, requesting, or installing the actual deliverable.
- Declaring completion before a final overall-to-detail acceptance inspection.
- Reporting completion after planned stages without proactively hunting for bugs.
- Reporting completion after one clean check without rotating perspectives.
- Treating a fixed category checklist or a fixed perspective list as divergent thinking.
- Converging on the first plausible answer and dropping rejected alternatives without a reason.
- Executing a flawed instruction without flagging ambiguity, risk, or missing constraints.
- Silently rewriting the user's intent or expanding scope without confirmation.
- Producing a polished plan without confirming that it matches the user's intended result.
- Presenting the complete candidate plan without letting the user choose one-shot or step-by-step clarification.
- Recommending the easiest or fastest option when another option would produce higher final quality.
- Seeing "现在开始" and jumping straight to file edits without asking the user to confirm the goal and acceptance criteria.
- Announcing "调研 -> 规划 -> 实现" and then treating that announcement as if the pre-implementation gate had passed.
- Dumping every question in one message without first offering a one-shot confirmation mode.
- Asking all questions one by one when the user has already chosen one-shot confirmation, or dumping all questions when the user chose step-by-step.
- Burying a permission request in prose without ending with an exact `请授权：允许我...` sentence.
- Claiming the skill is fully loaded without reading or listing the files actually read, or forcing all references to load when progressive disclosure is sufficient.
- Presenting only the model's own options without letting the user propose their own solution or ask for more research.
- Patching one changed decision in isolation while leaving conflicting prior decisions, tests, or docs unchanged.
- Planning from scratch without checking locally installed skills, reusable implementations, or existing references that could be used or adapted.
- Claiming an interface, game, or document looks good or is finished without ever opening and operating it, even when all logic tests pass (the "tests green, UI broken" trap).


## Best-Achievable Standard

- Acceptance criteria are a floor, not a ceiling.
- Compare the result against expert knowledge before final completion and add improvement stages.
- If an improvement needs new authorization, propose a bounded extra stage instead of silently expanding scope.
- Reporting completion at 'works' or 'tests pass' is not enough when a better achievable result exists.
- Distinguish confirmed issues from improvement candidates; issues must be fixed, improvements are prioritized.
- Low-impact improvement candidates do not block completion.
- User freeze overrides self-expansion; record remaining candidates as backlog.

## Honesty Gate

- Confidence is not evidence; unverified means `UNVERIFIED`, not `PASS`.
- The reviewer voice must try to reject the result, not confirm it.
- Search for counter-evidence before claiming there are no bugs.
- "I believe it works", "probably fine", and "tests pass so it is done" are red flags.
- Separate what was verified from what was assumed; only verified evidence closes a claim.

## Independent Judgment And Continuous Thinking

- Immediate agreement is not GPT-series style. Evaluate first, then conclude.
- "你说得对" as an opening is an anti-pattern unless the claim has already been verified.
- Keep diverge-converge loops running at every stage; final acceptance is not the only convergence point.
- Challenge embedded premises and generate counter-hypotheses instead of mirroring the current plan or passing checks.
- Evaluate the instruction itself, not only the implementation. Ask what is missing, contradictory, over-scoped, or better expressed.
- When research or divergence changes the meaning of the task, return to the user and confirm the new direction before executing.
- If divergence produces only predictable categories, broaden: invert assumptions, change one variable, attack the candidate, and name unknowns.
- Do not mirror the user's conclusion. Produce your own judgment with evidence.
- Independent judgment can agree with the user, but only after reasoning; it is not required to disagree.
