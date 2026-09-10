#!/usr/bin/env python3
"""Static self-check for the gpt-series-reasoning-style skill.

The 77 behavioural self-tests are prompt->expected descriptions that only
genuinely pass when a host model decides to follow them. This tool does NOT
verify rule semantics. It verifies what a machine *can* verify cheaply and
honestly: version/numbering consistency, structural completeness, cross-file
references, code-fence pairing, identity/reference counts, gate-field surface
sync, and the install-platform parameter set. Running it is a fast regression
check that the repo has not silently drifted.

Python 3.7+ stdlib only. Exit: 0=all passed, 1=failed, 2=usage.

Known blind spots (literal-layer checks only, documented by design after the
2026-09-10 external reviews): semantic drift; per-item bilingual parity
(incl. identities/); cross-file field-set unions; claims-vs-reality gaps
(use claim-check.py); install.sh parity; per-round ledger fields. Green
means the literal layer is intact — nothing more.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os.path
import pathlib
import re
import sys

import _selftest_parser

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FENCE_RE = re.compile(r"^```")


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


class Check:
    def __init__(self, code: str, title: str):
        self.code = code
        self.title = title
        self.ok = False
        self.detail = ""

    def pass_(self, detail: str = ""):
        self.ok = True
        self.detail = detail

    def fail(self, detail: str):
        self.ok = False
        self.detail = detail

    def line(self) -> str:
        flag = "PASS" if self.ok else "FAIL"
        return f"[{flag}] {self.code} {self.title} -- {self.detail}"


def run_checks() -> list:
    checks = []

    def new(code, title):
        c = Check("SB" + str(code), title)
        checks.append(c)
        return c

    # SB1 version consistency
    c = new(1, "version consistency")
    version = read_text(REPO_ROOT / "VERSION").strip()
    skill_text = read_text(REPO_ROOT / "SKILL.md")
    readme = read_text(REPO_ROOT / "README.md")
    selftest = read_text(REPO_ROOT / "references" / "self-test.md")
    if not re.search(r"Current version: " + re.escape(version), skill_text):
        c.fail("SKILL.md does not declare current version " + version)
    elif re.search(re.escape(version), selftest) is None:
        c.fail("self-test.md does not reference version " + version)
    elif re.search(r"version-" + re.escape(version), readme) is None:
        c.fail("README badge does not show version-" + version)
    else:
        residue = []
        for name, text in (("SKILL.md", skill_text), ("README.md", readme),
                           ("self-test.md", selftest)):
            if re.search(r"\b3\.2\.[0-9]\b", text):
                residue.append(name)
        if residue:
            c.fail("stale 3.2.x residue in: " + ", ".join(residue))
        else:
            c.pass_("all surfaces agree on " + version + "; no 3.2.x residue")

    # Shared parse (M1: single parser for self-test.md — selfcheck and
    # selftest-runner.py must never disagree on the format).
    cases, malformed_headers = _selftest_parser.parse(selftest)

    # SB2 self-test numbering contiguous
    c = new(2, "self-test numbering 1..N")
    nums = [c["num"] for c in cases]
    if not cases:
        c.fail("self-test.md contains no Test blocks")
    elif malformed_headers:
        c.fail("malformed Test headers (hidden from numbering): "
               + "; ".join(malformed_headers[:3]))
    elif len(nums) != len(set(nums)):
        c.fail("duplicate Test numbers")
    elif nums != list(range(1, len(nums) + 1)):
        c.fail("numbering not contiguous 1.." + str(len(nums)))
    else:
        c.pass_("contiguous Test 1.." + str(len(nums)) + " (" + str(len(nums)) + " tests)")

    # SB3 structural completeness
    c = new(3, "self-test structural completeness")
    missing = []
    if not cases:
        c.fail("self-test.md contains no test blocks")
    else:
        for case in cases:
            raw = case["raw"]
            name = "Test {}: {}".format(case["num"], case["title"])
            # case-insensitive (L2): format drift to lowercase must not slip past
            has_prompt = ("prompt" in raw.lower()) and ("```" in raw)
            low = raw.lower()
            has_expected = ("expected" in low or "期望" in raw) and bool(re.search(r"^- ", raw, re.M))
            if not (has_prompt and has_expected):
                missing.append(name)
        if missing:
            c.fail("tests lacking prompt or expectation: " + ", ".join(missing[:6]))
        else:
            c.pass_("all " + str(len(cases)) + " test blocks complete")

    # SB4 identity count == 21
    c = new(4, "identity file count == 21")
    idir = REPO_ROOT / "identities"
    names = {p.name for p in idir.glob("*.md")}
    names.discard("_template.md"); names.discard("README.md")
    if len(names) != 21:
        c.fail("found " + str(len(names)) + " identity files, expected 21")
    else:
        c.pass_("21 identity files present")

    # SB5 references count == 13
    # (11 originals + series-reasoning-workflow-en.md mirror + project-artifacts.md)
    c = new(5, "reference file count == 13")
    refs = list((REPO_ROOT / "references").glob("*.md"))
    if len(refs) != 13:
        c.fail("found " + str(len(refs)) + " reference files, expected 13")
    else:
        c.pass_("13 reference .md files")

    # SB6 code-fence pairing (+ escaped-fence detection, A2: a backslash-escaped
    # fence is invisible to the parser and silently drops content from tooling)
    c = new(6, "markdown code-fence pairing")
    bad = []
    escaped = []
    # Backslash-escaped fence (no regex: multi-layer escaping proved error-prone)
    backslash_fence = chr(92) + chr(96) * 3
    for p in sorted(REPO_ROOT.rglob("*.md")):
        if ".git" in p.parts:
            continue
        raw_lines = p.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(raw_lines, 1):
            if line.lstrip().startswith(backslash_fence):
                escaped.append("{}:{}".format(p.relative_to(REPO_ROOT), idx))
        n = sum(1 for line in raw_lines if FENCE_RE.match(line))
        if n % 2 != 0:
            bad.append(str(p.relative_to(REPO_ROOT)) + " (" + str(n) + ")")
    if escaped:
        bad.append("escaped fences (invisible to parser): " + ", ".join(escaped[:4]))
    if bad:
        c.fail("unpaired fences: " + "; ".join(bad))
    else:
        c.pass_("all markdown fences paired")

    # SB7 cross-file references exist
    c = new(7, "cross-file reference existence")
    missing_refs = set()
    root = REPO_ROOT / "references"
    for m in re.findall(r"references/([\w\-.]+?\.md)", selftest):
        if not (root / m).exists():
            missing_refs.add(m)
    for m in re.findall(r"identities/([\w\-.]+?\.md)", selftest):
        if not (REPO_ROOT / "identities" / m).exists():
            missing_refs.add("identities/" + m)
    if missing_refs:
        c.fail("missing referenced files: " + ", ".join(sorted(missing_refs)))
    else:
        c.pass_("all referenced reference/identity files exist")

    # SB8 authoritative field counts
    c = new(8, "authoritative field counts consistent")
    live = "\n".join([skill_text, readme, selftest])
    leaked = []
    if re.findall(r"24\s*字段|24-field", live):
        leaked.append("24-field mention in live surfaces")
    if not re.search(r"23\s*字段|23[- ]field", live):
        leaked.append("no 23-field mention")
    if not re.search(r"6\s*字段|six[- ]field|6-field", live):
        leaked.append("no 6-field mini package mention")
    if leaked:
        c.fail("; ".join(leaked))
    else:
        c.pass_("23-field/6-field present; no 24-field leak in live surfaces")

    # SB9 gate-field surface sync
    c = new(9, "gate-field surface sync")
    oai = read_text(REPO_ROOT / "agents" / "openai.yaml")
    missing_tokens = []
    for tk in ["风险分档", "形态选择", "已盘点可用资源", "最高影响问题", "需要你确认", "宿主对齐"]:
        if tk not in skill_text:
            missing_tokens.append("SKILL.md:" + tk)
        if tk not in readme:
            missing_tokens.append("README:" + tk)
    for tk in ["form selection", "risk tier", "surveyed"]:
        if tk not in oai:
            missing_tokens.append("openai.yaml:" + tk)
    if missing_tokens:
        c.fail("missing gate tokens: " + ", ".join(missing_tokens))
    else:
        c.pass_("CN gate tokens + EN tokens synced across surfaces")

    # SB10 install platform parameter set
    c = new(10, "install platform parameter set")
    try:
        ps1 = read_text(REPO_ROOT / "scripts" / "install.ps1")
    except FileNotFoundError:
        # Do NOT return early: skipping SB11-SB17 would silently shrink the
        # reported total and mask seven checks as "not applicable". Fail this
        # check and let the remaining checks run (each guards its own I/O).
        c.fail("scripts/install.ps1 missing")
    else:
        keys = set(re.findall(r"^\s+(\w+)\s+= Join-Path", ps1, flags=re.M))
        required = {"agents", "codex", "claude", "cursor", "windsurf", "cline",
                    "gemini", "kiro", "trae", "goose", "opencode", "roo", "antigravity"}
        diff = required - keys
        if diff:
            c.fail("install.ps1 missing platform keys: " + ", ".join(sorted(diff)))
        elif len(keys) < 13:
            c.fail("expected >=13 platform keys, found " + str(len(keys)))
        else:
            c.pass_("install.ps1 covers " + str(len(keys)) + " platform keys")

    # SB11 light-channel exclusion boundary cross-surface sync
    c = new(11, "light-channel exclusion boundary sync")
    surf = {
        "SKILL.md": "从零新建产物默认中档",
        "references/series-reasoning-workflow.md": "从零新建产物默认中档",
        "references/agent-modes.md": "从零新建产物未完整指定",
        "README.md": "全新产物默认中档",
        "agents/openai.yaml": "fully specifies type, location, and form",
        "docs/minimal-discipline.md": "完整指定类型/位置/形态",
        "references/self-test.md": "multi-deliverable",
    }
    miss = []
    for rel, tk in surf.items():
        try:
            txt = read_text(REPO_ROOT / rel)
        except FileNotFoundError:
            miss.append(rel + ":MISSING")
            continue
        if tk not in txt:
            miss.append(rel + ":" + tk)
    if miss:
        c.fail("light-channel boundary token missing: " + "; ".join(miss))
    else:
        c.pass_("new-from-scratch boundary + exclusions present on all 7 surfaces")

    # SB12 agentskills.io spec compliance (machine-checkable subset)
    c = new(12, "agentskills.io spec compliance")
    issues = []
    m = re.match(r"^---\s*\nname:\s*([^\s]+)\s*\n", skill_text)
    name = m.group(1) if m else ""
    if name != REPO_ROOT.name:
        issues.append("name != directory name: " + name)
    if not re.match(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$", name):
        issues.append("name format invalid: " + name)
    md = re.search(r"^description:\s*(.+)$", skill_text, flags=re.M)
    desc = md.group(1).strip().strip("\"'") if md else ""
    if not desc:
        issues.append("description missing")
    elif len(desc) > 1024:
        issues.append("description > 1024 chars: " + str(len(desc)))
    body = skill_text.split("---", 2)[2] if skill_text.startswith("---") else skill_text
    nlines = body.count("\n") + 1
    if nlines > 500:
        issues.append("SKILL.md body > 500 lines: " + str(nlines))
    if issues:
        c.fail("; ".join(issues))
    else:
        c.pass_("name/description/body within spec (desc=" + str(len(desc)) +
                " chars, body=" + str(nlines) + " lines)")

    # SB13 probe scenario registry consistent
    c = new(13, "probe scenario registry consistent")
    pj = REPO_ROOT / "probes" / "probe-scenarios.json"
    try:
        reg = json.loads(read_text(pj))
    except Exception as exc:  # noqa: BLE001 - machine-truth any parse failure
        c.fail("probe-scenarios.json unreadable: " + str(exc))
    else:
        scen = reg.get("scenarios", [])
        ids = [s.get("id") for s in scen]
        docs = read_text(REPO_ROOT / "docs" / "field-tests" / "field-test-2-probe-series.md")
        rounds = ["第一轮", "第二轮", "第三轮"]
        prob = []
        if not scen:
            prob.append("no scenarios")
        if sorted(ids) != ["P1", "P2", "P3"]:
            prob.append("ids != P1/P2/P3: " + str(ids))
        if not reg.get("probe_prompt"):
            prob.append("probe_prompt missing")
        for r in rounds:
            if r not in docs:
                prob.append("field-test-2 missing round " + r)
        if prob:
            c.fail("; ".join(prob))
        else:
            c.pass_("3 probe scenarios (P1/P2/P3) + prompt; field-test-2 documents all 3 rounds")

    # SB14 language-policy declaration anchored in README + layers exist
    c = new(14, "language-policy declaration synced")
    if "## Language Policy / 语言策略" not in readme:
        c.fail("README language-policy section missing")
    elif not re.search(r"分层双语", readme) or not re.search(r"layered bilingual", readme):
        c.fail("language-policy wording drifted (need 分层双语 + layered bilingual)")
    else:
        layers = [
            "references/series-reasoning-workflow.md",
            "references/series-reasoning-examples.md",
            "references/project-policy-template.md",
            "references/agent-modes.md",
            "docs/minimal-discipline.md",
        ]
        missed = [r for r in layers if not (REPO_ROOT / r).exists()]
        if missed:
            c.fail("matrix-listed layer files missing: " + ", ".join(missed))
        else:
            c.pass_("language policy declared (中文主导 / CN-primary); matrix layer files present")

    # SB15 self-test prompt uniqueness
    c = new(15, "self-test prompt uniqueness")
    seen = {}
    dup = []
    for case in cases:
        pp = case["text_prompt"]
        if not pp:
            continue
        if pp in seen:
            dup.append("Test " + seen[pp] + " & Test " + str(case["num"]))
        else:
            seen[pp] = str(case["num"])
    if dup:
        c.fail("duplicated prompts: " + "; ".join(dup[:6]))
    else:
        c.pass_("all " + str(len(seen)) + " non-empty prompts distinct")

    # SB16 bilingual coverage — tiered. Tier A (rule surfaces loaded by every
    # session) must stay bilingual; tier B (long-form reference docs) is
    # informational only — forcing full bilingual on 500+ line docs would either
    # stay red forever or double file size (see README Complexity Budget).
    c = new(16, "bilingual section coverage (tiered)")

    def _collect_bilingual_gaps(rel):
        gaps = []
        p = REPO_ROOT / rel
        if not p.exists():
            return gaps
        txt = read_text(p)
        parts = re.split(r"(?m)^(#{1,4}[ \t]+.*)$", txt)
        for i in range(1, len(parts), 2):
            title = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            zh = sum(1 for ch in body if chr(0x4e00) <= ch <= chr(0x9fff))
            en = len(re.findall(r"[A-Za-z]{3,}", body))
            if zh + en < 40:
                continue
            if en == 0:
                gaps.append("{} :: {} (纯中文{}字/无英文)".format(rel, title, zh))
            elif zh / max(en, 1) > 4:
                gaps.append("{} :: {} (中{}/英{})".format(rel, title, zh, en))
            elif en / max(zh, 1) > 4:
                gaps.append("{} :: {} (英{}/中{})".format(rel, title, en, zh))
        return gaps

    tier_a = [
        "references/multi-agent-closure-rules.md",
        "references/agent-modes.md",
    ]
    tier_b = [
        "references/series-reasoning-workflow.md",
    ]
    gaps_a, gaps_b = [], []
    # SKILL.md is Chinese-primary by design (language policy); bilingual sections
    # were moved down to the references (EN sections) to halve the always-loaded
    # cost. Only an English entry pointer is required here.
    if "Complete English rules live" not in skill_text:
        gaps_a.append("SKILL.md :: English entry pointer missing (see language policy)")
    for rel in tier_a:
        gaps_a.extend(_collect_bilingual_gaps(rel))
    for rel in tier_b:
        gaps_b.extend(_collect_bilingual_gaps(rel))
    if gaps_a:
        c.fail("tier-A bilingual gaps ({}): ".format(len(gaps_a)) + "; ".join(gaps_a[:6]))
    elif gaps_b:
        c.pass_("tier-A rule surfaces bilingual OK; tier-B long-form docs carry "
                + str(len(gaps_b)) + " informational gaps (not force-translated)")
    else:
        c.pass_("all rule-layer sections carry both languages")

    # SB17 AGENTS.md cross-runtime entry consistency (C4-1: the new surface
    # must stay aligned with SKILL.md or it drifts unguarded).
    c = new(17, "AGENTS.md entry consistency")
    ag_path = REPO_ROOT / "AGENTS.md"
    if not ag_path.exists():
        c.fail("AGENTS.md missing (cross-runtime entry alias expected at repo root)")
    else:
        ag = read_text(ag_path)
        problems = []
        if "SKILL.md" not in ag or "VERSION" not in ag:
            problems.append("does not route to SKILL.md/VERSION")
        if "宣布阶段序列不是确认。" not in ag:
            problems.append("quoted first hard rule missing/drifted")
        if "gpt-series-reasoning-style" not in ag:
            problems.append("skill name missing")
        for m in re.findall(r"references/([\w\-.]+\.md)", ag):
            if not (REPO_ROOT / "references" / m).exists():
                problems.append("routes to missing file references/" + m)
        if problems:
            c.fail("; ".join(problems))
        else:
            c.pass_("AGENTS.md routes to SKILL.md/VERSION; hard-rule quote intact; routed files exist")

    # SB18 forbidden-authorization-phrase parity (evidence: P0-4, a real 2026-09-10
    # external-review finding — the CN authority workflow.md lagged its EN mirror and
    # SKILL.md on the third phrase). The three phrases must appear on all three
    # hard-rule surfaces; the check cannot judge semantics, only presence parity.
    c = new(18, "forbidden-authorization-phrase parity")
    phrases = ["开始", "现在开始", "直接做"]
    surfaces = {
        "SKILL.md": skill_text,
        "references/series-reasoning-workflow.md": read_text(REPO_ROOT / "references" / "series-reasoning-workflow.md"),
        "references/series-reasoning-workflow-en.md": read_text(REPO_ROOT / "references" / "series-reasoning-workflow-en.md"),
    }
    missing_phrases = []
    for rel, txt in surfaces.items():
        for ph in phrases:
            if ph == "直接做":
                if "直接做" not in txt:
                    missing_phrases.append(rel + ":" + ph)
            else:
                if ('"' + ph + '"') not in txt and ("\u201c" + ph + "\u201d") not in txt:
                    missing_phrases.append(rel + ":" + ph)
    if missing_phrases:
        c.fail("forbidden phrases missing on: " + ", ".join(missing_phrases))
    else:
        c.pass_("开始/现在开始/直接做 present on SKILL.md + workflow CN/EN")

    # SB19 identity-count prose consistency across surfaces (evidence: commit
    # 9d32cbb — the qa-engineer/test-engineer merge updated SB4 and two README
    # spots but left five prose surfaces still saying "22 个身份"; SB4 only counts
    # FILES, so the prose drift was invisible to every check we had).
    # Admitted under README's own rule for a 19th check: it demonstrates a real
    # defect with an identifiable commit hash.
    # It scans an explicit allowlist of LIVE surfaces. Deliberately excluded:
    # CHANGELOG.md / INTERNAL-HISTORY.md / docs/reviews/ / docs/field-tests/
    # (dated records — a past count is correct for its date) and
    # docs/selftest-run/ (generated per run, not repo content).
    c = new(19, "identity-count prose consistency")
    expected_ids = 21
    id_surfaces = [
        "SKILL.md", "README.md", "AGENTS.md", "agents/openai.yaml",
        "identities/README.md", "docs/minimal-discipline.md", "site/index.html",
    ] + sorted(
        p.relative_to(REPO_ROOT).as_posix()
        for p in (REPO_ROOT / "references").glob("*.md")
    )
    id_cn = re.compile(r"(\d+)\s*(?:个|类)(?:内置)?(?:身份|角色|契约)")
    id_ctx = re.compile(r"(?:当前|全部|至全部)\s*(\d+)\s*个")
    id_ctx_guard = "内置身份"
    id_en = re.compile(r"(\d+)\s+(?:built-in\s+)?(?:identities|roles)\b")
    id_bad = []
    for rel in id_surfaces:
        p = REPO_ROOT / rel
        if not p.exists():
            id_bad.append(rel + ": missing (surface listed for the count check)")
            continue
        for ln, line in enumerate(read_text(p).splitlines(), 1):
            found = set()
            for rx in (id_cn, id_en):
                for m in rx.finditer(line):
                    if int(m.group(1)) != expected_ids:
                        found.add(m.group(0))
            # The catalog size is often stated apart from the noun
            # ("（当前 22 个，硬编码必然漂移）"). Only apply this second form on a
            # line that also says 内置身份 -- a bare "共 N 个角色" is legitimate
            # prose and must not trip the check.
            if id_ctx_guard in line:
                for m in id_ctx.finditer(line):
                    if int(m.group(1)) != expected_ids:
                        found.add(m.group(0))
            for f in sorted(found):
                id_bad.append("{}:{}: {}".format(rel, ln, f))
    if id_bad:
        c.fail("identity count != {} on: {}".format(expected_ids, "; ".join(id_bad[:8])))
    else:
        c.pass_("all {} live surfaces state {} identities".format(len(id_surfaces), expected_ids))

    return checks


def _write_report(args, lines: list) -> None:
    """Write the report inside the repository only (C1-3 guard).

    `--out` is an in-repo convenience; absolute paths or `..` traversal would
    let a typo drop the report anywhere on disk.
    """
    if pathlib.Path(args.out).is_absolute():
        print("ERROR: --out must be a repo-relative path, got: " + args.out)
        raise SystemExit(2)
    dest = (REPO_ROOT / args.out)
    resolved_root = REPO_ROOT.resolve()
    resolved = dest.resolve()
    rel = os.path.relpath(str(resolved), str(resolved_root))
    if rel == ".." or rel.startswith(".." + os.sep):
        print("ERROR: --out escapes the repository: " + args.out)
        raise SystemExit(2)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("\nreport written: " + str(dest))


def main() -> int:
    ap = argparse.ArgumentParser(description="Static self-check")
    ap.add_argument("--out", help="write a markdown report to this path")
    ap.add_argument("--label", default="local", help="tag for the report")
    args = ap.parse_args()

    try:
        checks = run_checks()
    except (OSError, UnicodeDecodeError) as exc:
        # Environment-level failure (missing/undecodable core file): report a
        # structured failure instead of a traceback. Genuine code bugs are NOT
        # swallowed — unexpected exception types still surface loudly.
        print("[FAIL] SB0 environment error -- " + str(exc))
        print("Static selfcheck aborted: core file missing or undecodable (see SB0 above).")
        return 1

    lines = [c.line() for c in checks]
    passed = sum(1 for c in checks if c.ok)
    total = len(checks)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fingerprint = hashlib.sha1("\n".join(lines).encode("utf-8")).hexdigest()[:12]
    summary = ("Static selfcheck {}/{} passed (label={} ts={} fingerprint={})"
               .format(passed, total, args.label, stamp, fingerprint))

    out_lines = [
        "# Static Self-Check Report / 静态自检报告", "",
        "- Label / 标签: `{}`".format(args.label),
        "- Time / 时间 (UTC): `{}`".format(stamp),
        "- Result / 结果: `{}/{}` passed".format(passed, total),
        "- Fingerprint / 指纹: `{}`".format(fingerprint), "",
        "```text", *lines, summary, "```", "",
    ]
    print("\n".join(out_lines))

    if args.out:
        _write_report(args, out_lines)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())