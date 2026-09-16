# metacognition 实验系列·分析交接包（供另一个 AI 分析用）

- 生成：2026-09-13 23:35 · 作者：判分/验收侧 lead（总指挥）
- 目标读者：零上下文 AI。读完即可对本系列实验做独立分析。
- 本系列 = 三段连续实验：**v1.2.3 修订验证 → P1-1 三臂 n=3 → P1-2 红队/自我校准**

---

## 一、背景一句话

gpt-series-reasoning-style skill（流程纪律层，仓库 `<skill-repo>/自制skill\gpt-series-reasoning-style`，当前 v1.2.2 已发布，两个提交 b016a39/e691313 待 push）经过四轮 A/B 实验（cycle-2/Phase 0/Stage 1/Stage 2，见总包 `<workspace>/SYNC-PACK-UNIFIED-v2.md`）后，执行侧 AI 起草了 v1.2.3 三项修订并完成对照组，lead 接手完成实验组、三臂 n=3 对比与红队机制验证。

## 二、全部文件路径（按类别）

### 2.1 交接与分析文档
| 路径 | 内容 |
|---|---|
| experiments/ab-metacognition/HANDOFF-v1.2.3-EXPERIMENT.md | 执行侧交接文档（lead 已核验属实） |
| experiments/ab-metacognition/CAPABILITY-EFFECT-MAPPING.md | 能力-效果映射（批判性自我怀疑/指令遵循弥补最强⭐5、自我校准最弱⭐3） |
| experiments/ab-metacognition/v1.2.3-REVISION-DRAFT.md | 修订草案 6 项（3 高+3 中优先级） |
| experiments/ab-metacognition/V123-VERDICT-REPORT.md | v1.2.3 验证终报（暂缓实施） |
| experiments/ab-metacognition/P1-1-FINAL-REPORT.md | P1-1 三臂 n=3 终报 |
| experiments/ab-metacognition/P1-2-SELFCAL-ANALYSIS.md | P1-2 数据轨：自我校准缺口量化 |
| experiments/ab-metacognition/P1-2-REDTEAM-FINAL.md | P1-2 终报（两轨合并） |
| experiments/ab-metacognition/P1-3-DESIGN.md | P1-3 设计稿（待批复未执行） |

### 2.2 skill 快照（对等性已 diff 核验：SKILL.md 唯一实质差异=第 8 步 3 项修订，4 行）
| 路径 | 说明 |
|---|---|
| experiments/ab-metacognition/skill-snapshots\v1.2.3-draft\ | 完整仓库快照（11MB），SKILL.md `2024c669…`，VERSION=1.2.3-draft，L146 含修订全文（④反例验证必做 ⑤可复算性必做 覆盖面枚举所有配置必选） |
| experiments/ab-metacognition/skill-snapshots\v1.2.2-full\ | 对等完整快照，SKILL.md `8ae7575e…`，VERSION=1.2.2 |
| <workspace>/ab-v5\skill-snapshot-v1.2.2\ | 轻量快照（SKILL.md+VERSION） |

### 2.3 实验任务书
- experiments/ab-metacognition/v1.2.3-test\TASK.md（T1 CSV 解析器）
- experiments/ab-metacognition/P1-1\T2-todo\TASK-T2.md（T2 待办清单）
- experiments/ab-metacognition/P1-1\T3-md2html\TASK-T3.md（T3 Markdown→HTML）

### 2.4 执行产物（10 份，未匿名原件）
| 任务 | 无 skill | 原则引导 v1.2.2 | 硬指标 v1.2.3 |
|---|---|---|---|
| T1 CSV | experiments/ab-metacognition/v1.2.3-test\Bprime-baseline\ | experiments/ab-metacognition/v1.2.3-test\v1.2.2-rerun-lead\ | experiments/ab-metacognition/v1.2.3-test\v1.2.3-draft\ |
| T2 待办 | experiments/ab-metacognition/P1-1\T2-todo\noskill\ | experiments/ab-metacognition/P1-1\T2-todo\principled\ | experiments/ab-metacognition/P1-1\T2-todo\hardmetric\ |
| T3 md2html | experiments/ab-metacognition/P1-1\T3-md2html\noskill\ | experiments/ab-metacognition/P1-1\T3-md2html\principled\ | experiments/ab-metacognition/P1-1\T3-md2html\hardmetric\ |
| T1 原对照（执行侧 AI 子智能体） | — | experiments/ab-metacognition/v1.2.3-test\v1.2.2\ | — |

