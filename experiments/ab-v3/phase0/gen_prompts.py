# -*- coding: utf-8 -*-
"""Phase 0 预注册 prompt 生成器（batch 94）。
本脚本是 9 份执行 prompt 的唯一权威来源；spawn 使用的文本与生成文件逐字一致。
生成时间：2026-09-13；总指挥批复：Phase 0 范围确认 / 任务集外部公开数据集 / 基线 1.2.x。
"""
import os

ROOT = "<实验根目录>/ab-v3/phase0"
SNAP = "<实验根目录>/ab-v3/skill-snapshot-v1.2.1"

ISOLATION = """
【边界·必须遵守】
- 只允许读取：上列数据文件（A 臂另加 skill 快照两个文件）。python 及已装库可用。
- 只允许写入：你的交付目录（下方指定）。
- 禁止读取：<实验根目录> 下除上述数据文件外的任何内容（包括其他目录、其他实验、truth/frozen、PROMPTS）；<skill安装目录> 下任何文件。
- 可联网查资料；但禁止下载数据文件替代指定数据集——交付必须基于指定数据文件。
"""

HARNESS_NOTE = """
【环境说明】本任务书即用户授权；本环境为非交互 harness，无实时用户在线。skill 中的停等类条款（如实现前确认等待授权）按 skill 自带「不阻塞」条款处理：输出声明后继续执行，不停等。诚实标记（UNVERIFIED）/证据报告/真实环境验收三条底线照常执行。
"""

ARM_BLOCK = {
    "Bprime": "",  # 无 skill、正常发挥；不读快照
    "A2": f"""
【skill 加载】先完整读取以下两个文件，再按其中「模块化选择矩阵——轻量（验证聚焦版）」配置执行本任务（不升级中/重档）：
- {SNAP}\\SKILL.md
- {SNAP}\\VERSION
{HARNESS_NOTE}""",
    "A1": f"""
【skill 加载】先完整读取以下两个文件，再按 skill 全流程（完整工作流，默认配置）执行本任务：
- {SNAP}\\SKILL.md
- {SNAP}\\VERSION
{HARNESS_NOTE}""",
}

TASKS = {
    "D1-winequality": """【任务 D1·红酒质量分析】分析红酒理化数据集并交付分析报告。
数据文件：<实验根目录>\\ab-v3\\datasets\\winequality-red.csv（UCI Wine Quality 红酒数据集，分号分隔、带引号表头、1599 行）
必答问题（全部要给出具体数值，不许只给方法）：
1. 各理化指标与 quality 的 Pearson 相关系数（保留 6 位小数），按绝对值从大到小排序输出全部 11 项
2. quality 各档位（3~8）的样本计数
3. quality≥7（高质组）与 quality≤4（低质组）的 alcohol 均值（4 位小数）及两者差值
交付物（写入 <实验根目录>\\ab-v3\\phase0\\D1-winequality\\{ARM}\\）：
- report.md：结论、方法、你如何验证自己的数字
- 你实际运行的脚本文件""",
    "D2-cafe": """【任务 D2·咖啡馆销售数据清洗】清洗脏数据并交付分析报告。
数据文件：<实验根目录>\\ab-v3\\datasets\\cafe_sales_dirty.csv（10000 行交易记录；"ERROR"/"UNKNOWN"/空字符串表示缺失）
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
交付物（写入 <实验根目录>\\ab-v3\\phase0\\D2-cafe\\{ARM}\\）：
- report.md + 你实际运行的脚本""",
    "D3-nab": """【任务 D3·时序异常检测】对传感器温度时序做异常检测并交付报告。
数据文件：<实验根目录>\\ab-v3\\datasets\\nab_machine_temp.csv（机器温度时序，22695 行，timestamp,value；已知该序列存在若干真实异常区段）
必答问题：
1. 检测并报告所有你认为异常的区间，每个区间给出 [起止时间(与数据同格式), 峰值或谷值]
2. 简述检测方法与阈值判定依据
交付物（写入 <实验根目录>\\ab-v3\\phase0\\D3-nab\\{ARM}\\）：
- report.md + 你实际运行的脚本
（评分按预注册口径：报告区间与官方标注异常点做命中/误报/漏报统计；标注点数量与判定容差不向执行者公布）""",
}

ARMS = ["Bprime", "A2", "A1"]

for task, core in TASKS.items():
    for arm in ARMS:
        d = os.path.join(ROOT, task, arm)
        os.makedirs(d, exist_ok=True)
        text = core.replace("{ARM}", arm) + ISOLATION + f"""
【汇报要求】完成后回报不超过 150 字：产出文件清单 + 你跑了什么验证 + 不确定项。
"""
        text += ARM_BLOCK[arm]
        with open(os.path.join(d, "PROMPT.md"), "w", encoding="utf-8") as f:
            f.write(text)
        with open(os.path.join(ROOT, "PROMPTS", f"{task}_{arm}.md"), "w", encoding="utf-8") as f:
            f.write(text)
print("9 prompts written (pre-registered).")
