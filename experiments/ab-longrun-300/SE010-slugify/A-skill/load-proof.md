# Load Proof — gpt-series-reasoning-style

## Version

Current version: **1.2.0** (public release; post-1.2.0 rule increments are tracked as Unreleased batches in CHANGELOG.md — cite the batch when it matters).

## Verbatim quote — Mandatory Pre-Implementation Gate 硬性规则第一条

> 宣布阶段序列不是确认。

## 协作架构简介

- **主干（默认）· 单 Agent 模式** — 同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- **扩展A · 子 Agent 增强** — 任务适合并行或隔离且宿主支持子 Agent 时启用；启用前必须先确认子 Agent 能力，能力未证实退回主干并标记 `UNVERIFIED`。
- **扩展B · 指挥官多 Agent** — 需要协调独立大模型/Agent 或经用户转交时启用模式三协议；只影响启用的任务，不改变主干地位。

形态由 AI 按任务事实自选并在门禁声明一行理由；用户指名优先、可随时切换。启用扩展须先用一句话说明理由，并各过各的确认门禁。

## 实际读过的文件

1. `<skill安装目录>
2. `<skill安装目录>
3. `<实验根目录>\ab-longrun-300\SE010-slugify\A-skill\task.md`
4. `<实验根目录>\ab-longrun-300\SE010-slugify\meta.json`

---

Phase 1 only. `slugify.py` 未修改。
