# External Reviews 5–7 — Verification Verdict / 三份外部全面复查的核验结论

- Date: 2026-09-10
- Provenance: three independent full-project audits of this skill, produced by
  external AIs and relayed by the maintainer (方法二). Model identities were not
  disclosed by the relays. One of them wrote its own report file
  (`2026-09-10-deep-audit.md`, same directory); the other two exist as relayed
  text only — their claims are archived here as verified by us, not verbatim.
- Verification method: every load-bearing claim was re-checked on disk or
  against the GitHub API before being believed. Claims we could not check are
  listed as UNVERIFIED, not silently accepted.

## P0 — all three CONFIRMED, all three fixed (batch 22)

| # | Claim | Verdict | Evidence | Fix |
| --- | --- | --- | --- | --- |
| P0-1 | CI has never been green; the skilllint step fails and the three validation steps after it are always skipped | **CONFIRMED** | GitHub API: 7/7 runs `failure`; step-level for run 34459210405 → step 6 `Official skilllint` = failure, steps 7 (openai.yaml parses) / 8 (Probe scenarios parse) / 9 (Self-test sheet parses) = **skipped**. Two root causes verified by inspection: the workflow has no `setup-uv` step, and `check gpt-series-reasoning-style` is a path that does not exist relative to the CI checkout (repo root = working dir); locally it only works because we run it from the parent directory | `.github/workflows/selfcheck.yml`: added `astral-sh/setup-uv@20cfd1bf…` (SHA-pinned v10.0.1) and changed the lint step to `cd .. && uvx skilllint@1.19.2 check gpt-series-reasoning-style`. Locally reproduced both forms: parent-dir form passes clean; `check .` reproduces the FM010 false positive named in the pin comment |
| P0-2 | Resume Check is 7 items in the authority file but only 3–4 on the must-load and acceptance surfaces | **CONFIRMED** | `series-reasoning-workflow.md` Resume Check = 7 items; `SKILL.md` workflow item 1 = 4; `README.md` EN line 100 and CN line 106 = 3; `self-test.md` Test 55 = 4. The two missing items (re-anchor the original instruction; project-root hard check) are exactly the fixes for the two most expensive defects the A/B rounds caught | `SKILL.md` now enumerates ①–⑦; both README lines carry all 7; Test 55 gained two expectations (re-anchor; project-root hard check) |
| P0-3 | The load-proof template in examples.md contradicts itself within four lines | **CONFIRMED** | `series-reasoning-examples.md` ~L470: announces 「一条主干 + 两个按需扩展」 then enumerates `1. 单 Agent 模式 / 2. 子 Agent 模式 / 3. 指挥官多 Agent 模式` and refers to 模式一/二/三 — the retired three-mode vocabulary, inside a template hosts are told to reproduce | Template rewritten as 主干 / 扩展 A / 扩展 B with the current vocabulary |

## P1 — CONFIRMED and fixed in the same batch

| Claim | Verdict | Evidence | Fix |
| --- | --- | --- | --- |
| README Maintainer Notes still says 22 identity files; SB19 cannot catch that form | **CONFIRMED — and it is a blind spot in our own SB19** | `README.md:465`: 「内置身份 **22** 个文件（21 类角色）」 while SB4 counts 21 files. Our SB19 regex only matches 个/类 followed by 身份/角色/契约, so `22 个**文件**` (bold breaks the phrase) and the EN number-after-noun form (`identity files **22**`) both slip through | README 22→21 (both languages); SB19 gained file-count forms for CN and EN with the count allowed on either side of the noun, gated on the line mentioning identity + files. RED proof executed against the pre-fix README: both drift forms caught |

## Verified FALSE / stale

| Claim | Verdict | Evidence |
| --- | --- | --- |
| 「docs/selftest-run 应入 .gitignore」(deep-audit C6) | **FALSE** — already ignored since batch 12 | `.gitignore` line 8: `docs/selftest-run/` |

## Verified TRUE but not yet fixed (queued, maintainer's call)

- `claim-check.py` runs untrusted commands with `shell=True`; the destructive-command
  blacklist does not cover interpreter-indirect execution (`python -c "import os;…"`,
  `python malicious.py`), so a hostile claims file still reaches local RCE. Confirmed by
  reading `DANGEROUS_RES` (19 patterns, no python form). The tool documents that it is not
  a sandbox and has `--allow-dangerous`; the gap is real nevertheless. Candidate fix:
  default to `shell=False` with an argv parser, or require `--allow-dangerous` for any
  command that is not a small allowlist.
- `README.md:395` states 「实测中文字符占比 1.5–1.8×英文词」 — the wording claims a
  measurement, but no archived measurement artifact was found. Either archive the
  measurement or soften the wording to an estimate.
- Test 37's self-contradiction (previously archived as C2, "待裁决") remains open.
- deputy-commander placement (README Core vs Optional vs commander-roles) needs a
  three-way re-read before touching.

## NOT YET VERIFIED (listed for the next pass — no verdict, no fix)

The deep-audit report's remaining items (B1–B5, C1–C5, D1–D5, E1–E2, F1–F3) and the
second report's P2 list (23-field token-vs-field-set checking, SemVer communication,
probe fail_patterns being dead data, installer `--dry-run`) have **not** been verified
by us yet. They are neither accepted nor rejected; the next verification pass should
take them one by one, and anything confirmed lands with the same
real-defect-evidence bar the SB checks require.
