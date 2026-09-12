# A/B cycle5-clean · 干净对照实验报告（T1+T2 合并轮）

- **日期**：2026-09-12
- **模型**：Hy3（六格同模型，任务原文双臂逐字同文）
- **协议**：`E:\Harness\cycle5-clean\PROTOCOL.md`（W11 修订版）；工作区 `Desktop\A6\Skills_*` 六格，lead 预建并逐格 md5 验收
- **判分**：lead 亲跑磁盘真值（import 协议用例）+ 六格 jsonl 行为链逐格提取；不采信被测自述。判分板：`E:\Harness\cycle5-clean\scoreboard-cycle5.md`

## 一、实验目的

1. **T1 裸差**：隔离宿主 skill 生态后，第一次测出本 skill 相对**裸模型**的真实增量（消除 cycle4 的 W1 对照臂污染）。
2. **T2 复现**：异构 bug 床（next_date.py 闰年边界）复现覆盖面条款 GREEN——A 臂是否自发枚举输入域分段。

## 二、六格行为链与成本（面板 + jsonl 时间戳）

| 格 | 臂/床 | 行为链摘要 | 工具调用 | 墙钟 | 上下文% | Conv |
|---|---|---|---|---|---|---|
| B1 | B·床1 | 读产物 → **自行调用 `Skill: verification-sensitivity-audit`** → 变异杀伤 + 无头 Chrome 真渲染 → 抓到 -27 与 3 条死守卫 → 修复后重跑杀伤 3/3 | 31 | 17.1min | 59.1% | ~55.3K |
| A1 | A·床1 | 加载 skill → 对齐两停等「可」→ 独立重算 + F6 变异 + 真渲染 → 抓到同组缺陷 → 修复 + 复跑闭环 + 标 UNVERIFIED 残留 | 23 | 16.2min | 58.9% | ~48.1K |
| B3 | B·床3 | 读码 → 一处 Edit → 7 例 eyeball 循环（含 3661） | 3 | **0.7min** | 20.5% | ~2.3K |
| A3 | A·床3 | 对齐两停 → 读码 → 一处 Edit → **10 例电池带期望值断言** + CLI 冒烟 | 11 | **8.6min** | 30.5% | ~14.2K |
| B4 | B·床4 | 读码 → 一处 Edit → 9 例边界循环（含 2024-02-29、2020/1900/2000 世纪闰年） | 3 | **0.7min** | 20.8% | ~2.7K |
| A4 | A·床4 | 对齐两停 → 读码 → 两处 Edit → **9 例电池逐段注释**（闰年/平年/月末/年末/世纪闰年400/非闰世纪100）+ CLI 测试 | 16 | **7.2min** | 28.4% | ~13.0K |

A 臂额外治理产物：`docs/agents/host-alignment.md` ×2、`.workbuddy/memory/` ×3（其中两格在收到任务前写入）。

## 三、lead 亲跑真值与 M4 计分

- 床3（3661/7200/86399/60/59/0）：B3 **6/6**、A3 **6/6**（两格修复产物 md5 相同，同改 `datetime` 标准库）。
- 床4（2024-02-28/2000-02-28/2023-02-28/2024-12-31/2024-04-30）：B4 **5/5**、A4 **5/5**（同改 `datetime`，独立成稿）。
- M4（RED 3 + 修复 3 + 对等 2 = 8）：**四格均 5/8**——修复正确 3 + 声称-产物对等 2，**RED 全丢**（四格都是读码即定位直接改，无人先跑坏版本复现；Hy3 行为特征，与前测模型的执行式 RED 不同）。

## 四、床1（F6）：双臂皆 T3，但 B1 不裸——W12 判污染格

- **B1 在 FC#2 调用了 `Skill: verification-sensitivity-audit`**。该 skill 住 `C:\Users\yutia\.workbuddy\skills\`（宿主用户级 skill 路径），**不在本次隔离范围**（只搬了 `~/.agents/skills`）。佐证：B1 面板 Skills≈5.6K vs B3/B4 3.6K。
- 因此「干净环境 B 臂还能否 T3」**本轮不可测**，床1 裸差悬置。cycle4 的结论（B 臂有 audit skill 助阵仍输在声称-产物对等）保持不变。
- A1 全程 T3：独立重算（462 vs 435）→ 变异杀伤（金额类 0%）→ 真渲染抓自检装置自身 11/12 → 修复 → 复跑杀伤 100% → **标注 UNVERIFIED 残留**（跨源账单核对、打印实测）。质量与 B1 相当，方法归属明确。

## 五、T2 判定：覆盖面条款升级「已验证」

