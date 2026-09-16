# Load Proof — gpt-series-reasoning-style

## Version

**1.2.0**

Source: `<skill安装目录> (exact file content: `1.2.0`).
Cross-check: SKILL.md §Version states "Current version: 1.2.0 (public release; post-1.2.0 rule increments are tracked as Unreleased batches in CHANGELOG.md — cite the batch when it matters)."

## Mandatory Pre-Implementation Gate — Hard Rule #1 (verbatim)

> 宣布阶段序列不是确认。

(Skill text, hard rules block, first bullet. English sense: announcing a phase sequence is not confirmation / is not authorization.)

## Collaboration Architecture (brief)

- **Backbone (default)**: Single Agent mode — one model switches planning / execution / review faces; most tasks complete here.
- **Extension A (on-demand)**: Sub-agent enhancement — map role faces to sub-agents when parallelism or isolation fits and the host supports it; only after sub-agent capability is confirmed, else fall back and mark `UNVERIFIED`.
- **Extension B (on-demand)**: Commander multi-Agent — for coordinating independent models/agents or user handoff; mode-3 protocol (role identity, channel, full task package + closure) only for the tasks that enable it.

Form is chosen by the AI per task with a one-line reason declared at the gate; user-named form takes priority and can switch at any time. Extensions each need their own confirmation gate.

## Files actually read (this load)

| Path | Role |
|------|------|
| `<skill安装目录> | Primary skill body (core style, load proof, architecture, gate, workflow, references map, version note) |
| `<skill安装目录> | Version pin (`1.2.0`) |
| `<实验根目录>\ab-longrun-300\SE012-slugify\A-skill\task.md` | Task context (SE012 slugify deliverables / acceptance / bans) — not skill content |
| `<实验根目录>\ab-longrun-300\SE012-slugify\A-skill` (directory listing) | Workspace inventory: `slugify.py`, `task.md` |

**Not read (by design of this load proof)**: any `references/*` under the skill; CHANGELOG.md. Per skill rule: load proof requires only `SKILL.md` + `VERSION`; references are read on demand.

## Host alignment note

Host alignment declaration (capability overlap + SKIP map + trimmed scope) is **not** part of this load-proof file; it is the next one-time step after load proof and before the first gate. This phase stop is load proof only.
