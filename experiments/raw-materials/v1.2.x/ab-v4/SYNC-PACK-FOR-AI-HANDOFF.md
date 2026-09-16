# ab-v4 Stage 1 实验完整同步包（供跨 AI 信息同步，无删节）

- 生成：2026-09-13 16:35 · 作者：判分/验收侧 lead（WorkBuddy 会话，总指挥=总指挥）
- 读者：任意无上下文 AI。本文自包含，读完即获得与 lead 相同的全部事实。
- 项目：gpt-series-reasoning-style skill（仓库 <skill安装目录> <owner>/gpt-series-reasoning-style，当前 HEAD fe6d876）

---

## 0. 一句话总结

为验证「SKILL.md 从未被测试证明过的条款」（覆盖缺口分析 18 项），lead 经总指挥授权 spawn 13 个执行臂（3 GUI 任务×3 臂 + 时序任务×4 变体）+ 4 个盲评判分子完成全链路实验；结论：GUI 任务打破 cycle-2 的 NULL 结果（G1/G3 剂量效应 A2+>A2>B′）、G2 出现首例 A2+ 反面样本（多路径≠覆盖面）、保守度调节两分支按设计工作（precision 9 倍提升/全量分支 recall 保持）、实操闭环底线条款首获正向证据。

## 1. 背景文件链（按时间序）

| 文件 | 内容 |
|---|---|
| <实验根目录>\ab-v3\phase0\PHASE0-REPORT.md | Phase 0 九臂（A1/A2/B′×D1红酒/D2咖啡/D3时序）定稿报告：总均分 A2 90.3 > A1 87.6 > B′ 76.2；D1 三臂客观全对盲评 B′ 第一；D3 A2 recall 0.75/precision 1.00（区间3）、A1 0.75/0.17（18区间）、B′ 0/0 |
| <实验根目录>\ab-v3\phase0\A2PLUS-PILOT-VERIFY-2026-09-13.md | A2+ 先锋测试独立核验：D1 A2+ 5/5 声称磁盘证实（3路径/1000置换/10000Bootstrap/evidence 7文件/保守度8+3分流）；D2/D3 A2+ 零产物（空 evidence/），D3「11区间/3方法/EWMA」全盘搜索无实物=不可引用；4 项实验卫生瑕疵 |
| <skill安装目录> | 条款×证据覆盖缺口分析：18 项 D 档零覆盖（实操闭环正向路径、模式3、中等档、类型漂移、参照系变更闭环、Resume Check、子Agent、资产编排、搜索判类型、宿主对齐、文件整理、保守度全量分支、中断保护、中间档、轻通道排除项、2轮收敛、让位原则、发散收敛）+ 5 类型 B 档（研究/绘画/建模/冒险/复合仅 batch83-88 旧证据）+ 2 个元发现（cycle-2 交付 A=B NULL 结果；从未测「条款执行率」） |
| <skill安装目录> | 补测派发计划：P-A 底线 GUI 验证（9）/P-B A2+ 补测（4）/P-C 中等档+漂移（4）/P-D 五类型复证（15）/P-E 条款执行率审计（0执行）；装置前提 G1 消融臂/G2 判分尺度/G3 样本量 |
| <实验根目录>\ab-cycle2\_judge\FINAL-REPORT.md | cycle-2 定稿报告（12对24臂）：A 94 vs B 89，交付质量 A=B 无可测优势，A 臂证据链系统性更重但被 0-2 尺度天花板+成本噪声双向遮蔽；V-02 判分事故（evidence/ 子目录漏盘）已勘误 |

## 2. ab-v4 实验装置（全部路径）

