# 加载证明（Load Proof）

## 版本号

- Skill: `gpt-series-reasoning-style`
- Current version: **1.2.0**
- 来源：`VERSION` 文件（内容：`1.2.0`）与 `SKILL.md` 末节（`Current version: 1.2.0 (public release; post-1.2.0 rule increments are tracked as Unreleased batches in CHANGELOG.md — cite the batch when it matters).`）

## Mandatory Pre-Implementation Gate 硬性规则第一条（逐字引用）

> 宣布阶段序列不是确认。

## 协作架构简介

- **主干（默认）· 单 Agent 模式**：同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- **扩展A · 子 Agent 增强**：任务适合并行或隔离（并行分支、独立审查）且宿主支持子 Agent 时启用；启用前必须先确认子 Agent 能力，能力未证实退回主干并标记 `UNVERIFIED`。
- **扩展B · 指挥官多 Agent**：需要协调独立大模型/Agent 或经用户转交时，对该任务启用模式三协议；只影响启用的任务，不改变主干地位。
- 形态由 AI 按任务自选并在门禁声明一行理由（判定顺序见 agent-modes；轻通道免填）；用户指名优先、可随时切换；启用扩展须先用一句话说明理由，并各过各的确认门禁。

## 实际读过的文件

1. `<skill安装目录>
2. `<skill安装目录>

说明：本阶段仅按「加载证明」最小集读取 `SKILL.md` + `VERSION`；references 未读取（按需读取策略）。未修改 `slugify.py` 或其他实现文件。
