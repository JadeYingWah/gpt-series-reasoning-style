# Load Proof · gpt-series-reasoning-style

## Version

Current version: **1.2.0**

## Mandatory Pre-Implementation Gate 硬性规则第一条（逐字引用）

> 宣布阶段序列不是确认。

## 协作架构简介

- 主干（默认）：单 Agent 模式 — 同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- 扩展A：子 Agent 增强 — 任务适合并行或隔离且宿主支持子 Agent 时启用；启用前须先确认子 Agent 能力，能力未证实退回主干并标记 `UNVERIFIED`。
- 扩展B：指挥官多 Agent — 需要协调独立大模型/Agent 或经用户转交时启用；只影响启用的任务，不改变主干地位。
- 形态由 AI 按任务自选并在门禁声明一行理由；用户指名优先、可随时切换；可混合搭配。

## 实际读过的文件

1. `<skill安装目录> 113 行）
2. `<skill安装目录>
3. `<实验根目录>\ab-longrun-300\SE005-slugify\A-skill\task.md`（任务上下文，非 skill 加载必需）

## 阶段范围

本次仅完成阶段1（加载证明）。未进入门禁、未改 `slugify.py`、未创建测试或 response。