### 2.5 匿名样本（盲评用，映射表在旁）
- v1.2.3-test\submission-{22,34,47,89}\ + truth-blind-mapping.json（22=原对照/34=draft/47=B′/89=rerun，seed=20260913）
- P1-1\blind\T2-todo\submission-{22,89,34}\、P1-1\blind\T3-md2html\submission-{39,57,58}\ + P1-1\blind\truth-mapping.json（各组 22=无skill/89或57=原则/34或58=硬指标）

### 2.6 红队轨
- 目标副本：P1-1\redteam\target-A\（=T1-22 的 csv_parser.py，含**静默数据损坏** bug）、target-B\（=T1-89 的，含 CLI 编码崩溃 bug）+ 各 TASK-ORIGINAL.md
- 红队工作件：P1-1\redteam\work-A\（120 对 target-B 的审查）、work-A2\（120 对 target-A）、work-B\（121 对 target-B）
- 注：120 号曾目标错位（先审了 target-B），后经追加任务完成 target-A——两红队先后审同一目标发现高度一致（审查者可靠性正面数据）

### 2.7 jsonl 行为链（执行者与判分者全部留痕）
目录前缀：`%USERPROFILE%\.workbuddy\projects\c-Users-<user>-WorkBuddy-2026-09-10-23-57-12\45c568dd-ff70-4d57-af10-5860ee739c6b\subagents\`
| jsonl | 身份 |
|---|---|
| agent-f7898d1c | T1 v1.2.2-rerun 臂（token 1,075,604/15.0min） |
| agent-ae69c877 | T1 v1.2.3-draft 臂（775,437/9.0min） |
| agent-1a343c27 | T1 无 skill B′ 臂 |
| agent-f63bdec2 / agent-2ceaa991 / agent-dab450da | T2 无skill / 原则 / 硬指标 |
| agent-a5bb95cc / agent-926e5125 / agent-3b464214 | T3 无skill / 原则 / 硬指标 |
| agent-98709950 | 判分子 109 号（T1 三份首轮，44 项探针作者） |
| agent-b041a425 | 判分子 118 号（T1 四份复判，44 项复用） |
| agent-1b1ba9b5 | 判分子 119 号（全部 10 份锚点 rubric 终判） |
| agent-58636ca3 / agent-980aa8c6 | 红队 120 / 121 |

### 2.8 判分探针与副本（复核用）
- %LOCALAPPDATA%\Local\Temp\csvjudge\（109 号：probe.py/probe2.py=44 项探测+copy22/34/89 副本）
- %LOCALAPPDATA%\Local\Temp\csvjudge2\（118 号：JUDGE_REPORT_118.md+副本）
- %LOCALAPPDATA%\Local\Temp\judge9\（119 号：T1 probe 结果 4 份 + T2\probe_todo.py 36 项 + T3\probe_md.py 40 项 + r* 复算副本）

## 三、实验结果总结（全部有磁盘/探针证据）

### 3.1 v1.2.3 验证（T1 单任务，双组同执行者+原对照）
盲评（109 号）：89=44 > 22=36.5 > 34=34.5。复判（118 号同探针）：47(B′)=45.0 > 34=42.5 > 89=41.5 > 22=40.0。
**发现：判分者方差 9.5 分 > 执行者方差 7.5 分 > 版本差——44 项客观探测两判分子逐份完全一致，分歧全在主观权重。**

### 3.2 P1-1 三臂 n=3（锚点 rubric：基础 50−客观扣分+主观两项）
| 条件 | T1 | T2 | T3 | 均值 | vs 无skill |
|---|---|---|---|---|---|
| 原则引导 v1.2.2 | 56.5 | 59.0 | 59.0 | **58.17** | **+2.83** |
| 硬指标 v1.2.3 | 54.0 | 59.5 | 57.5 | **57.00** | **+1.67** |
| 无 skill | 56.5 | 56.5 | 53.0 | **55.33** | — |
- 原则 vs 硬指标 +1.17（判分误差内等效）→ **v1.2.3 终局：不实施硬指标化**（原则引导下反例执行率已 4/4=100%）
- skill 有效性正向成立（两版本均 > 无 skill）；T1 精确任务无 skill 并列第一（任务开放度规律第三次确认）

### 3.3 P1-2 自我校准缺口（10 份量化）
- 缺口率（独立探测发现而执行者未自报）：**无 skill 4/4=100%（幅度最重）vs skill 条件 1/3=33%**
- skill 改善的是「知道自己哪里可能错」而非「不产生 bug」
- 恒真断言（T2 原对照组 verify.py:249 对两种行为都为真）=「全绿但不鉴别」教科书样本

### 3.4 P1-2 红队轨（黑盒审查 vs 有报告判分子）
| 目标 | 红队发现 | 有报告判分子 |
|---|---|---|
| target-A（T1-22） | 3 根因：EOL 静默数据损坏（L153，newline="" 修复）/目录参数崩溃/GBK 崩溃 | 2 根因 |
| target-B（T1-89） | GBK 崩溃（L143）+ parse 非 CSV 类型体验问题 | 1 根因 |
- **红队发现 ≥ 有报告判分子（各多 1 项）**：证据报告无锚定效应、也非必要地图
- 红队自发深度：6 万/12 万轮 fuzz 对比 stdlib——**静默数据损坏靠此法发现，常规断言无效**
- 红队自发自发变异（T1 B′ 4/4）与未做（T2/T3 无 skill 未做）并存：skill 条件下反例执行率 4/4 vs 无 skill 1/3

### 3.5 判分子跨组观察（119 号 7 条）
①Windows 控制台编码=最高频崩溃源（10 份中 4 份，仅 3 份显式处理）②第一名共性=声明完备而非通过率 ③静默数据改写是最贵缺陷（4 例 3 例自测全绿）④声明与实现矛盾同方向 3 例 ⑤可复算性 10/10 健康 ⑥变异全有全真实，梯度在过程留痕 ⑦规模与质量弱相关

### 3.6 方法学发现（三条铁律，已沉淀技能）
1. **执行者方差（7.5 分）> 版本差** → A/B 必须同执行者双组重跑
2. **判分者方差（9.5 分）> 版本差** → 单判分子 + 锚点 rubric（崩溃 −1.5/数据损坏 −2.5/错误结果 −1.0/声明矛盾 −1.0/未声明盲区 −0.5/不可复算 −2.0/缺反例 −1.5；主观仅两项各 0-5）
3. **盲区带随机性** → 独立探测用例数须远超交付方自测（44 探测 vs 96/85/29 自测）

## 四、交给另一个 AI 的分析任务（建议）

1. **独立复核**：抽查任一 submission 的判分（探针脚本在 Temp\judge9\ 可直接跑），验证 lead 判分的可复算性
2. **数据再分析**：基于 3.2 表做统计检验（n=3 样本小，可评估效应量与置信区间）
3. **跨系列综合**：结合总包 `<workspace>/SYNC-PACK-UNIFIED-v2.md`（四轮 A/B 完整结果）写 skill 价值综合报告——特别是「单文件任务 skill 无增益 vs 多文件/开放任务有增益」的边界条件
4. **v1.2.3 裁决辅助**：基于 3.2/3.4 评估「不实施硬指标化」判定是否需要修正（当前判定：等效，不实施）
5. **能力-效果映射校准**：对照 CAPABILITY-EFFECT-MAPPING.md 的 ⭐ 评级与实测数据（如「自我校准最弱⭐3」vs 实测缺口率 skill 33% vs 无 skill 100%）
6. **P1-3 设计评审**：评审 experiments/ab-metacognition/P1-3-DESIGN.md（档位效率曲线设计）的判据框架是否完善

## 五、注意事项

1. 本系列所有产物均为只读分析对象——复算请在副本进行（判分子曾原位复跑覆盖过一份 test_report.txt，已恢复）
2. v1.2.3-draft 快照含 .git 残留（分析时无需读；执行实验时须边界禁读）
3. Temp 下判分工作件可能被系统清理——核心数据已全部在本包所列 <workspace>/ 路径
4. 仓库 v1.2.2 两提交（b016a39/e691313）待 push（铁律 1：总指挥 cmd 手动）
5. 另一 AI 的「解耦版/C 实验」等历史数字 lead 未核验，引用需自行验证

—— 分析交接包完 ——