### 2.1 根与快照
- 实验根：`<实验根目录>\ab-v4\`
- 装置说明：`<实验根目录>\ab-v4\README.md`
- skill 快照：`<实验根目录>\ab-v4\skill-snapshot-v1.2.1\SKILL.md`（SHA256 `bf57729b90e7af1748756f3de8ac5c826e16450ed7925751890960fd3f6cd40e`）+ `VERSION`（`d7c5f05b…`，=1.2.1，含 fe6d876 的 A2+ 四条款：①多路径交叉验证≥2种独立方法 ②验证证据必须入 evidence/ ③质量标准可检查化 ④保守度调节——主报告取最保守结果/安全监控场景用全量报告分支）

### 2.2 预注册任务书（13 份，`<实验根目录>\ab-v4\PROMPTS\`，SHA256 清单=`<实验根目录>\ab-v4\truth\prompts-sha256.txt`）
- G1-calculator_Bprime.md / G1-calculator_A2.md / G1-calculator_A2plus.md
- G2-formvalidator_Bprime.md / G2-formvalidator_A2.md / G2-formvalidator_A2plus.md
- G3-dashboard_Bprime.md / G3-dashboard_A2.md / G3-dashboard_A2plus.md
- P-B_D3-conservative.md / P-B_D3-noconstraint.md / P-B_D3-fullreport.md / P-B_D3-interrupt.md

任务要点：G1 单页计算器（四则/小数/C/退格/等号/键盘）；G2 表单校验（email/phone/密码≥8位含字母数字、失焦+提交双校验、空值/格式错/超长/特殊字符明确反馈）；G3 静态看板（12月内联数据/3指标卡/SVG趋势图/季度筛选同步、禁 CDN）；P-B 四臂均做 nab_machine_temp.csv（22695行）异常检测，差异仅在 A2+ 配置：conservative=保守度调节（主报告取最保守方法）、noconstraint=不启用保守度（合并全报）、fullreport=安全监控场景全量报告分支（宁可错报不漏报）、interrupt=保守度+分段落盘要求（中断场景臂）。

### 2.3 真值与判分装置（`<实验根目录>\ab-v4\truth\`）
- nab_combined_labels.json（NAB 官方标注拷贝，machine_temperature 4 点：2013-12-11 06:00 / 2013-12-16 17:25 / 2014-01-28 13:55 / 2014-02-08 14:30，容差 ±60min，与 Phase 0 预注册一致）
- objective_d3_check.py（自动比对脚本，含 >7d 元数据行过滤修复）+ objective_d3_auto.json（宽松解析预检结果）
- blind-mapping.json（匿名化映射，random.seed=20260913 可复现）
- jsonl-mapping.json（13 个 jsonl→臂映射，配置特征句裁决）
- clause-audit-raw.json（条款执行率审计原始矩阵，13 臂×10 指标）
- prompts-sha256.txt（任务书冻结哈希）

### 2.4 匿名化盲测目录（判分子读的）
- <实验根目录>\ab-v4\blind\G1-calculator\submission-{22,89,34}
- <实验根目录>\ab-v4\blind\G2-formvalidator\submission-{39,57,58}
- <实验根目录>\ab-v4\blind\G3-dashboard\submission-{63,52,16}
- <实验根目录>\ab-v4\blind\P-B\submission-{56,60,36,79}

### 2.5 判分子产物（临时目录，可能已被清理）
- G1 判分子（91号）：<用户目录>\AppData\Local\Temp\g1judge\（my-judge.mjs/my-results.json）
- G2 判分子（92号）：<用户目录>\AppData\Local\Temp\g2judge\
- G3 判分子（93号）：<用户目录>\AppData\Local\Temp\g3judge\（report.md/s63.png/s52.png/s16.png/results.json/expected.json）
- D3 判分子（94号）：<用户目录>\AppData\Local\Temp\d3judge\

## 3. 执行时间线

- 15:14 预注册冻结 → 15:15 spawn 13 臂并行（独立 subagent，prompt 自包含）→ 15:17 用户取消 lead turn 致团队级中断（13 臂 paused，交付目录全空）→ 15:21 逐个 SendMessage 恢复（磁盘确认无覆盖风险）→ 16:05 前后 13 臂全部完成并汇报 → 16:06 匿名化 → 16:07 spawn 4 盲评判分子 → 16:25-16:35 盲评全部回报 → 16:35 解封汇总出报告。

## 4. 13 执行臂产物路径与交付概要

| 臂 | 产物路径 | 交付概要（执行臂自报 + lead 核实） |
|---|---|---|
| G1-Bprime | <实验根目录>\ab-v4\G1-calculator\Bprime\（index.html，1 文件） | 功能全对；node+DOM stub 测试 20 项（0.1+0.2=0.3 via toPrecision(12)）；真实浏览器 UNVERIFIED 如实标注 |
| G1-A2 | <实验根目录>\ab-v4\G1-calculator\A2\（index.html + evidence/:verify-cdp.mjs,verify-log.txt,REPORT.md,截图×2） | Node22+Edge headless CDP 47/47 PASS（19键全可达/键盘=鼠标逐态一致/控制台零报错）；首轮 5 FAIL 均系测试脚本缺陷，产物零改动 |
| G1-A2plus | <实验根目录>\ab-v4\G1-calculator\A2plus\（index.html + evidence/:oracle.py,test-core.mjs,test-browser.mjs,vectors.json,results×2,截图×5,report.md，共 11 文件） | 三路径：Chrome 实操 26/26 向量+Node 27/27 对 Python Fraction oracle+变异 5/5 杀伤；唯一实现真运算优先级（自建词法求值器 2+3×4=14）；UNVERIFIED 3 项精准 |
| G2-Bprime | <实验根目录>\ab-v4\G2-formvalidator\Bprime\（index.html） | node 语法检查+自查；无 evidence；a@b.c 单字符 TLD 放行（设计差异） |
| G2-A2 | <实验根目录>\ab-v4\G2-formvalidator\A2\（index.html + evidence/:report.md,extracted-script.js,截图×3） | JS 单测 38 断言+Playwright Chromium 20 断言+自发 17 用例变异测试杀伤率 100%；行为 30/30；punycode 侧写 1 漏洞（中文域名浏览器自动转 xn--）；首轮 26/27 失败诚实披露 |
| G2-A2plus | <实验根目录>\ab-v4\G2-formvalidator\A2plus\（index.html + evidence/:verify-logic.js/-result,verify-browser.js/-result,report.md,截图×2） | 浏览器 21 项 DOM 断言+CDP 控制台三通道零报错+Node 31 用例+变异 5/5；唯一一键重跑复现；**但中文 local/中文域名/双点域名/! 放行（任务书点名中文须拦截），电池未覆盖且未披露盲区** |
| G3-Bprime | <实验根目录>\ab-v4\G3-dashboard\Bprime\（index.html，8.4KB） | Chrome headless 真实加载+注入点击 Q4 实测；node 独立复算五口径；无 evidence 目录 |
| G3-A2 | <实验根目录>\ab-v4\G3-dashboard\A2\（index.html + evidence/:EVIDENCE.md,verify_data.py,cdp_verify.js,cdp_result.json,初始DOM,截图×2，共 9 文件） | Python 独立复算+CDP 真实点击 5 态全同步+零控制台错误；自发建 evidence/（任务书未强制） |
| G3-A2plus | <实验根目录>\ab-v4\G3-dashboard\A2plus\（index.html + evidence/ 四脚本+报告，21 文件） | 双语言复算交叉一致+DOM 仿真 16 断言+Edge headless 5 态+变异 3/3+对比度 8/8≥4.5:1+**唯一坏输入防御**（?scope=zzz/q999/URL编码注入安全回退）；「无控制台报错」主动标 UNVERIFIED，判分子 CDP 补验证实成立 |
| D3-conservative | <实验根目录>\ab-v4\P-B\D3-conservative\（report.md + evidence/ 16+ 文件：01_explore.py,02a_methods_statistical.py,02b_methods_trendresid.py,02c_methods_iforest.py,03_consensus.py,consensus_result.json,sensitivity_result.json,05_mutation_test.py,06_plot.py,07_acceptance.py,points_m1-m4_loose/strict.csv,segments_per_method.json,detection_overview.png） | 4 方法（全局z/相位基线/趋势残差/IsolationForest）共识，主报告 4 区段+附录 86 候选；30 组扰动敏感性全 robust；变异注入红/对照绿 PASS；验收 C1-C7 全过 |
| D3-noconstraint | <实验根目录>\ab-v4\P-B\D3-noconstraint\（report.md + evidence/ 16 文件：m1_rolling_mad.py,m2_seasonal_profile.py,m3_jump_static.py,merged_intervals.csv,merge_and_validate.py,cross_validation.json/md,validate_deliverables 等） | 3 方法合并 40 区间（9 个≥2方法确认）；发现源数据 12 重复时间戳+1 乱序块（gap=-3300s@row10149）；23 项完成标准核验+40/40 极值复核 PASS；无变异测试、全文无 UNVERIFIED 字样 |
| D3-fullreport | <实验根目录>\ab-v4\P-B\D3-fullreport\（report.md + evidence/ 13 文件：10_multipath_detect.py,10_intervals_full/highconf.csv,10_summary.json,00_data_profile,20_mutation_test,25_crosscheck,30_gen_report_tables） | 四路径（全局MADz/滚动残差/季节残差/差分）全量合并 55 区间+高置信（≥2方法）7 区间；变异 12/12 命中+对照 0 误报；独立复算 55 区间极值全一致；自曝两处过程缺陷已修复 |
| D3-interrupt | <实验根目录>\ab-v4\P-B\D3-interrupt\（report.md + evidence/ 21-22 文件：s1_load_overview,s2_method1_robustz,s3_method2_slowbaseline,s4_method3_globalquantile,s5_clusters.json,s5_crossvalidate.py,s5b_daily_median 等） | 3 机制（滚动鲁棒Z/季节基线残差/全局分位包络），主报告 32 区段+附录 19 候选；分段落盘 21 文件全留存（中断为弱形式：实际未运行中 kill，团队暂停时目录为空从零重启）；复跑一致；参照系变更历史独特 |

## 5. 执行过程行为链审计（jsonl 归档）

路径前缀：`<用户目录>\.workbuddy\projects\c-Users-<用户名>-WorkBuddy-2026-09-10-23-57-12\45c568dd-ff70-4d57-af10-5860ee739c6b\subagents\`

| jsonl | 臂 | skill读取 | evidence落盘 | 门禁 | 完成标准 | 变异测试 | UNVERIFIED | 截图 | 交叉验证 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| agent-461fd4e6 | G1-B′ | 0 | 11 | 15 | 0 | 1 | 6 | 2 | 22 |
| agent-9d7c33b8 | G1-A2 | 21 | 178 | 231 | 35 | 4 | 96 | 271 | 106 |
| agent-599e75e9 | G1-A2+ | 20 | 284 | 288 | 46 | 220 | 63 | 342 | 241 |
| agent-b59f4c12 | G2-B′ | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| agent-8222a299 | G2-A2 | 15 | 160 | 197 | 22 | 5 | 62 | 343 | 85 |
| agent-06f04a64 | G2-A2+ | 12 | 356 | 206 | 17 | 89 | 43 | 199 | 155 |
| agent-0384581c | G3-B′ | 0 | 21 | 52 | 0 | 1 | 2 | 2 | 68 |
| agent-d4461ef7 | G3-A2 | 13 | 139 | 144 | 13 | 3 | 39 | 167 | 38 |
| agent-85b272cf | G3-A2+ | 22 | 424 | 276 | 30 | 163 | 65 | 18 | 351 |
| agent-5a93c739 | D3-保守度 | 8 | 130 | 197 | 45 | 169 | 43 | 43 | 248 |
| agent-8bf21b82 | D3-无保守度 | 8 | 168 | 169 | 39 | 12 | 32 | 18 | 262 |
| agent-5717c402 | D3-全量 | 8 | 97 | 156 | 12 | 114 | 47 | 9 | 260 |
| agent-041ad668 | D3-中断 | 8 | 268 | 210 | 23 | 11 | 40 | 16 | 339 |

要点：B′ 三臂 skill 读取全 0（边界 100% 合规）；变异测试 A2+ 89–220 次 vs A2 3–5 vs B′ 0–1（多路径条款行为指纹）；evidence 落盘 A2+ 284–424 最高；映射方法=配置特征句（「轻量（验证聚焦版）」=A2/「验证深度增强版」=A2+/「无 skill 基线」=B′），jsonl 文件名 hash≠task_id。判分子 task_id：91=8c0e208b、92=356f2327、93=0d55b94a、94=53f68cf8（jsonl 同目录按 mtime 定位）。

## 6. 盲评结果（4 判分子×真机 Chrome headless CDP 可信鼠标键盘+四通道控制台+evidence 重跑抽验；五维各 0-10）

映射：G1 22=B′/89=A2/34=A2+；G2 39=B′/57=A2/58=A2+；G3 63=B′/52=A2/16=A2+；D3 56=保守度/36=全量/60=无保守度/79=中断。

| 床 | 匿名=臂 | 正确 | 深度 | 可验证 | 结构 | 诚实 | 直和 | 床内序 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| G1 | 34=A2+ | 10 | 9.5 | 9 | 9 | 10 | 48.5 | 1 |
| G1 | 89=A2 | 10 | 8.5 | 9 | 9 | 9 | 45.5 | 2 |
| G1 | 22=B′ | 10 | 7 | 4 | 8.5 | 6 | 35.5 | 3 |
| G2 | 57=A2 | 10 | 9 | 9 | 9 | 9 | 46 | 1 |
| G2 | 58=A2+ | 7 | 8 | 10 | 8 | 6 | 39 | 3 |
| G2 | 39=B′ | 10 | 8 | 5 | 9 | 6 | 38 | 2 |
| G3 | 16=A2+ | 10 | 9.5 | 9.5 | 9 | 10 | 48 | 1 |
| G3 | 52=A2 | 10 | 8.5 | 8 | 8.5 | 9 | 44 | 2 |
| G3 | 63=B′ | 9.5 | 8 | 6 | 9 | 8 | 40.5 | 3 |
| D3 | 56=保守度 | 9 | 9 | 9.5 | 8.5 | 9 | 45 | 1 |
| D3 | 36=全量 | 8.5 | 8.5 | 9 | 8.5 | 9.5 | 44 | 2 |
| D3 | 60=无保守度 | 8.5 | 8 | 8.5 | 9 | 8 | 42 | 3 |
| D3 | 79=中断 | 8 | 7.5 | 8.5 | 8 | 8.5 | 40.5 | 4 |

判分子关键发现（全部有实测记录）：
- G1（91号）：34 唯一真运算优先级+三路径全复现（唯一扣分 test-browser.mjs 硬编码绝对路径）；89 的 47/47 可原地一键重跑+往返一致性最佳（acc 保原始浮点）；22 功能全对+错误文案最友好但零证据；`0.1+0.2` 三臂都清理显示未分化（埋点鉴别力弱）；三臂控制台零错误。
- G2（92号）：57 行为 30/30+证据链完整+首轮 26/27 失败诚实披露，仅 punycode 1 漏洞；39 行为满分但零证据零自证；58 可验证性 10（唯一一键重跑）但**中文拦截失守+4 项邮箱边界放行**，电池未覆盖且未披露盲区，ALL GREEN 高估覆盖面——定性「披露缺失而非造假」。
- G3（93号）：16 唯一坏输入防御+诚实 UNVERIFIED 与判分子 CDP 补验互证；52 verify_data.py 复跑相符+声明与实物相符；63 零证据链+Y 轴 62.5/187.5 非整值瑕疵；三份数值全对、5 态同步、独立复算一致、控制台三通道零报错。
- D3（94号）：10 脚本重跑全部复现、零声称失实；独立核查数据质量（12 重复时间戳/乱序-3300s/值域 2.08~108.51/无 NaN）与执行臂披露全部相符；56 验证体系最完整（敏感性审计独有）；36 诚实最佳（自曝两处过程缺陷）；60 无变异测试+无 UNVERIFIED 字样；79 无注入类验证+C11 边界僵硬；「区段数量差异（4/55/40/32）未作为扣分项」。

## 7. D3 客观精算（lead 侧，结构化源正式口径，±60min 容差）

| 臂 | 主报告区间 | 命中 | recall | precision | 漏检点 |
|---|---:|---:|---:|---:|---|
| conservative（primary 键） | 4 | 2/4 | 0.50 | **0.500** | 12-11、01-28 |
| noconstraint（merged_intervals.csv 40 行） | 40 | 3/4 | 0.75 | 0.075 | 12-11 |
| fullreport（10_intervals_full.csv 55 行） | 55 | 3/4 | 0.75 | 0.055 | 01-28 |
| fullreport 高置信子集（10_intervals_highconf.csv 7 行） | 7 | 2/4 | 0.50 | 0.286 | 12-11、01-28 |
| interrupt（s5_clusters.json main_report_segments） | 32 | 3/4 | 0.75 | 0.094 | 12-11 |

- 保守度版漏检 01-28 13:55 **不在** appendix 86 候选 ±60min 内（最近候选 01-28 15:05~18:40，起点距 70 分钟——按 Phase 0 先例注记「疑似同事件超容差不命中」）。
- 宽松 markdown 解析曾得 conservative 3/4（附录混入高估）与 62/51 区间（元数据行）——已修（>7d 过滤）并改用结构化源，此教训已写入技能。
- Phase 0 参照：A2 轻量 3 区间 0.75/1.00（其命中含 12-11）；本轮 A2+ 四臂均未命中 12-11。

## 8. 条款级验证结论（对照 18 项缺口）

1. **实操闭环正向路径（底线）**：首次正向证据——6 skill 臂全部自发真机实操，B′ 三臂中 2 臂未上真实浏览器（G1 用 stub、G2 仅语法检查），可验证性 4-6 vs 8-10。
2. **A2+ ①多路径**：行为指纹成立（变异 89-220 vs 3-5 vs 0-1），但 G2 反例=**多路径≠覆盖面**，验证路径不足时「验证错了也全绿」。
3. **A2+ ②证据入 evidence/**：成立（A2+ 284-424 vs A2 139-178 vs B′ 0-21；G2-A2+ 唯一一键复现）。
4. **A2+ ③可检查标准**：成立（A2+ 17-46 vs B′ 0）。
5. **A2+ ④保守度调节**：两分支均按设计工作（精确交付 precision 9 倍↑/安全监控全量 recall 保持 0.75）；recall 代价 0.25 需条款化明示。
6. **条款执行率审计轨**：可行（jsonl 10 指标矩阵）；B′ 边界 100% 合规。
7. **仍零覆盖**：中等档、类型漂移、参照系变更闭环、Resume Check、子 Agent、模式3、资产编排、搜索判类型、宿主对齐、文件整理、自定义中间档、轻通道排除项、2 轮收敛、让位原则、发散收敛、严格中断注入、5 类型复证。

## 9. 与 cycle-2/Phase 0 对比

- cycle-2 NULL（交付 A=B）在 GUI 任务被打破：G1/G3 剂量效应成立。归因：①GUI 任务让验证产生真实信息差 ②真机判分可检出证据链差异 ③0-10 尺度替代 0-2。
- B′ 基线画像修正：不是不会验证而是**验证不稳定**（真浏览器/语法检查/DOM stub 三样）——skill 增量=验证纪律一致性+证据留存。
- A2+ 双面性：可验证性三连 10 分+变异指纹；但正确性可因覆盖盲区失守（G2）。

## 10. 待总指挥裁决与 Stage 2 候选

1. A2+ 条款修订候选：覆盖面枚举强制前置+ALL GREEN 盲区自查声明（治 G2 反例）。
2. 严格中断注入实验（运行中 TaskStop kill）。
3. P-C（中等档/类型漂移/参照系变更，4 执行）、P-D（5 类型×3 臂复证，15 执行）放量。
4. 埋点鉴别力改进（G1 浮点陷阱未分化）。
5. 仓库 push 状态：HEAD=fe6d876（batch 94），origin/main 跟踪引用 [gone]（本地引用问题），推送由总指挥 cmd 手动执行（铁律 1）。cf561aa（batch 98 cycle-2 归档）亦在此 HEAD 链上。

—— 同步包完（本文档与 <实验根目录>\ab-v4\FINAL-VERIFY-REPORT.md 配套，后者为判分视角定稿报告）——
