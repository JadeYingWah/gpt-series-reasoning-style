# 负增益场景改进·测试·优化总计划（2026-09-12）

> 依据：cycle3 + cycle4/A5 + 鹈鹕案全部实测，叠加外部研究（长上下文指令衰减 / CoT 简单任务负收益 / 指令合规天花板）交叉定位出六类「skill 低于不装」的场景。本计划是总指挥委托定制的下一阶段总方案：改进、测试、优化三线并行。**证据边界**：场景②③为本机 n=1 实锤；④⑤⑥为外部研究+机制推演，未在本仓模型组合实测——本计划的任务就是把它们变成实测。

## 六类负增益场景（计划的对象）

| # | 场景 | 证据状态 | 对应阶段 |
| --- | --- | --- | --- |
| ① | 简单/天花板任务（纯付成本） | 本仓盲测二 0 vs 0 + 外部 FLenQA/CoT 研究 | 优化线 O2 |
| ② | 创意/审美任务（方向锁死+注意力挤占） | 鹈鹕案实锤（v5 条款后方向反转，成本未解） | 优化线 O4 |
| ③ | 纪律形式执行反噬（虚假确认） | A3 案实锤（3/8），覆盖面条款仅 1 格 GREEN | 测试线 T2 |
| ④ | 长会话/多轮规则稀释 | 外部 IFScale 68% + 本仓 resume 漂移个案 | 测试线 T3 |
| ⑤ | 规则冲突/多 skill 叠加 | W1 实锤（B 臂靠他 skill 拿分）+ R2 完成门疑似宿主混淆 | 测试线 T1 |
| ⑥ | 时间/成本敏感 | 本仓 +14~21K/任务 + 鹈鹕 5 倍墙钟 | 优化线 O3 |

## 测试线（按序执行）

### T0 · 床2 落败追因（零成本考据，立即可做）

- **问题**：B2 37 vs A2 35 是唯一「败了但没被条款针对」的床。A2 丢的 5 分（缆车到达时序 1+0、节奏波次 1 等）是能力不及，还是流程开销挤占工程注意力（鹈鹕式）？
- **方法**：深读 A2 转写（`E:\Harness\ab-cycle4-effectiveness\transcripts\`），统计 A 臂流程性输出占比 vs B 臂；对照其 reasoning 里对时序设计的思考量。
- **判据（预注册）**：若 A 臂流程输出占比显著高于 B 臂且功能设计思考量更少 → 坐实挤占，产出「流程预算/门禁后注意力回归交付」候选条款；若功能思考同样充分但实现质量差 → 能力噪声，床2 结案不立项。

### T1 · 干净对照实验（cycle5-clean，解决 W1 的裸差欠账）

- **环境隔离协议（先于一切预注册）**：
  1. 隔离：`~/.agents/skills` → 改名 `skills.isolated`；宿主新会话验证 B 臂视角无任何用户级 skill 可加载（贴面板截图入证据）；
  2. A 臂：干净目录只装本 skill（SKILL.md+VERSION+按需 references）；
  3. 恢复：实验后改回原名并 cmp 验证目录完整（OB-02 纪律：只动本次目标，禁全局清理）；
  4. 隔离与恢复步骤**写进对话卡 v3**，防操作者临场发挥。
- **床**：复用床1（F6 证据鉴别力）+ 床3（M4），双床双臂 = 4 格，资产 md5 已验。
- **对话卡 v3**：第一段加载原文写死「加载skill：gpt-series-reasoning-style」。
- **预注册看点**：①B 臂在无生态可借时还能否 T3（预期：不能，裸差现形）；②床3 A/B 裸差幅度；③成本账 A−B 是否仍在 +14~21K。
- **裁决分支**：若某轴裸差为负（skill 臂 < 裸臂）→ 触发该轴条款降密提案，不以「至少流程合规」辩护。

### T2 · 异构 bug 床（cycle6-transfer，覆盖面条款的 GREEN 复现 + 泛化）

- **造床**：与时间进位**不同类**的分段敏感 bug，三选一或各一：字符串长度截断边界 / 日期跨月进位 / 浮点精度阈值。植入手法同床3（弱检查自检 + 隐藏真缺陷）。
- **跑法**：与 T1 合并同一干净环境跑（省一次隔离）；A 臂带 skill、B 臂裸。
- **预注册看点**：A 臂是否**自发**枚举输入域分段（不提示 bug 类型）。连续 2 格 GREEN → 覆盖面条款升级「已验证」；不 GREEN → 条款过拟合 timer.py，回炉。

### T3 · 长会话稀释床（cycle7-dilution，场景④）

- **设计**：20+ 轮任务，前 15 轮布置与条款无关的杂务（自然稀释注意力），第 15+ 轮植入触发点（如边界 bug 修复、完成声明时刻）；另跑同任务的短会话版作对照。
- **预注册看点**：A 臂长会话末段的条款触发率（覆盖面声明 / UNVERIFIED / 完成门）vs 短会话——量化「第 150 行条款的存活率」。
- **决策分支**：若稀释显著 → 候选对策：关键条款前重申（SessionStart hook 已有雏形）/ 关键决策点自动重锚 / 条款进一步下沉为脚本守卫。

## 优化线（随测试并行落地）

- **O1 · 批次密度回顾机制（对冲④）**：每累计 10 批做一次条款合并/降密评估——目标不是减条款，是减**常驻与按需 token 的规则密度**。先入 proposal，攒一个 RED（稀释证据）后升条款。
- **O2 · 轻通道边界微测（对冲①）**：预注册 4 个边界格（该升档没升 ×2、不该升乱升 ×2），测轻通道排除项①②③的判别力。首次给轻通道上一致性证据。
- **O3 · 成本账补墙钟与美元（对冲⑥）**：成本账从纯 token 扩为 token + 墙钟 + 费用三列，让「时间/成本敏感场景不值」成为可判断项而非感觉。
- **O4 · 创意任务成本条款候选（对冲②）**：鹈鹕 v5 方向已反转但 5 倍墙钟未解；若 T0 坐实「挤占」机制，与 T0 产出合并成一条「创意任务流程预算」候选条款，攒 RED 再立项（SB 准入纪律）。

## 执行顺序与终止

1. **立即**：T0（零成本）→ 出结案或候选条款。
2. **下次实验主场**：T1 + T2 合并（同一隔离环境，4–6 格对话）。
3. **其后**：T3 单独一轮；O1–O4 按各自治息点插入。
4. **总终止条件**：六类场景全部有「实测/条款/结案」三态之一，无悬空推演。
5. **纪律**：所有新实验对话卡用 v3（第一段原文写死）；隔离/恢复步骤预注册；判分仍由 lead 亲跑磁盘真值；n=1 结论只做方向性，不外推。

---

## English abstract

Plan covering six negative-gain scenarios (trivial-task overhead, creative suppression, discipline-as-ritual false confirmation, long-session rule dilution, rule/skill conflicts, latency-cost sensitivity). Test track: T0 free post-mortem of bed-2 loss; T1 clean-control experiment with preregistered user-skill isolation protocol (resolves W1); T2 heterogeneous-bug bed to replicate the coverage clause's GREEN and test generalization; T3 long-session dilution bed quantifying clause survival at round 15+. Optimization track: batch-density review every 10 batches, light-channel boundary micro-tests, cost ledger extended to wall-clock/currency, creative-task process-budget candidate clause. Termination when every scenario has a tested/clause/closed state.
