# Load Proof — gpt-series-reasoning-style

## Version

`1.2.0`

(from `<skill安装目录>)

## Mandatory Pre-Implementation Gate · Hard Rule #1 (verbatim)

> 宣布阶段序列不是确认。

## Collaboration architecture (brief)

- **主干（默认）**：单 Agent — 同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- **扩展A（按需）**：子 Agent 增强 — 任务适合并行/隔离且宿主支持子 Agent 时，把部分角色面映射为子 Agent；启用前必须先确认子 Agent 能力，未证实退回主干并标 `UNVERIFIED`。
- **扩展B（按需）**：指挥官多 Agent — 需要协调独立大模型/Agent 时启用模式三协议；只影响启用的任务，不改变主干地位。

形态由 AI 按任务自选并在门禁声明一行理由；用户指名优先、可随时切换。可混合搭配。

## Files actually read

1. `<skill安装目录>
2. `<skill安装目录>
3. `<实验根目录>\ab-longrun-300\SE015-slugify\A-skill\task.md` (workspace task brief; listed for context only)

References under `references/` were **not** read in this phase (load proof requires only `SKILL.md` + `VERSION`; references are on-demand).

## Scope of this phase

Phase 1 only: prove load of the skill. No implementation, no edits to `slugify.py`, no test files, no pre-implementation gate output, no host-alignment declaration yet.
