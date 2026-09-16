# Load Proof — gpt-series-reasoning-style

## Version

1.2.0

## Mandatory Pre-Implementation Gate — Hard Rule #1 (verbatim)

> 宣布阶段序列不是确认。

## Collaboration Architecture (brief)

单 Agent 主干默认 + 子 Agent 增强与指挥官多 Agent 按需扩展。形态由 AI 按任务自选并在门禁声明一行理由，用户指名优先。

- **主干（默认）· 单 Agent 模式** — 同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- **扩展A · 子 Agent 增强** — 任务适合并行或隔离且宿主支持子 Agent 时启用；启用前必须先确认子 Agent 能力，能力未证实退回主干并标记 `UNVERIFIED`。
- **扩展B · 指挥官多 Agent** — 需要协调独立大模型/Agent 或经用户转交时启用模式三协议；只影响启用的任务，不改变主干地位。

## Files Actually Read

1. `<skill安装目录>
2. `<skill安装目录>

## Scope Note

Phase 1 only (per task instruction). References under `references/` were not read — load proof requires only `SKILL.md` + `VERSION`. `slugify.py` was not modified.
