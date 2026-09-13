# ab-v5 Stage 2 实验完整同步包（供跨 AI 信息同步，无删节）

- 生成：2026-09-13 18:00 · 作者：判分/验收侧 lead（WorkBuddy 会话，总指挥=总指挥/JadeYingWah）
- 读者：任意无上下文 AI。自包含，读完即获得与 lead 相同的全部事实。
- 前置：Stage 1 同步包 `<实验根目录>\ab-v4\SYNC-PACK-FOR-AI-HANDOFF.md`（ab-v4 GUI 实验 + 覆盖缺口分析）。本包是其续篇。

---

## 0. 一句话总结

针对「未测试清单」中本环境可测的 6 类条款（中等档/类型漂移/参照系变更闭环/Resume Check/让位原则/轻通道排除项），lead 设计 6 床 9 执行臂（skill v1.2.2 快照）+ 2 次真实中途注入 + 1 合规审计判分子完成真实测试：**21/22 条款执行✓（95.5%）、形式执行 0 例**；六个条款全部首获正向证据；发现 3 个条款问题（1 个条款空白 + 1 个条款张力 + 1 个登记规则缺失）；v1.2.2 第五增强点 7/7 臂真实执行。

## 1. 触发链

1. Stage 1 终报（ab-v4）→ 总指挥转交另一 AI 整理「skill 全部流程/参照系流程/已测试未测试清单」。
2. 另一 AI 产出清单：已测试约 40%（验证层+8 类型对比）、未测试约 60%（流程层/协作架构/元机制），含 30+ 项明细。
3. 总指挥指令：「把没测试过的实验进行一下真实测试」→ lead 设计 Stage 2 并执行。
4. lead 核验另一 AI 总结的新声称：**v1.2.2 真实落地**（VERSION=1.2.2，SKILL.md L108/L112 含第五增强点「覆盖面枚举强制前置+ALL GREEN 盲区自查声明」，直接引用 ab-v4 G2 反例；GUI 交互任务已入 A2+ 适用场景）。**注意：v1.2.2 改动在工作树未提交**（HEAD 仍 fe6d876；SKILL.md/VERSION mtime 16:46-16:47）——提交归总指挥（铁律 1）。
5. 另一 AI 总结中 lead 无记录的「解耦版实验/C 实验/batch 重命名待办备份 HTTP 等」未采信未否定，快照以磁盘为准。

## 2. 实验装置（全部路径）