- **A4 自发枚举输入域分段 = YES**：电池 9 例逐段注释——闰年 2/28、平年 2/28 进位、闰年 2/29 进位、年末、31 天月、30 天月、普通日、世纪闰年(400)、非闰世纪(100)。GREEN 判据达成。
- 与 cycle4-A5 合计**连续 2 格 GREEN → 第五十六批「测试电池覆盖面声明」条款升级「已验证」**（仍 n=2、判分为作者；升级指的是证据等级，不是真理等级）。
- **诚实注记**：B4 裸电池也覆盖闰年段且含 1900/2000 世纪用例（9 例），覆盖广度与 A4 相当。A4 的真实增量在**期望值断言**（机械报 FAIL，不靠肉眼比对输出）与**分段标注**（声称-证据对等可核），不在覆盖发现力。Hy3 裸基线在异构 bug 床上已很强。

## 六、裸差判定与成本

- 床3 裸差 **0**（5/8 vs 5/8）；床4 裸差 **0**（5/8 vs 5/8）；床1 不可测（W12 污染）。**无负轴 → 不触发条款降密**。
- 成本：床3/床4 A 臂 Conversation **+10~12K**（约 5-6 倍）、墙钟 +6.5~8min、工具调用 3→11/16，含两轮对齐停等与治理仪式产物。与 cycle3+4 合并口径（+14~21K）同向，本次略低于区间下沿（任务更轻）。
- **负增益场景①（简单任务纯开销）在 Hy3 上再次实证**：裸修复全对且快，skill 增量只剩断言化 + 文档化。

## 七、W12 · 隔离协议路径盲区（本轮新增教训）

`~/.agents/skills` 隔离 ≠ 全生态隔离。宿主 skill 至少还有两处来源：`~/.workbuddy/skills/`（用户级）与内置插件 skill。B1 恰好触发验证类 skill，床1 裸对照再次失效。**修正**：下轮隔离须同时搬 `~/.workbuddy/skills`，或选用无宿主 skill 的环境；隔离后用一次性对话盘点两臂可见 skill 清单并截图。

## 八、对齐阻塞发现（第六十四批条款来源）

A 臂加载后**两停等「可」**（加载证明后一停、对齐声明后一停），A1 更宣布「实现类任务→确认前不落盘」。SKILL.md 宿主对齐条款原文「交用户确认后本次会话生效」是直接根因——对齐成了收费站。本轮 A 臂 +6.5~8min 墙钟中相当部分是纯等待。第六十四批落地两条修正：**对齐不阻塞**（声明输出即生效、事后可改、未证实能力按保守假设标 UNVERIFIED）与**门禁换挂点**（确认门禁只挂破坏性/外部/不可逆/多代理派发四类风险操作；宿主有机器级权限兜底时中档降级为事前一行声明+事后证据报告；边界情形默认询问）。**方法学修正**：今后 A 臂实验卡不得人为插「可」，由 AI 自主走完对齐，成本才是真实交互成本。

## 九、协议偏差留档

1. A 臂实际从 `E:\Skill管理\...` 仓库读取 SKILL.md/VERSION（非隔离安装副本）；SKILL.md md5 与安装副本一致（`3916dabc`），无实质影响。
2. 总指挥在床1 两格验收交付后发「可」触发修复轮（两格对称）；验收判级以修复前结论为准。
3. B1 的 `_audit/` 留下 Chrome profile 等运行时临时物于交付格内（B 臂无第五十五批条款约束所致，如实记档）。

## 十、结论

1. 覆盖面条款「已验证」升级（T2 达成）。
2. 床1 裸差问题因 W12 仍未测出；隔离协议修正后择机重跑（T1 未结案）。
3. Hy3 裸基线强：床3/床4 裸修全对且 0.7min；skill 价值面进一步收窄到验收/判分/多代理治理类任务与声称-证据对等。
4. 对齐阻塞是 skill 自伤源之一（场景①的机制层解释），已修（64 批）。

## EN Summary

cycle5-clean ran the first isolation-based bare comparison (3 beds × 2 arms × Hy3, six isolated cells, lead-judged). Protocol cases judge-run: both arms fixed bed-3/bed-4 bugs correctly (M4 5/8 each — all four cells skipped RED, reading code straight to fix). The T2 primary look succeeded: the A arm spontaneously enumerated input-domain segments on bed 4, giving the coverage clause its second consecutive GREEN — upgraded to "verified" (n=2, author-judged). Honest note: the bare battery covered leap segments equally well; the skill's real increment is expected-value assertions and labeled segments, not discovery. Bed 1 was again polluted — the B arm invoked `verification-sensitivity-audit` from the host user-level skill path (`~/.workbuddy/skills/`) that our isolation missed (W12); the bare comparison there remains unmeasured. Bare differences: 0 / 0 / unmeasurable; no negative axis, no clause downgrade. Cost: A arms +10–12K conversation tokens, +7 min wall clock, partly from a blocking alignment ritual — fixed in batch 64 with two clauses (alignment is non-blocking; the confirmation gate attaches only to destructive/external/irreversible/multi-agent operations, degrading to evidence reporting when the host already enforces machine-level permission prompts).
