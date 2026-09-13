# Load Proof — gpt-series-reasoning-style

## Version

**1.2.0**

（来源：`<skill安装目录> Version 节同为 1.2.0。）

## Mandatory Pre-Implementation Gate 硬性规则第一条（逐字引用）

> 宣布阶段序列不是确认。

## 协作架构简介

- **主干（默认）· 单 Agent 模式**：同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- **扩展A · 子 Agent 增强**：任务适合并行或隔离且宿主支持子 Agent 时启用；启用前须先确认子 Agent 能力，能力未证实退回主干并标记 `UNVERIFIED`。
- **扩展B · 指挥官多 Agent**：需要协调独立大模型/Agent 时启用模式三协议（角色身份确认、协调通道确认、完整任务包与闭环）；只影响启用的任务。
- 形态由 AI 按任务事实自选并在门禁声明一行理由；用户指名优先、可随时切换。

## 本次实际读取的文件

| 文件 | 说明 |
|------|------|
| `<skill安装目录> | skill 本体（全文） |
| `<skill安装目录> | 版本号文件 |
| `<实验根目录>\ab-longrun-300\SVG015-seahorse-cableway\A-skill\task.md` | 任务规格（已存在，无需自建） |

## 阶段边界

本文件为 **阶段1 only**：完成加载证明后停止。未创建/编辑 `art.html`、`notes.md`、`response.md` 或其他实现产物。
