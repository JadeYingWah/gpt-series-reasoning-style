# Load Proof · gpt-series-reasoning-style

## Version

1.2.0

## Mandatory Pre-Implementation Gate — 硬性规则第一条（逐字引用）

> 宣布阶段序列不是确认。

## 协作架构简介

- **主干（默认）**：单 Agent 模式 —— 同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- **扩展A（按需）**：子 Agent 增强 —— 任务适合并行或隔离且宿主支持子 Agent 时启用；启用前须确认子 Agent 能力，未证实退回主干并标 `UNVERIFIED`。
- **扩展B（按需）**：指挥官多 Agent —— 需协调独立大模型/Agent 时启用模式三协议；只影响启用的任务。
- **形态选择**：由 AI 按任务事实自选，并在门禁中声明一行理由；用户指名优先、可随时切换；可按阶段混合搭配。

## 实际读取的文件

| 文件 | 状态 |
|------|------|
| `<skill安装目录> | 已读 |
| `<skill安装目录> | 已读 |
| `<实验根目录>\ab-longrun-300\SE013-slugify\A-skill\task.md` | 已读（任务上下文） |

references/ 目录未读（按需读取；本阶段未触发）。

## 范围声明

- 本阶段（阶段1）仅产出本文件 `load-proof.md`。
- 未修改 `slugify.py`（禁止）。
- 未创建测试、未输出实现前门禁、未执行实现命令。
