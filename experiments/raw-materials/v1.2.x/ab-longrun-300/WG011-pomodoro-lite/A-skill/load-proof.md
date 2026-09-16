# 加载证明（Load Proof）

任务：WG011-pomodoro-lite · 极简番茄钟（单文件）  
范围：阶段 1 only — 证明 skill 已加载，不进入实现前门禁、不实现。

## 版本号

Current version: **1.2.0**  
（来源：`<skill安装目录> 全文一行 `1.2.0`；与 SKILL.md Version 节 “Current version: 1.2.0” 一致。）

## Mandatory Pre-Implementation Gate 硬性规则第一条（逐字引用）

> 宣布阶段序列不是确认。

## 协作架构简介

- **主干（默认）· 单 Agent 模式** — 同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- **扩展A · 子 Agent 增强** — 任务适合并行或隔离（并行分支、独立审查）且宿主支持子 Agent 时启用；启用前必须先确认子 Agent 能力，能力未证实退回主干并标记 `UNVERIFIED`。
- **扩展B · 指挥官多 Agent** — 需要协调独立大模型/Agent 或经用户转交时启用；只影响启用的任务，不改变主干地位。
- **形态选择**：形态由 AI 按任务事实自选，并在门禁声明一行理由；用户指名优先、可随时切换。可混合搭配（同一任务不同阶段可用不同形态）。

## 实际读过的文件

| 文件 | 路径 | 用途 |
|------|------|------|
| SKILL.md | `<skill安装目录> | 本 skill 主文件（加载证明权威依据） |
| VERSION | `<skill安装目录> | 版本号 `1.2.0` |
| task.md | `<实验根目录>\ab-longrun-300\WG011-pomodoro-lite\A-skill\task.md` | 本任务指令（交付范围与验收清单） |
| meta.json | `<实验根目录>\ab-longrun-300\WG011-pomodoro-lite\meta.json` | 任务元数据（id/title/kind） |

未读取 references/ 目录下任何按需文件（阶段 1 仅需 SKILL.md + VERSION；references 按需读取，本阶段不涉及）。

## 阶段 1 完成声明

- 已读取 `SKILL.md` 与 `VERSION`，版本号与硬性规则第一条均已逐字核对。
- 协作架构已按 SKILL.md 原文摘要列出。
- 未创建实现产物、未进入门禁、未实现 `pomodoro.html`。
