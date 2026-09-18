<div align="center">

# GPT-Series Reasoning Style

**Turn "the agent says it's done" into "the agent proves it's done".**

<img src="assets/social-preview.svg" alt="GPT-Series Reasoning Style · Delivery Discipline Layer" width="100%">

![Version](https://img.shields.io/badge/version-1.6.0-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Size](https://img.shields.io/badge/SKILL.md-3594%20bytes%C2%B735%20lines%20gate-orange)
![Experiments](https://img.shields.io/badge/A%2FB%20field%20tests-300%2B%20arms-success)
![Runtime](https://img.shields.io/badge/on--demand%20loading-pure%20text-blueviolet)
![CI](https://github.com/JadeYingWah/gpt-series-reasoning-style/actions/workflows/ci.yml/badge.svg)

中文版：[README.zh.md](README.zh.md)

</div>

## Origin and Scope

This skill is not an invented rule set. It was **observed and distilled** from long-term, hands-on use of a series of **GPT-series models** — including **GPT-5.6 Sol** and **GPT-6 Astra** — on real delivery tasks.

We kept and froze the habits these models showed at their best during planning and acceptance: **think it through before acting, ship reproducible verification, and flag what you could not verify**.

It is therefore **not** a model-specific add-on. What is distilled is **behavioral patterns**, not model capabilities — any instruction-following LLM can load it. "GPT-Series" in the name records its **origin**, not its **scope**.

**It does not pick its battles.** During execution the rule files are not loaded at all — the marginal cost of keeping it on is effectively zero at execution time: no thought interruption, no context tax, no workflow shoved in your face. Small and reversible tasks auto-degrade to "just do it, glance at the end" — no research, no plan approval. Across the **historical A/B line (233 task×arm×round)** plus later beds (script count ≥286 arms / 53 batches through 09-17 materials, plus 09-17 eight desktop beds and 09-18 four v1.6.0 single-arm field packs), **no task category showed the skill making things worse**; the consistent gain is in delivery trustworthiness, not in forcing a pipeline.

Code, writing, design, analysis, everyday Q&A — keep it on. Its only "cost" is one extra look before you ship; if you want raw speed, just say so.


## Why Not Copy Every Rule

Extensive A/B testing keeps showing one thing: **turning GPT's own behavioral traits into rules and injecting them into the user's execution process backfires.** You cannot make a user reproduce GPT-grade output quality by piling on rules.

In our tests, more rules did not mean better results: turning the discipline into hard metrics brought **no gain** (the gap versus principle-based guidance fell within scoring error and was judged equivalent), and the far heavier v1.2.5 build — 179 lines with 77 self-checks — was directly falsified and retired. Executors could not remember elaborate steps, templates were never fully filled, and compliance became theatre.

> **Version note**: the "more rules, worse results" comparison comes from **older v1.2.x builds** (v1.2.2 / v1.2.3-draft / v1.2.5). Hard metrics and bulky clauses were removed in the v1.4.x minimal line, so the comparison **no longer applies to the current 1.6.0**.

So we do only two things:

1. **Extract a few traits that can actually be followed** (really open it, mark what is unverified, all-green is not evidence, etc.);
2. Pair them with a **distinctive forgetting mechanism** — the discipline steps aside during execution and is reloaded at delivery time.

Users therefore **get the upside only**:

- more trustworthy deliveries (skill-armed runs score markedly higher on quality/discipline);
- "really open it" catches visual and runtime defects that code review misses;
- counter-example verification rises from roughly one-third to near-full coverage;
- unverified items are listed one by one, so you can tell at a glance what to trust and what to re-check.

while **avoiding the downside**:

- no ever-present discipline taxing attention, interrupting thought, or burning context;
- no regression from rule pile-up;
- no slide into checkbox-theatre.


## Coexists with Other Skills

> **No process hijack, only acceptance.** We designed the coexistence mechanism deliberately: this skill only intervenes at **stage 2 (planning)** and **stage 5 (acceptance)**. Stages 1/3/4 are completely open — any other type of skill (implementation/design/visual, etc.) runs its methods and workflows as usual, no interference. When workflows conflict, the host and user instructions take precedence.
>
> This means you can run frontend-design, imagegen, xlsx, or any other skill alongside this one as a delivery gate — each does its own job, no fighting.


## A First of Its Kind

To our knowledge, this is the first design to achieve **discipline/flow isolation across a five-stage timeline** — inside a **single skill**, via **file-level progressive loading**.

Five stages unfold in sequence:

| # | Stage | Rule state | What happens |
| - | ----- | ---------- | ------------ |
| 1 | **Unconstrained ideation** | absent | think it through on judgment alone |
| 2 | **Progressive rule loading for planning** | loading | turn the vision into a plan, **fully preserving** the stage-1 vision rather than overwriting it |
| 3 | **Execution** | withdrawn | focused work; rules simply do not exist |
| 4 | **Unruled check** | absent | intuition-driven, catching what the rules **do not** cover |
| 5 | **Progressive rule loading for discipline check** | reloaded | enforce every rule, one by one |

The result is two **zeros**:

- **Zero interruption while executing** — the rules are absent during execution, so flow is never broken;
- **Zero compromise at acceptance** — the rules reload in full at delivery, and nothing on the list is skipped.

And with that: **delivery trustworthiness rises markedly** (skill-armed runs score clearly higher on quality/discipline).

---

## The Actual Problem

The most expensive failure of an AI agent is never "it doesn't know how" — it's **declaring done without verifying**:

- Tests never actually ran, yet "all pass" is claimed;
- The HTML never opened in a browser, yet "page works" is claimed;
- Key numbers were never recalculated, yet the first-pass result is copied;
- The delivery says "audio implemented" — but there isn't a single line of audio code in the artifact.

In **four independent reproductions, 14 experimental arms total**, the AI **invariably** self-reported "all tests pass, verified working" — while independent review (mechanical adjudication) still found numerous real defects.

The 2026-09-17 same-task dual-arm test (4 mini-games, two independent teams) reproduced all of this: **the discipline-free arm** delivered and announced "playable end-to-end, all assertions pass" — file-by-file review showed the claimed verification didn't match the artifact. The same day, the disciplined control arm delivered **reproducible verification scripts with itemized assertion records**.

So what really matters isn't "how fast it works" — it's:

> **Do you dare use its output directly.**

This skill does one thing only: **turn "I think it's fine" into "it's verified, here's the evidence."**

## One Divergence

The default shape of mainstream skills is "**always present once loaded**"; multi-agent frameworks often push governance rules to **every** participant — the executor holds the commander's authority clauses, and role creep begins there.

This skill isolates to **two physical layers**:

1. **Executors and reviewers don't load this skill** — their behavioral norms come entirely from their identity files and task packages (self-contained). The commander's authority clauses (five stages, form judgment, config confirmation) are **physically not in their context**;
2. **The commander's own SKILL.md is also just a gate** (3594 bytes / 35 lines) — the full discipline (DISCIPLINE.md, 3862 bytes / 33 lines) is only released **the moment before action begins**.

Only one gate sentence lives in persistent context — you don't see the usual downsides of skills, you only get the benefits.

> **Why it's built this way**: most skills stay present once loaded. This skill splits into **planning** and **acceptance**, and goes further: even the commander's own SKILL.md is a pure gate — the discipline file is released the moment before action. You get the benefits **without paying the costs** of an ever-present discipline.

## How It Works

Once installed, **no special instructions needed**. When the agent receives a delivery task (write code, compute data, build a page, multi-agent orchestration), the SKILL.md pure gate releases the full discipline **the moment before action**, then enters the **five-stage timeline**:

```text
┌─ Gate (SKILL.md · 35-line pure gate) — "the moment before" = earliest of: write deliverable / construction confirm / build command / announce delivery
│         Creative tasks get one round of direction ideation without reading DISCIPLINE; unknown proper nouns still require ask/search first
│
┌─ Stage 1 · Free ideation (don't read plan/review/multi-agent, don't create governance dirs) — figure out what you're doing on your own
│      Exit: ideation points listed, about to enter planning or implementation
┌─ Stage 2 · Rule planning (read references/plan-rules.md) — turn plan into reality per rules, respond to each ideation item
│      Exit: plan confirmed (structured option cards) ＋ risk graded ＋ form decided
│             ＋ creative quality budget written (A-tier doesn't cap quality ceiling) ＋ no more questions to ask
┌─ Stage 3 · Execution (rules completely absent) — work with your abilities, flow uninterrupted
│      Exit: no unresolved bugs; creative/visual tasks additionally require "openable complete path"
┌─ Stage 4 · Intuitive check (no rules) — scan the deliverable on common sense
│      Exit: no new doubts found (doubts confirmed or fixed on the spot, not carried into stage 5)
└─ Stage 5 · Discipline check (read references/review-rules.md) — items 1–8 + item 9 completion tier
       Exit: rules passed (light tasks ★3 items + item 9 / heavy tasks full + item 9) ＋ three-piece set
             ＋ completion tier C1/C2 marked ＋ no unresolved "something looks off here"
```

**Completion tiers (1.6.0)**: Stage 5 pass = **C1 acceptable for acceptance** (must state whether product tier is maxed); "product is good" = **C2**, which can only come from your confirmation or an external scorecard — agents are forbidden from self-declaring. Execution side has no rules — discipline only appears at gate timing, stage 2, and stage 5.

**After task delivery**: completely forget the specific content of `plan-rules.md` / `review-rules.md` / `multi-agent.md` — only remember "there are five stages, read the right file at the right stage". What the rules actually say, read again next time.

Rule files are only read in at stage 2 and stage 5 — **during execution they're not in context at all**; the full discipline (DISCIPLINE.md) is also only released the moment before action.

The design intent is two sentences:

- **No discipline while creating** — stage 1 and the entire execution phase, rules don't pollute thought;
- **Two checks** — intuition catches what rules **don't cover**, discipline ensures what rules **do cover** is all done, neither replaces the other.

---

## What Delivery Looks Like

Same task, two faces before and after installation:

**Without the discipline layer:**

> Done. All features implemented, tests all pass.

**With the discipline layer:**

> **What was done**: rewrote export functionality, added 3 edge cases.  
> **How it was verified**: real browser render (screenshots attached); `pytest tests/test_export.py -q` → 12 passed.  
> **What wasn't verified**: ① Safari compatibility — no Safari on this machine, please open and verify yourself; ② performance on 100k+ row datasets — no existing dataset.

The difference isn't pretty formatting — it's that you **know at a glance which claims to trust and which to verify yourself**.

## How To Know It's Working

- Delivery messages start including the three-piece set: what was done / how it was verified (reproducible commands) / what wasn't verified;
- What wasn't verified is **admitted** up front, not glossed over;
- When the environment can't really open something, you get self-verification steps, not fake verification;
- After two consecutive failures on the same action, it switches paths instead of stubbornly retrying;
- On light tasks it's nearly invisible — **that's by design, not malfunction**.

---


## The Rules

Stage 5 (discipline check) strictly passes these **8 items** (★ = 3 items that light tasks must also do):

| #  | Rule | Key point |
| -- | ---- | --------- |
| 1★ | **Really open it** | Open and actually use the artifact in a real environment — HTML needs browser rendering, API needs frontend calls, running scripts doesn't count. Other types: games go through a full core gameplay loop, reports check every number against the source, SVG is really rendered and zoomed in on. When the environment doesn't support it: honestly mark "unverified: browser render" + give the user self-verification steps |
| 2★ | **Mark what's unverified** | Delivery says three things only: what was done / how it was verified (reproducible commands) / what wasn't verified. List each unverified item with its reason, don't just write "partially unverified"; unverified items must be **prominently marked** with asterisks or bold, not hidden in the middle of paragraphs |
| 3  | **Delivery claims match** | You say "did X" — is there actually X in the artifact? One last read-back of your own delivery claims before delivery, find each item in the artifact; if you can't find it, either do it or change it to "not done + reason" |
| 4  | **Switch paths after two failures** | On the 2nd consecutive failure of the same action, don't try the same method a 3rd time; first judge whether it's equivalent to a verified path, don't get stuck |
| 5  | **All-green isn't evidence** | Deliberately introduce the error you're guarding against, assertions going red counts as verification; if everything still passes after mutation = mutation didn't work. Minimal recipe: null/too long/invalid type/missing key. **Non-code artifacts**: click every link, cross-check numbers, really render visuals and record verification |
| 6  | **Recalculate key numbers** | Key numbers in data/research deliveries, independently recalculate or cross-source; if they don't match, recalculation wins |
| 7  | **Isolate temp files** | Temp files don't go in the delivery directory, clean up at the end; cleanup only touches this task's own directory, no global process killing |
| 8★ | **Anti-infinite-loop** | Read the same file 3 times with no new info = stop; same action 3 times in a row with identical output = switch approach |

---

## Multi-Agent

Details in `references/multi-agent.md` (read only when triggered), role card templates in `templates/`.

### Form 2 · Sub-agents (open proactively when there's clear benefit, don't wait for user to ask)

**Open when any of these hit**: completely independent subtasks / need to run two things in parallel / need independent critical perspective / worried intermediate process pollutes main context.  
When dispatching, make three things clear: **goal, completion criteria, who to report back to**. Iron rule: after sub-agent reports back, **the main agent is still the DRI**, must verify it yourself; sub-agents don't report directly to the user; if one person can do it coherently, don't open a second.

### Form 3 · Multi-agent (confirm with user first / cross-model / large task division)

Six steps: commander identity declaration → build character profiles → break subtasks and write task packages → user relays dispatch → verify against original goal (check for drift first, then have the critic pick apart) → report three-piece set to user.

**Task package seven elements**: background / decided decisions / open gaps / completion criteria / allowed and prohibited scope / unique DRI / who to report back to.

**Three role cards** (`templates/`): **Commander** defaults to DRI, delegation doesn't transfer final responsibility; **Executor** only says "done per spec, please review"; **Critic** independently picks apart, doesn't do the work themselves.

**Red lines**: Executor saying "I'm done" isn't acceptance; Critic doesn't modify work; doesn't bypass the commander to report directly.

---



## Field Tests

**Latest tests (2026-09-18 · v1.6.0) — delivery + creative single-arm (no B arm, only records behavior and completion tier):**

| Experiment | Conditions | Results |
|---|---|---|
| **Wuthering Waves damage calculator table** (data/delivery) | skill v1.6.0 · engine `damage_calc.py` 1:1 | in-page 21/21 + Python 15-item cross-check + mutation `792→793` red; **completion tier C1** (real-device reconciliation pending user) |
| **Star Catch** (creative mini-game) | v1.6.0 · A-tier direction card · quality budget ≤2 rounds | logic 24/24 (including mutation) + Chrome/click to start; **C1**, product tier not maxed |
| **3D Fishing / Neon Void** (creative game) | v1.5.5–1.6.0 discussion period | transcripts and artifacts show C1-style annotation + automated evidence; **C2 requires user playtest**; complete fishing source not in repo (transcript-level) |

> **1.6.0 framing**: Stage 5 pass = **C1 acceptable for acceptance**; "product is done" = **C2** (user or external scorecard). Execution side has no rules; creative segments can skip the skill, then attach acceptance. Evidence in the [`experiments` branch](https://github.com/JadeYingWah/gpt-series-reasoning-style/tree/experiments) `raw-materials/*2026-09-18/`.

**Controlled experiments (2026-09-17) — dual-arm, disk evidence + post-interview transcripts:**

| Experiment | With skill | Without skill | Who's better |
|---|---|---|---|
| **v1.5.1 · Phoebe retest** (unknown proper noun + from-scratch 2D game) | two rounds of search found "Phoebe" source → three questions to confirm → protagonist made it into the product | core word **silently dropped**, generic fishing game | **With skill clearly better** |
| **v1.5.2 · Q&A dual-arm** | search-verified + read VERSION + cited sources | same questions both arms got right | **Tie** → removed Q&A forced research |
| **v1.5.1 · Three-game collection** | A-tier confirmation → **exe direct-launch 3/3 playable** + unverified item automated closure | bat dependencies **2/3 don't open**, zero annotation | **With skill comprehensively better** |

> **One sentence**: clauses exist only for measured gaps; **C1/C2 separates "no fake completion" from "product is done well"**.

<details>
<summary><b>Historical experiment archive</b> (framing and old numbers, click for reference)</summary>

- Historical cumulative framing (don't mix):
  - **Narrative A/B rounds 233** (= heavy version line 207 + minimal line 26; one "task × arm × round" counts as one);
  - **experiments branch script count**: ≥ **286 arms / 53 batches** (regex-covered arm dirs, lower bound; ~3250 files total, including v1.2.x and pre-09-17 materials);
  - **2026-09-17**: 8 groups of desktop comparison/form beds (Phoebe / three-games×2 / 4399×2 / pomodoro / finance suite / three txts);
  - **2026-09-18**: 4 v1.6.0 test packs (WUWA calculator table, Star Catch, 3D fishing transcript, Neon Void evidence layer).
- Conclusion distilled: fewer rules is better, but the core few can't be missing; **C1/C2 separates honest completion from product satisfaction**.
- Harness has several local ab-* dirs, **not all in the experiments branch**, not counted in the public numbers above.
- Citable hard numbers (v1.2.x era controlled experiments): soft-dimension improvement **+20~24** (P1-5); counter-example verification execution rate **with skill 100% vs without skill 33%** (P1-1); self-calibration gap **100% → 33%** (P1-2).
- Raw experimental data (~70 MB / 3066+ files) is in the [`experiments` branch](https://github.com/JadeYingWah/gpt-series-reasoning-style/tree/experiments); the main repo only contains the skill itself.

</details>

---

## What It Is Not

This section lists **the limitations we've measured ourselves** — not modesty, but framing.

> **Version applicability**: items marked "**old**" were measured in the **v1.2.x era**. Hard metrics and bulky clauses were removed in the v1.4.x minimal line, so **these old conclusions no longer apply to the current 1.6.0**.

- **Doesn't improve reasoning ability**, and isn't GPT-specific — distilled from GPT series (including GPT-5.6 Sol, GPT-6 Astra), but applies to all instruction-following LLMs.
- **Doesn't improve code quality** — experiments consistently show: code itself barely differs, what improves is **delivery trustworthiness**.
- **Not an accelerator** — verification habits eat up about 30-40% of the time budget, in exchange for "dare to use directly" deliveries.
- **Not workflow kidnapping** — during execution the rule files aren't loaded at all, creation isn't interrupted; Q&A scenarios showed zero disruption in dual-arm tests. Light tasks are nearly invisible.
- **The base platform's model is already strong** — information Q&A both arms got full marks with no difference; three games the base platform could also make (though it lost the theme and two didn't open). The skill's value isn't making the model stronger, it's turning quality from luck into a guarantee: task core words aren't dropped (Phoebe comparison), delivery form is asked first (exe double-click direct launch), unverified items are honestly annotated and self-closed.

<details>
<summary><b>Historical experiment boundary archive</b> (v1.2.x era, doesn't apply now, click for reference)</summary>

Doesn't catch critical defects [old v1.2.2 / v1.2.5] — n=2 comparison: critical defect dimension showed no distinguishable gap between with and without skill, held-out slightly worse. Reverse results are also kept in the repo. The defense relies on evidence and independent re-verification, not clauses.

Adding clauses ≠ better [old v1.2.2 / v1.2.3-draft] — hard metrics brought no score improvement (58.17 vs 57.00, equivalent); the heavier v1.2.5 (179 lines/77 self-checks) was falsified and retired.

</details>

---

## Philosophy

- **Fewer rules is better, but the core few can't be missing** — historical A/B (233 rounds) + later measurements' final conclusion;
- **Creation is creation, review is review** — the entire reason for the remember/forget alternation;
- **Evidence over claims** — all-green isn't evidence, assertions going red is what counts as verified;
- **Responsibility doesn't transfer with delegation** — after sub-agent reports back, the main agent is still the DRI.

---

## Install

Two installation methods, corresponding to two loading modes (use multiple clients, install each separately, no conflicts):

- **Method 1 · Native Skill (recommended)**: put the folder in the client's skills directory, auto-discovered on startup via `SKILL.md` description and triggered by context.
- **Method 2 · AGENTS.md project instructions**: for clients that don't support skill auto-discovery but read project-root `AGENTS.md`, `cd` into the repo and AGENTS.md points to the loading.

### Method 1: Native Skill (auto-discovery)

Skills directories for each client (`<name>` = `gpt-series-reasoning-style`):

| Client | Personal (global, all projects) | Project-level (shared with team via repo) |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Cursor (2.4+) | `~/.cursor/skills/` | `.cursor/skills/` |
| Codex CLI | `~/.codex/skills/` | `.codex/skills/` (or `.agents/skills/`) |
| WorkBuddy | `~/.workbuddy/skills/` | — |
| Other SKILL.md-supporting clients | check their docs for skills directory | same |

> **One location feeds two clients**: Cursor will also load `.claude/skills/` and `~/.claude/skills/` (same for Codex dir). If using both Claude Code and Cursor, install into `~/.claude/skills/` and both work.

**macOS / Linux (bash)** — Claude Code personal level example:

```bash
git clone https://github.com/JadeYingWah/gpt-series-reasoning-style
mkdir -p ~/.claude/skills && cp -r gpt-series-reasoning-style ~/.claude/skills/
# Cursor: change target to ~/.cursor/skills/; Codex: ~/.codex/skills/; WorkBuddy: ~/.workbuddy/skills/
```

**Windows (PowerShell)**:

```powershell
git clone https://github.com/JadeYingWah/gpt-series-reasoning-style
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse -Force gpt-series-reasoning-style "$HOME\.claude\skills\"
# Cursor target "$HOME\.cursor\skills"; Codex "$HOME\.codex\skills"; WorkBuddy "$HOME\.workbuddy\skills"
```

**Project-level / team share**: put the folder in the project repo's `.claude/skills/` (or the corresponding client dir) and commit — teammates clone the repo and automatically get it, no separate install.

After install, **start a new session** (or restart the client) to discover the new skill.

### Method 2: AGENTS.md project instructions (cd-type)

For clients that don't do skill auto-discovery but read project-root `AGENTS.md` (Codex / Gemini CLI / Copilot CLI / Windsurf / Zed, etc.):

```bash
git clone https://github.com/JadeYingWah/gpt-series-reasoning-style
cd gpt-series-reasoning-style    # start the agent inside the repo dir, AGENTS.md entry point auto-applies
```

This isn't skill registration, it's the agent treating `AGENTS.md` as project instructions and following its lead to `SKILL.md` (gate) → `DISCIPLINE.md` (five stages) → read references as needed. If your client only reads specific filenames, add a symlink at the repo root pointing to `AGENTS.md` (e.g., `ln -s AGENTS.md CLAUDE.md`, `ln -s AGENTS.md GEMINI.md`; on Windows use `mklink` or just copy a file).

### Installation notes

- **Copy the whole folder, don't just copy `SKILL.md`** — `DISCIPLINE.md`, `references/`, `templates/`, `scripts/` are all loaded on demand; missing them breaks multi-agent scenarios.
- **The directory name must be `gpt-series-reasoning-style`**: downloaded ZIP extracts with `-main` / `-master` suffixes, rename it or some clients' discovery and slash invocation will break.
- **Zero dependencies, no network, no telemetry**: the whole thing is plain Markdown; only `scripts/selfcheck.py` repo self-check needs Python 3 (optional, skill works fine without Python).

### Update and verify

```bash
cd <skills dir>/gpt-series-reasoning-style && git pull    # version in VERSION file
python scripts/selfcheck.py    # optional: 38 static self-check items, exit code 0 = all pass
```

Verify it's installed: in a new session ask the agent "**What's your version? What files prove you're loaded? What are the five stages?**" — should answer `1.6.0`, state the gate chain (`SKILL.md` gate → **moment before** reading `DISCIPLINE.md`; moment before = earliest of writing deliverable / construction confirm / build command / announcing delivery) and five-stage timeline, and quote rule 1 verbatim; mention completion tiers **C1 acceptable / C2 product satisfaction** (C2 requires user or external recognition).

## Usage

- **Auto-trigger** (determined by `SKILL.md` description): tasks involving numeric verification, code delivery, multi-agent collaboration, need to prevent fake completion; or user says "done, help me check / see if it's right / accept it"; or dispatching subtasks, multiple AI division of labor. Constrains whether delivery is real, **doesn't set creative quality satisfaction standards on its own** (see DISCIPLINE completion tiers).
- **Explicitly named**: `Use gpt-series-reasoning-style for this task.`
- **Don't load**: one-sentence Q&A, pure chat, small and reversible changes — discipline doesn't belong where it's not needed.
- **Creative task usage**: to raise the product ceiling, **creative/implementation segments can skip this skill**, attach acceptance after finishing (really open + C1/C2); gates and polishing budgets stay out of the creative space, that's how zero-friction works.

## Cost

| Item | Measured value |
| ---- | -------------- |
| `SKILL.md` | **3594 bytes / 35 lines** (~0.6k token resident) — **pure gate**, full discipline in `DISCIPLINE.md` (3862 bytes / 33 lines, read only the moment before action) |
| Stage 2 on-demand | `references/plan-rules.md` (6162 bytes) — only read in the planning stage |
| Stage 5 on-demand | `references/review-rules.md` (5041 bytes) — only read in the discipline check stage |
| Multi-agent on-demand | `references/multi-agent.md` (5718 bytes) — only loaded when adding form 2/3 |
| Loading path | normally only reads `SKILL.md` (35-line gate) + `VERSION`; **moment before action/answer** reads `DISCIPLINE.md` (full discipline); stage 2 reads plan-rules, stage 5 reads review-rules, multi-agent scenarios additionally read `multi-agent.md`; **rule content all forgotten after task ends** |
| Peak resident text | at any moment, rule text in context is at most one copy (planning or review, never both present) |

**Compared to v1.2.5 heavy version**: 38.7 KB / 179 lines / ~12k token — experimentally proven to be the worse choice (see "Field Tests").


## What's Inside

| File | Role |
| ---- | ---- |
| `SKILL.md` | **Gate** (35 lines). No discipline text; "moment before" actionized + creative ideation exception |
| `DISCIPLINE.md` | **Full discipline** (33 lines). Five stages + **completion tiers C1/C2** + post-task forgetting + boundaries + loading rules |
| `references/plan-rules.md` | **Stage 2 only**: planning rules (ideation substantive preservation, form judgment, A-tier doesn't cap quality, creative quality budget) |
| `references/review-rules.md` | **Stage 5 only**: 8 rules (★ three light-task-mandatory) + **item 9 completion tier** + exit conditions |
| `references/multi-agent.md` | Form 2/3 details: trigger signals, dispatch norms, six-step operations, red lines |
| `AGENTS.md` | Cross-runtime entry routing (Codex / Gemini CLI etc.), pointer only, no rules |
| `templates/` | Commander / Executor / Critic three role cards + task package seven elements |
| `scripts/selfcheck.py` | Repo consistency self-check (**38 items**, read-only, adapted to file-level progressive loading) |
| `SECURITY.md` | Security model explanation |
| `assets/social-preview.svg / .png` | Repo banner (1280×640) |

## Version

Current version: **1.6.0**

- **v1.6.0**: rewritten manual (REFERENCE.md); coexistence rules refined; document consistency aligned; .gitattributes adjusted (Python/YAML counted in Languages);
- **v1.5.8**: creative tasks can skip stage 2 directly (unknown proper nouns searched first then ask user to confirm);
- **v1.5.7**: coexistence rules (only intervenes at stage 2/5); B-tier hard cap (max 1 proper-noun question unless user asks for item-by-item); vertical slice priority (playable slice immediately after A-tier); fixed SKILL.md encoding garble;
- **v1.5.5**: SKILL.md gated, full discipline moved into DISCIPLINE.md (physical isolation);
- **v1.4.x minimal line**: five-stage timeline, file-level progressive loading — the mainline predecessor;
- **v1.2.x heavy line**: 179 lines, module matrix, self-test frozen 77 items — **experimentally falsified**, this line is retired.

**Usage principle (1.6.0)**: no rules on execution side; creative segments can skip the skill before acceptance if zero-friction is desired; major versions (≥1.6) require commander to proactively bring it up.

## License

MIT
