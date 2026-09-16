# 加载证明 — gpt-series-reasoning-style

## 版本号

1.2.0

## Mandatory Pre-Implementation Gate 硬性规则第一条（逐字引用）

> 宣布阶段序列不是确认。

## 协作架构简介

- 主干（默认）：单 Agent —— 同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- 扩展A：子 Agent 增强 —— 任务适合并行或隔离且宿主支持子 Agent 时启用；启用前必须先确认子 Agent 能力，能力未证实退回主干并标记 `UNVERIFIED`。
- 扩展B：指挥官多 Agent —— 需要协调独立大模型/Agent 或经用户转交时启用模式三协议；只影响启用的任务，不改变主干地位。
- 可混合搭配；形态由 AI 按任务事实自选并在门禁声明一行理由，用户指名优先、可随时切换。

## 实际读过的文件

1. `<skill安装目录> 113 行）
2. `<skill安装目录>

（按加载证明规则，references 按需读取；本次阶段1仅需 SKILL.md + VERSION，未读 references。）
