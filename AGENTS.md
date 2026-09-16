# AGENTS.md / Agent 入口（跨运行时别名）

本仓库是一个 Agent Skill：`gpt-series-reasoning-style`（交付验收纪律层，中文主导）。
This repository is an Agent Skill: `gpt-series-reasoning-style` (a delivery-discipline layer, Chinese-primary).

识别 `AGENTS.md` 的运行时（Codex / Gemini CLI / Copilot CLI 等）按以下顺序初始化：
Runtimes that recognize `AGENTS.md` initialize as follows:

1. 读取 `SKILL.md` 与 `VERSION`——**加载证明只需要这两个文件**。
   Read `SKILL.md` and `VERSION` — **the loading proof requires only these two files**.
2. 按 `SKILL.md` 的规则执行任务；`references/` 与 `templates/` 按需读取——平时不读，
   仅当任务叠加形态二三（子智能体 / 多智能体）时才读 `references/multi-agent.md` 与模板。
   Follow the rules in `SKILL.md`; `references/` and `templates/` are on-demand — read
   `references/multi-agent.md` and the templates only when the task stacks mode 2/3 (sub-agent / multi-agent).
3. 被要求证明已加载时：输出版本号；说明五面时序（规划面1 自由构想 → 规划面2 规则规划 → 执行面 → 审查面1 直觉 → 审查面2 纪律）；
   逐字引用审查面2 第 1 条「真打开看一眼：产物在真实环境打开、真用一遍，不许只看代码或心算就宣布完成。」；
   说明协作形态（默认形态一；形态二有明显增益就自觉开；形态三由用户指名）；列出实际读过的文件。
   When asked to prove loading: state the version; describe the five-face sequence (plan-1 free thinking →
   plan-2 ruled planning → execution → review-1 intuition → review-2 discipline); quote Review-2 rule 1
   verbatim ("真打开看一眼：产物在真实环境打开、真用一遍，不许只看代码或心算就宣布完成。"); state the
   collaboration modes (mode-1 default; mode-2 self-initiated when clearly beneficial; mode-3 user-named);
   and list only the files actually read.
4. 没有读到 `SKILL.md` 或 `VERSION` 时，不伪造，停止并请求只读权限。
   If `SKILL.md` or `VERSION` is unavailable, do not fabricate — stop and request read permission.

冲突裁决：本文件只是入口指路；规则权威在 `SKILL.md`（需跨运行时同步改动时，一并更新本文件）。
On conflict: this file is a router only; the authority is `SKILL.md` (when a change must be mirrored across
runtimes, update this file in the same pass).
