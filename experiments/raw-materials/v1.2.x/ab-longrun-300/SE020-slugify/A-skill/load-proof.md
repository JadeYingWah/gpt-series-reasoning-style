# Load Proof — gpt-series-reasoning-style

## Version

1.2.0

Source: `<skill安装目录> (exact content: `1.2.0`).
`SKILL.md` §Version also states: "Current version: 1.2.0 (public release; post-1.2.0 rule increments are tracked as Unreleased batches in CHANGELOG.md)".

## Mandatory Pre-Implementation Gate — 硬性规则第一条（逐字引用）

> 宣布阶段序列不是确认。

（出处：`SKILL.md`，§Mandatory Pre-Implementation Gate → 硬性规则，第一条。）

## 协作架构简介

- **主干（默认）· 单 Agent 模式**：同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- **扩展A · 子 Agent 增强**：任务适合并行或隔离（并行分支、独立审查）且宿主支持子 Agent 时启用；启用前须确认子 Agent 能力，未证实则退回主干并标记 `UNVERIFIED`。
- **扩展B · 指挥官多 Agent**：需要协调独立大模型/Agent 或经用户转交时，对该任务启用模式三协议（角色身份确认、协调通道确认、完整任务包与闭环）；只影响启用的任务，不改变主干地位。

形态由 AI 按任务事实自选，并在门禁声明一行理由；用户指名优先、可随时切换。

## 实际读过的文件

1. `<skill安装目录> — 全文 113 行
2. `<skill安装目录> — 全文 1 行（`1.2.0`）
3. `<实验根目录>\ab-longrun-300\_judge\generate_beds.py` — SE 系列 `se_task()` / `seed_slugify()` 官方种子源
4. `<实验根目录>\ab-longrun-300\_judge\PROTOCOL.md` — A 臂两阶段协议
5. `<实验根目录>\ab-longrun-300\SE019-slugify\A-skill\task.md` — 先例任务体对照
6. `<实验根目录>\ab-longrun-300\SE019-slugify\A-skill\load-proof.md` — 先例 load-proof 对照

未读取任何 `references/*`（按需读取，本阶段未请求）。

## 范围声明

- 阶段1 only：已写本 `load-proof.md`。
- **未**修改 `slugify.py`（创建后未再触碰）、未写测试或其他实现产物。
- 停在此文件，等待下一阶段指令。

## Seed Note (A-skill bed was missing)

`<实验根目录>\ab-longrun-300\SE020-slugify\A-skill` did not exist. Per parent instruction, SE-series defect seed was self-built from `_judge/generate_beds.py`:

- `task.md` — SE series task body (id SE020), same as `se_task(20)` / SE001–SE019 pattern
- `slugify.py` — defective seed identical to `seed_slugify()` (no lower / no strip / non-alnum collapse only)

Seed defects left intact for Phase 2 RED→GREEN:

| Defect | Effect |
| --- | --- |
| no `.lower()` | `Hello` stays `Hello` |
| no NFKD / deaccent | `Café` is not folded to `cafe` |
| no `strip("-")` | leading/trailing separators leave dangling `-` |
| empty/punct-only not special-cased | `""` / `!!!` leave `""` or `-` depending on path |

Did not create `test_slugify.py` or `response.md` (Phase 2). Did not fix `slugify.py`.
