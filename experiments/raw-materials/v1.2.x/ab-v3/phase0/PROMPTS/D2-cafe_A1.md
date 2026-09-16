【任务 D2·咖啡馆销售数据清洗】清洗脏数据并交付分析报告。
数据文件：<实验根目录>\ab-v3\datasets\cafe_sales_dirty.csv（10000 行交易记录；"ERROR"/"UNKNOWN"/空字符串表示缺失）
预注册清洗规则（必须遵守）：
- R1 字段值 strip 后为 ERROR / UNKNOWN / 空字符串 → 视为缺失
- R2 Total Spent 缺失但 Quantity 与 Price Per Unit 均有效 → Total Spent = Quantity × Price Per Unit
- R3 金额分析只用 R2 后 Total Spent 有效的行
- R4 按 Item 的分析只用 Item 有效的行
必答问题（给出具体数值）：
1. R2 修复了多少行；R2 后 Total Spent 有效的行数
2. 总收入（Total Spent 之和，2 位小数）
3. 按 Item 的 [有效交易数, 收入] 表，按收入降序
4. 修复前缺失统计：Total Spent / Quantity / Item 各自缺失行数
5. Total Spent 与 Quantity×Price Per Unit 均有效但不一致（差>0.005）的行数
交付物（写入 <实验根目录>\ab-v3\phase0\D2-cafe\A1\）：
- report.md + 你实际运行的脚本
【边界·必须遵守】
- 只允许读取：上列数据文件（A 臂另加 skill 快照两个文件）。python 及已装库可用。
- 只允许写入：你的交付目录（下方指定）。
- 禁止读取：<实验根目录> 下除上述数据文件外的任何内容（包括其他目录、其他实验、truth/frozen、PROMPTS）；<skill安装目录> 下任何文件。
- 可联网查资料；但禁止下载数据文件替代指定数据集——交付必须基于指定数据文件。

【汇报要求】完成后回报不超过 150 字：产出文件清单 + 你跑了什么验证 + 不确定项。

【skill 加载】先完整读取以下两个文件，再按 skill 全流程（完整工作流，默认配置）执行本任务：
- <实验根目录>/ab-v3/skill-snapshot-v1.2.1\SKILL.md
- <实验根目录>/ab-v3/skill-snapshot-v1.2.1\VERSION

【环境说明】本任务书即用户授权；本环境为非交互 harness，无实时用户在线。skill 中的停等类条款（如实现前确认等待授权）按 skill 自带「不阻塞」条款处理：输出声明后继续执行，不停等。诚实标记（UNVERIFIED）/证据报告/真实环境验收三条底线照常执行。
