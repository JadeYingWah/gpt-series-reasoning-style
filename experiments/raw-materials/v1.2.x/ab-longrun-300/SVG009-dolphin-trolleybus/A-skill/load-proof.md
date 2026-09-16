# 加载证明 · gpt-series-reasoning-style

## 版本号

Current version: **1.2.0**

（来源：`<skill安装目录> → `1.2.0`；SKILL.md 末节 Version 同步为 1.2.0 public release。）

## 硬性规则第一条（逐字引用）

> 宣布阶段序列不是确认。

出处：SKILL.md → Mandatory Pre-Implementation Gate → 硬性规则，第 1 条。

## 协作架构简介

本 skill 协作架构为 **单 Agent 主干默认 + 两个按需扩展**：

- **主干（默认）· 单 Agent 模式** —— 同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- **扩展A · 子 Agent 增强** —— 任务适合并行或隔离（并行分支、独立审查）且宿主支持子 Agent 时启用；启用前必须先确认子 Agent 能力，能力未证实退回主干并标记 `UNVERIFIED`。
- **扩展B · 指挥官多 Agent** —— 需要协调独立大模型/Agent 或经用户转交时启用模式三协议；只影响启用的任务，不改变主干地位。

形态由 AI 按任务自选并在门禁声明一行理由；用户指名优先、可随时切换。可混合搭配：同一任务的不同阶段可用不同形态。

## 实际读过的文件

| 文件 | 路径 | 读取结果 |
|------|------|----------|
| SKILL.md | `<skill安装目录> | 全文 113 行，成功 |
| VERSION | `<skill安装目录> | 全文 1 行，成功 |
| task.md | `<实验根目录>\ab-longrun-300\SVG009-dolphin-trolleybus\A-skill\task.md` | 全文 30 行，成功（本任务上下文，非 skill 加载必需） |

未读取 references/ 下任何文件（按需读取原则；本阶段仅需 SKILL.md + VERSION）。

---

阶段1（加载证明）完成。按指令停止，不进行实现。
