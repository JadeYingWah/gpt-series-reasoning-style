# Load Proof · gpt-series-reasoning-style

## Version

Current version: **1.2.0**
(From `VERSION`; SKILL.md Version section states: `1.2.0 (public release; post-1.2.0 rule increments are tracked as Unreleased batches in CHANGELOG.md — cite the batch when it matters).`)

## Mandatory Pre-Implementation Gate · Hard Rule #1 (verbatim)

> 宣布阶段序列不是确认。

## Collaboration Architecture Brief

- **主干（默认）**: 单 Agent — same model switches planning / execution / review faces; most tasks complete here.
- **扩展A**: 子 Agent 增强 — parallel or isolated branches when host supports sub-agents; capability must be confirmed first, else fall back to 主干 and mark `UNVERIFIED`.
- **扩展B**: 指挥官多 Agent — coordinate independent models/agents via Mode-3 protocol (role identity, channel, full task package); enabled only per-task.
- Form is self-selected by the AI per task and declared with a one-line reason in the gate; user-named form takes priority and can switch anytime. Mixed forms allowed across phases.

## Files Actually Read

| Path | Role |
|------|------|
| `<skill安装目录> | Skill body (loaded) |
| `<skill安装目录> | Version stamp 1.2.0 (loaded) |

References under `references/` were **not** read this phase (on-demand only, per 加载证明 rule).

## Scope of This Phase

Phase 1 only: load proof written. No implementation, no gate, no directories beyond this file, no `pomodoro.html`.
