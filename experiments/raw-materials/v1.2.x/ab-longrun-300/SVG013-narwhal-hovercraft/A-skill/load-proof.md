# Load Proof — gpt-series-reasoning-style

## Version

**1.2.0**

## Mandatory Pre-Implementation Gate — 硬性规则第一条（逐字引用）

> 宣布阶段序列不是确认。

## 协作架构简介

- **主干（默认）· 单 Agent 模式**：同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- **扩展A · 子 Agent 增强**：任务适合并行或隔离且宿主支持子 Agent 时启用；启用前必须先确认子 Agent 能力，能力未证实退回主干并标记 `UNVERIFIED`。
- **扩展B · 指挥官多 Agent**：需要协调独立大模型/Agent 时启用模式三协议；只影响启用的任务，不改变主干地位。
- 形态由 AI 按任务事实自选并在门禁声明一行理由；用户指名优先、可随时切换；可混合搭配。

## 实际读取的文件

| 文件 | 说明 |
|------|------|
| `<skill安装目录> | 完整读取（113 行） |
| `<skill安装目录> | 完整读取（内容：`1.2.0`） |
| `<实验根目录>\ab-longrun-300\SVG013-narwhal-hovercraft\A-skill\task.md` | 完整读取（30 行，任务上下文） |

References 未读取（按需，加载证明不要求）。

## 状态

加载完成。停在阶段 1（load proof），未进入实现前门禁、未实现。
