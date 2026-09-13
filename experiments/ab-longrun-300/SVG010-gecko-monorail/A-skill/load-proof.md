# Load Proof — gpt-series-reasoning-style

## Version

`1.2.0`

（来源：`<skill安装目录> 与 `SKILL.md` 末节 Current version: 1.2.0）

## Hard rule #1 (verbatim)

> 宣布阶段序列不是确认。

（出处：`SKILL.md` → Mandatory Pre-Implementation Gate → 硬性规则第一条）

## Collaboration architecture (brief)

主干（默认）· 单 Agent 模式 — 同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。

扩展A · 子 Agent 增强 — 任务适合并行或隔离且宿主支持子 Agent 时，把部分角色面映射为子 Agent；启用前必须先确认子 Agent 能力，能力未证实退回主干并标记 `UNVERIFIED`。

扩展B · 指挥官多 Agent — 需要协调独立大模型/Agent 或经用户转交时，对该任务启用模式三协议；只影响启用的任务，不改变主干地位。

形态由 AI 按任务事实自选并在门禁声明一行理由；用户指名优先、可随时切换。

## Files actually read

| Path | Role |
|------|------|
| `<skill安装目录> | skill body (required) |
| `<skill安装目录> | version stamp (required) |
| `<实验根目录>\ab-longrun-300\SVG010-gecko-monorail\A-skill\task.md` | local task brief (workspace context) |

References under the skill directory were **not** read this session (on-demand; not required for load proof).

## Status

Load proof complete. No implementation performed. Awaiting next instruction (host-alignment / gate / implementation).