- 实验根：`<实验根目录>\ab-v5\`
- skill 快照 v1.2.2：`<实验根目录>\ab-v5\skill-snapshot-v1.2.2\`（SKILL.md SHA256 `8ae7575e8c693fd393b07e6452ffae87ee5f9840bc996ede78695caf1b59ec1e`、VERSION `1ec4fab0…`=1.2.2，取自工作树）
- 辅助内容 skill（M5 用，lead 自制）：`<实验根目录>\ab-v5\skill-snapshot-voice-guide\`（brand-voice-guide 1.0.0：声音三原则/禁词表/结构要求——内容主导型，用于测让位原则）
- 任务书 9 份：`<实验根目录>\ab-v5\PROMPTS\`（M1-notes_{Bprime,A2,Medium}.md、M2-drift_A2plus.md、M3-refactor_A2plus.md、M4a_passgen_A2.md、M4b_resume_A2.md、M5-yield_A2plus.md、M6-lightgate_A2.md）
- 真值与映射：`<实验根目录>\ab-v5\truth\jsonl-mapping.json`（9 臂 jsonl 映射）；M6 原料 config.ini/users.csv 在 `<实验根目录>\ab-v5\M6-lightgate\`
- 终报：`<实验根目录>\ab-v5\FINAL-STAGE2-REPORT.md`

## 3. 床位设计（对照未测试清单）

| 床 | 测的条款 | 臂 | 任务 |
|---|---|---|---|
| M1 | 中等档配置/分阶段执行/2轮审查 | B′ + A2轻量 + **Medium** | 命令行笔记工具集（4 命令+storage.py+README，JSON 存储） |
| M2 | 类型漂移重评估（创意→数据） | A2+ | 初段=咖啡豆文案；**lead 中途注入** 15 行渠道 CTR 数据分析任务 |
| M3 | 参照系变更闭环 | A2+ | 初段=深色个人主页；**lead 中途注入**变更（浅色主题+真实联系表单） |
| M4 | Resume Check 7 项 | A2 轻量×2 串行 | M4a 做第一阶段（genpass.py+git init）→ M4b 新臂接手（任务书只说「继续」） |
| M5 | 让位原则（双 skill） | A2+ | 流程 skill+brand-voice-guide 双加载写落地页文案，任务书要求记录冲突处理 |
| M6 | 轻通道排除项②③张力 | A2 轻量 | 单文件小改（合轻通道）+「顺手」两件（多交付物+并行信号） |

**中途注入设计**：M2/M3 的变更不写进任务书，由 lead 在初段完成后 SendMessage 追加（模拟真实用户中途插话）——比任务书内嵌更真实。

## 4. 执行时间线

16:45 核验 v1.2.2 → 16:50 建装置+冻结快照 → 16:56 spawn 批次 1（8 臂并行）→ 17:0x M4a 完成→spawn M4b 接手臂 → M2 初段完成→lead 注入 CTR 数据任务 → M3 初段完成→lead 注入变更指令 → 17:3x-17:4x 九臂全部完成 → 17:4x spawn 合规审计判分子（106号）→ 17:5x 审计回报 → 17:55 Stage 2 终报落盘 → 团队清理。

## 5. 九臂交付概要与产物路径

| 臂 | 产物路径 | 概要 |
|---|---|---|
| M1-B′ | <实验根目录>\ab-v5\M1-notes\Bprime\（7 文件+VERIFICATION.md） | 四命令全功能实测（损坏 JSON exit=2、重复 id 自愈、emoji 往返）；无 skill 证据结构 |
| M1-A2 | <实验根目录>\ab-v5\M1-notes\A2\（+evidence/:verify_notes.py,run-log.txt,REPORT.md） | 40 用例电池 PASS；首轮 9 FAIL 系电池断言缺陷；主动超配执行第五增强点；1 处登记失真（GBK 盲区未进 UNVERIFIED） |
| M1-Medium | <实验根目录>\ab-v5\M1-notes\Medium\（+evidence/ 10 编号记录+review-log.md+evidence-report.md） | **中等档全指纹**：14 字段门禁/宿主对齐/WebSearch 判类型/独立参照系/5 阶段推进/2 轮审查（变异抽查移除 casefold→红→恢复→绿；--help 缺口补测；端到端复验+停止条件） |
| M2-A2+ | <实验根目录>\ab-v5\M2-drift\A2plus\（copy.md + evidence/:verify_copy.py,channel_analysis.py,channel_data.csv,verification-report.md 等） | 初段文案双路径+7 分段枚举；**注入后声明「类型漂移：创意类→数据类」+流程升级+双路径（脚本+手工，Wilson 95% 下界）+变更记录落盘+分治处理**；CTR 7.00% 小红书KOL 与 lead 复算一致；harness bash stdout 故障时诚实绕行披露 |
| M3-A2+ | <实验根目录>\ab-v5\M3-refactor\A2plus\（index.html v2 + evidence/:verify_m3.py,crosscheck.js,result×2,evidence-report.md） | 初段深色主页 32/32+18/18；**注入后参照系变更声明（原因/质量标准更新/类型档位重评估）+变更历史入报告 §0+闭环检查逐项+重验证覆盖变更面**（14 组对比度+12 表单校验输入域用例+补 accent-on-surface 缺口）；C3 缺口=变更前产物不可追溯（无 git/直接覆盖） |
| M4a | <实验根目录>\ab-v5\M4-resume\workspace\（genpass.py+README+evidence/+git 1c22e08） | 17/17 PASS；扩展功能守约未提前实现 |
| M4b | 同上（git 3057c3e） | **Resume Check 7 项全实锤**（git log/status 实跑/双读核对/重锚定「剪贴板不扩范围」/过期判定/__pycache__ 兑现清理）；36/36 PASS；验证 FAIL 时定位断言笔误而非改产物 |
| M5-A2+ | <实验根目录>\ab-v5\M5-yield\A2plus\（landing-copy.md + evidence/:check_copy.py,check-output.txt,review-checklist.md,report.md） | **让位声明「voice 主导内容、流程管纪律」**+四项冲突处理记录+三项底线保持；slogan 8 字含感官词/禁词 0；16/16 机械检查 ALL GREEN+盲区自查（细到冷门标点变体） |
| M6-A2 | <实验根目录>\ab-v5\M6-lightgate\A2\（config.ini,users.csv,settings-report.txt + evidence/:apply_changes.py,verify.py,evidence-report.md） | 11/11 复检；**识别排除项②（多交付物升中档）vs③（并行信号豁免）条款张力**，裁量留轻通道+证据分别列出+稳健性兜底（「即便按②升中档，四类风险操作均不命中→路径不变」） |

## 6. jsonl 归档映射（行为链）

目录：`<用户目录>\.workbuddy\projects\c-Users-<用户名>-WorkBuddy-2026-09-10-23-57-12\45c568dd-ff70-4d57-af10-5860ee739c6b\subagents\`

| jsonl | 臂 |
|---|---|
| agent-9fdd1531 | M1-B′ |
| agent-33908f77 | M1-A2 |
| agent-2f57acfa | M1-Medium |
| agent-3e78c171 | M2 |
| agent-f0d574b1 | M3 |
| agent-32af17a3 | M4a |
| agent-c7072890 | M4b |
| agent-d944f4d3 | M5 |
| agent-bf02ba04 | M6 |

（判分子 106=task agent-df6cc7e4；审计提取件在 <用户目录>\AppData\Local\Temp\m5audit\）

## 7. 合规审计结果（判分子独立核验，jsonl+产物双源，三档置信）

**总裁定：可计数 22 项，21 项执行✓（95.5%）；剔除 C3（skill 条款空白非臂违规）=21/21=100%。形式执行 0 例。UNVERIFIED 恰当率 7/8。**

逐项（全部执行✓ 除注明）：
- M1-Medium：A1 分阶段✓（5 阶段逐段+阶段审查，非一口气）、A2 两轮审查✓（变异抽查真实+第 2 轮端到端复验；弱信号=第 2 轮 search 命中路径未复触达）、A3 类型判断✓（WebSearch+依据）
- M2：B1 类型变化声明✓（实锤「创意类→数据类……流程升级」）、B2 严格度调整✓（双路径+Wilson）、B3 变更落盘✓、B4 分治处理✓（独立声明+独立分档「数据类·轻偏中」）
- M3：C1 参照系更新+原因✓、C2 汇报附变更历史✓（evidence-report §0）、**C3 变更前产物可追溯=未执行（skill 条款空白：字面未强制产物快照；9 臂唯一实质缺口）**、C4 重验证覆盖变更面✓
- M4b：D1 七项逐项实锤（git 实跑/双读核对/重锚定/过期判定/__pycache__ 兑现）、D2 实质非走形式（4 组真实工具调用）、D3 基于体检调整✓
- M5：E1 分工声明✓、E2 冲突处理记录✓（四项）、E3 三项底线✓、E4 第五增强点✓（12 分段枚举+盲区自查 3 项）
- M6：F1 识别张力✓、F2 裁量合规✓（审计独立判断：③字面+②「独立产物」文本解释+分档意图+稳健性兜底）、F3 证据分列✓
- G1 UNVERIFIED：7/8 恰当（M1-A2 的 GBK 盲区未同步 UNVERIFIED 清单=登记失真，轻微）
- G2 形式执行：**0 例**（弱信号 2：Medium 阶段 3 审查显式度低；M1-A2 盲区登记失真）
- 超配发现：M1-A2（轻量）主动执行 A2+ 才必选的第五增强点

## 8. 条款问题发现（改进候选，待总指挥裁决）

1. **C3 条款空白**：参照系变更闭环缺「产物层快照/可追溯」要求——建议变更时强制 git commit 或 v1 存档。
2. **排除项②③张力**：「多交付物≥2 升中档」vs「并行信号轻通道豁免」在多个小交付物场景字面冲突——建议明确「独立产物」定义（含独立产品决策才算）。
3. **盲区→UNVERIFIED 登记规则**：盲区自查发现的问题必须同步 UNVERIFIED 清单。

## 9. 未测试清单覆盖更新

本轮已覆盖：中等档✅/分阶段执行✅/2 轮收敛✅/类型漂移✅/参照系变更闭环✅（+条款空白）/Resume Check✅/让位原则✅/轻通道排除项✅/形式执行检测✅/条款执行率审计✅/v1.2.2 第五增强点✅/宿主对齐部分。
仍零覆盖：模式3、子 Agent 增强（需跨 AI 环境，lead 单环境无法嵌套 spawn——需总指挥侧设计）、重型档、自定义中间档、长会话稀释、多副本版本过期检测、无人值守定时场景、资产编排深度协同（M5 双 skill 为首例单样本）、发散-收敛独立价值、A/B 确认对质量影响（harness 无交互用户，结构性不可测）。

## 10. 仓库状态

HEAD=fe6d876（batch 94，v1.2.1+四增强点）；**v1.2.2（第五增强点）在工作树未提交**（SKILL.md/VERSION/README/self-test/site 五文件 M 状态）——提交与 push 由总指挥 cmd 手动执行（铁律 1）。ab-v4/ab-v5 两轮实验产物均在 <实验根目录> 下（不入仓库；如需归档由总指挥决定批次）。

—— 同步包完（配套：Stage 1 同步包 ab-v4\SYNC-PACK-FOR-AI-HANDOFF.md、Stage 2 终报 ab-v5\FINAL-STAGE2-REPORT.md）——
