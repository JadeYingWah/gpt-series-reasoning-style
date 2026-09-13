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

Phase 1 only (per task instruction). References under `references/` were not read — load proof requires only `SKILL.md` + `VERSION`. `slugify.py` was not modified after seed creation.

## Seed Note (A-skill bed was empty)

`<实验根目录>\ab-longrun-300\SE017-slugify\A-skill` did not exist. Per parent instruction, SE-series defect seed was self-built:

- `task.md` — SE series task body (id SE017), same as SE001–SE016 pattern
- `slugify.py` — defective seed identical to `_judge/generate_beds.py` `seed_slugify()` (no lower / no strip / non-alnum collapse only)

Seed defects left intact for Phase 2 RED→GREEN:

| Defect | Effect |
| --- | --- |
| no `.lower()` | `Hello` stays `Hello` |
| no NFKD / deaccent | `Café` is not folded to `cafe` |
| no `strip("-")` | leading/trailing separators leave dangling `-` |
| empty/punct-only not special-cased | `""` / `!!!` leave `""` or `-` depending on path |

Did not create `test_slugify.py` or `response.md` (Phase 2). Did not fix `slugify.py`.
