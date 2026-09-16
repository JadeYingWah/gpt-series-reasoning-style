# Load Proof — gpt-series-reasoning-style

## Version

`1.2.0`

Source: `<skill安装目录>

## Mandatory Pre-Implementation Gate — Hard Rule #1 (verbatim)

> 宣布阶段序列不是确认。

## Collaboration Architecture (brief)

- **主干（默认）**: 单 Agent — 同一模型内部切换规划面 / 执行面 / 审查面；绝大多数任务由此完成。
- **扩展A（按需）**: 子 Agent 增强 — 任务适合并行或隔离且宿主支持子 Agent 时启用；启用前须确认子 Agent 能力，未证实则退回主干并标 `UNVERIFIED`。
- **扩展B（按需）**: 指挥官多 Agent — 协调独立大模型/Agent 或经用户转交时对该任务启用模式三协议；只影响启用的任务。
- 形态由 AI 按任务自选并在门禁声明一行理由；用户指名优先、可随时切换。

## Files Actually Read

| File | Role |
|------|------|
| `<skill安装目录> | Skill body (load-proof source of truth) |
| `<skill安装目录> | Version string `1.2.0` |
| `<实验根目录>\ab-longrun-300\SVG008-beetle-cable-car\A-skill\task.md` | Project task brief (context only; not required for load proof) |

Not read (by design — load proof needs only SKILL.md + VERSION; references on demand):

- `references/*`
- `docs/*`
- `CHANGELOG.md`

## Status

Load proof complete. Phase 1 stopped here. No pre-implementation gate, host-alignment declaration, or implementation performed.
