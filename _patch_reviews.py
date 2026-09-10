"""One-shot patch: land all verified findings from the two external reviews."""
import pathlib
import re

ROOT = pathlib.Path(".")
done, failed = [], []


def patch(path, old, new, name, count=1):
    p = ROOT / path
    t = p.read_text(encoding="utf-8")
    if old not in t:
        failed.append((name, path, "anchor not found"))
        return
    t = t.replace(old, new, count)
    p.write_text(t, encoding="utf-8", newline="\n")
    done.append(name)


def rpatch(path, pattern, repl, name, flags=0):
    p = ROOT / path
    t = p.read_text(encoding="utf-8")
    t2, n = re.subn(pattern, repl, t, count=1, flags=flags)
    if n == 0:
        failed.append((name, path, "regex not matched"))
        return
    p.write_text(t2, encoding="utf-8", newline="\n")
    done.append(name)


# ── MED-1 / 豆包 L1: SB16 -> SB17 stale budget wording ──
patch("README.md",
      "- **静态检查上限 16 项（SB1–SB16）**：新增第 17 项前，必须先证明它抓到过至少一个真实缺陷（可指认提交哈希）；抓不到就不加。",
      "- **静态检查当前 17 项（SB1–SB17）**：新增第 18 项前，必须先证明它抓到过至少一个真实缺陷（可指认提交哈希）；抓不到就不加。",
      "MED-1 README L409")
rpatch("site/index.html",
       r"SB1–SB16</code></td><td>版本一致性、门禁字段多表面同步、结构完整性等；新增第 17 项须先证明抓到过真实缺陷",
       "SB1–SB17</code></td><td>版本一致性、门禁字段多表面同步、结构完整性等；新增第 18 项须先证明抓到过真实缺陷",
       "MED-1 site L91")

# ── MED-2: SKILL.md 形态撞义 ──
patch("SKILL.md",
      "仅当指令已完整指定产物类型、位置与形态时才可走轻通道",
      "仅当指令已完整指定产物类型、位置与产品形态时才可走轻通道",
      "MED-2 SKILL L74")
patch("SKILL.md",
      "除非指令已完整指定产物类型、位置与形态，否则不得走轻通道",
      "除非指令已完整指定产物类型、位置与产品形态，否则不得走轻通道",
      "MED-2 SKILL L75")

# ── MED-3: 迷你包 T3 缺位（agent-modes CN+EN）──
patch("references/agent-modes.md",
      "6. **信任层级**：T1 只读 / T2 可写产物。",
      "6. **信任层级**：T1 只读 / T2 可写产物。T3（命令/部署/破坏性或外部操作）属指挥官扩展（23 字段包）场景——子 Agent 迷你包限 T1/T2。",
      "MED-3 agent-modes CN")
patch("references/agent-modes.md",
      "6. **Trust tier**: T1 read-only / T2 artifact writes.",
      "6. **Trust tier**: T1 read-only / T2 artifact writes. T3 (commands, deployments, destructive/external) belongs to the Commander extension's 23-field package; subagent mini packages are limited to T1/T2.",
      "MED-3 agent-modes EN")

# ── M1(豆包): openai.yaml 并行对冲 ──
patch("agents/openai.yaml",
      "point to Subagent)",
      "point to Subagent only when parallel payoff beats briefing cost (evaluate first; fall back to the Single-Agent backbone otherwise))",
      "M1 openai.yaml hedge")

# ── M2(豆包): 身份层声明贴合实际 ──
patch("README.md",
      "| 身份 identities/ | 22 个角色契约 | 逐段双语 EN+CN |",
      "| 身份 identities/ | 22 个角色契约 | 身份定位节双语（EN+CN）；契约正文英文为主 |",
      "M2a language-policy row")
patch("README.md",
      "each following the same 8-section contract: **Identity · Mission · Responsibilities · Process · Required Output · Handoff · Boundaries · Anti-Patterns**.",
      "each following the same 8-section contract: **Identity · Mission · Responsibilities · Process · Required Output · Handoff · Boundaries · Anti-Patterns** (deputy-commander additionally carries a ninth `Command Succession` section).",
      "M2b 8-section EN")
patch("README.md",
      "**身份定位 · 使命 · 职责 · 流程 · 必需输出 · 交接 · 边界 · 反模式**。",
      "**身份定位 · 使命 · 职责 · 流程 · 必需输出 · 交接 · 边界 · 反模式**（deputy-commander 额外含第 9 节「指挥权接管」）。",
      "M2b 8-section CN")

# ── M3(豆包): P0/P1/P2 判据表落地 identity-library ──
patch("references/identity-library.md",
      "| T3 | Commands, deployments, destructive or external actions / 命令、部署、破坏性或外部操作 | Explicit per-action user authorization. |",
      """| T3 | Commands, deployments, destructive or external actions / 命令、部署、破坏性或外部操作 | Explicit per-action user authorization. |

## Finding Severity / 发现严重度（P0/P1/P2）

Review- and audit-type findings are graded with these definitions (used by `reviewer`, `code-reviewer`, `documentation-consistency-reviewer`, and the fix-loop). This table is the single authority for severity labels.

| Severity / 严重度 | Definition / 定义 | Handling / 处置 |
| --- | --- | --- |
| P0 | Would cause wrong execution, data/credential leakage, security incidents, or irreversible damage. / 会导致错误执行、数据或凭据泄露、安全事故或不可逆损坏。 | Fix immediately; block delivery until resolved. / 立即修复，修复前不得交付。 |
| P1 | Violates the skill's discipline or produces wrong results, without security or irreversible impact. / 违反本 skill 纪律或产生错误结果，但不涉及安全与不可逆。 | Fix before delivery. / 交付前修复。 |
| P2 | Quality, consistency, or maintainability improvement. / 质量、一致性或可维护性改进。 | Record as backlog; non-blocking. / 记入 backlog，不阻塞交付。 |""",
      "M3 severity table")

patch("identities/reviewer.md",
      "- Return findings with severity: P0 / P1 / P2 / UNVERIFIED.",
      "- Return findings with severity: P0 / P1 / P2 / UNVERIFIED (definitions: `references/identity-library.md` → Finding Severity).",
      "M3 reviewer.md pointer")

# ── L1+L2+L3+L17(豆包): 静态展示面滞后一次扫平 ──
patch("README.md",
      "    └── artifact-check.py        # 用户项目治理产物结构校验（gate/台账/账本）",
      "    ├── artifact-check.py        # 用户项目治理产物结构校验（gate/台账/账本）\n    ├── claim-check.py           # 完成声明机械核验（Files/Commands/Hashes）\n    └── _selftest_parser.py      # self-test.md 共享解析器（selfcheck/runner 共用）",
      "L2 README tree scripts")
patch("README.md",
      "│   └── ab-baseline/             # A/B 基线评测（协议 + 12 样例；两轮已完成，见 judgement-sheet）",
      "│   └── ab-baseline/             # A/B 基线评测（协议 + 12 样例；三轮已完成，见 judgement-sheet）",
      "L3 README tree rounds")
rpatch("site/index.html",
       r'<tr><td><a href="(https://[^"]*judgement-sheet\.md)">A/B 基线评测 · 两轮</a></td><td>12 任务 × 双臂 × 2 轮：R1 81 vs 84 → R2 <b>89 vs 87（skill 臂首次跑赢）</b>；位置违规 6\+ → 0。n=1、裁判=作者，结论不外推</td></tr>',
       r'<tr><td><a href="\1">A/B 基线评测 · 三轮</a></td><td>12 任务 × 双臂 × 3 轮：R1 81 vs 84 → R2 89 vs 87 → R3 <b>93 vs 86（三轮最大分差）</b>；T12 完成门 5→3→8；位置违规 6+ → 0。n=1、裁判=作者，结论不外推</td></tr>',
       "L3 site results row")
rpatch("site/index.html",
       r"（三条核心，约 500 tok）",
       "（三条核心，约 500 tok，估算值）",
       "L17 site tok hedge")
patch("references/platform-installation.md",
      "├── scripts/                 # install.ps1 / install.sh",
      "├── scripts/                 # install.ps1 / install.sh / selfcheck.py / selftest-runner.py / artifact-check.py / claim-check.py",
      "L2b platform-installation tree")

# ── L5(豆包): artifact-check 字段数与逐轮校验 + L15 argparse ──
patch("scripts/artifact-check.py",
      'FINDINGS_FIELDS = ["轮次编号", "未解项", "证据指针"]',
      'FINDINGS_FIELDS = ["轮次编号", "本轮改动与原因", "未解项", "证据指针"]',
      "L5a FINDINGS_FIELDS")
patch("scripts/artifact-check.py",
      '''def check_findings_ledger(path: pathlib.Path, items: list) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    rounds = ROUND_HEADING.findall(text)
    if not rounds:
        fail(items, "findings-ledger.md: no round headings (## Round N / 第 N 轮)")
        return
    for field in FINDINGS_FIELDS:
        if field not in text:
            fail(items, "findings-ledger.md: required per-round field [{}] not found".format(field))''',
      '''def check_findings_ledger(path: pathlib.Path, items: list) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    rounds = list(ROUND_HEADING.finditer(text))
    if not rounds:
        fail(items, "findings-ledger.md: no round headings (## Round N / 第 N 轮)")
        return
    # L5: check PER ROUND — file-wide containment let a single complete round
    # mask other rounds that were missing required fields.
    for i, m in enumerate(rounds):
        start = m.end()
        end = rounds[i + 1].start() if i + 1 < len(rounds) else len(text)
        seg = text[start:end]
        name = m.group(0).strip()
        for field in FINDINGS_FIELDS:
            if field not in seg:
                fail(items, "findings-ledger.md: [{}] missing field [{}]".format(name, field))''',
      "L5b per-round check")
patch("scripts/artifact-check.py",
      '''  3. findings-ledger.md — if present, each round must name the required fields
                          (round number / change & reason / open items / evidence pointer).''',
      '''  3. findings-ledger.md — if present, each round must name all four required
                          fields (round number / change & reason / open items /
                          evidence pointer); checked per round, not file-wide.''',
      "L5c docstring")
patch("scripts/artifact-check.py",
      '''import pathlib
import re
import sys''',
      '''import argparse
import pathlib
import re
import sys''',
      "L15a argparse import")
patch("scripts/artifact-check.py",
      '''    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    root = pathlib.Path(sys.argv[1])''',
      '''    ap = argparse.ArgumentParser(
        description="Structure checker for project governance artifacts (docs/gate, ledgers)")
    ap.add_argument("root", help="project root whose docs/ governance artifacts are checked")
    args = ap.parse_args()
    root = pathlib.Path(args.root)''',
      "L15b argparse use")

# ── L7(豆包): 身份文件字段清单并集 ──
patch("references/identity-library.md",
      "each member file carries role, responsibilities, platform/channel, trust tier, status, and current task.",
      "each member file carries role, responsibilities, platform/channel, trust tier, DRI ownership, availability for this task, status, and current task.",
      "L7a identity-library union")
patch("references/multi-agent-closure-rules.md",
      "Each member file must include role identity, responsibilities, current platform/channel, task status, DRI ownership, and whether it is available for this task.",
      "Each member file must include role identity, responsibilities, current platform/channel, trust tier, task status, DRI ownership, and whether it is available for this task.",
      "L7b closure EN union")
patch("references/multi-agent-closure-rules.md",
      "成员文件包含角色身份、职责、平台/通道、任务状态、DRI 归属和是否可承接本次任务。",
      "成员文件包含角色身份、职责、平台/通道、信任层级、任务状态、DRI 归属和是否可承接本次任务。",
      "L7c closure CN union")

# ── L9(豆包): qa/test-engineer 分工声明 ──
patch("identities/qa-engineer.md",
      "# ",
      "# ",
      "L9 SKIP-probe", count=0) if False else None

# ── L10(豆包): fix-loop 第 6 轮缓冲交叉引用 ──
patch("references/agent-modes.md",
      '打回与 23 字段场景共用"修复循环上限 5 轮"的纪律。',
      '打回与 23 字段场景共用"修复循环上限 5 轮"的纪律（近闭环缓冲可延至第 6 轮——见 multi-agent-closure-rules 的 Fix-Loop Cap）。',
      "L10 agent-modes CN")
patch("references/agent-modes.md",
      'Returns share the "fix-loop cap of 5 rounds" discipline with the 23-field scenario.',
      'Returns share the "fix-loop cap of 5 rounds" discipline with the 23-field scenario (a near-closure buffer may extend to a 6th round — see the Fix-Loop Cap in multi-agent-closure-rules).',
      "L10 agent-modes EN")
patch("README.md",
      "审查-修复循环上限 5 轮。",
      "审查-修复循环上限 5 轮（近闭环缓冲可延至第 6 轮，见 closure 规则）。",
      "L10 README")

# ── L16(豆包): install.ps1 守卫前移 ──
p = ROOT / "scripts/install.ps1"
t = p.read_text(encoding="utf-8")
guard = '''# Safety guard (C3-3): refuse to install into the skill repo itself — a
# pwd-based DEST run from the repo root would otherwise nest the repo
# inside itself via Copy-Item -Recurse.
$destFull = [System.IO.Path]::GetFullPath($dest)
$sourceFull = [System.IO.Path]::GetFullPath($source)
if ($destFull -like "$sourceFull*") {
  Write-Error "Refusing: destination is inside the skill repo itself ($dest)"
  exit 1
}

'''
if guard in t:
    t = t.replace(guard, "", 1)
    anchor = "New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null"
    if anchor in t:
        t = t.replace(anchor, guard + anchor, 1)
        p.write_text(t, encoding="utf-8", newline="\n")
        done.append("L16 ps1 guard order")
    else:
        failed.append(("L16", "install.ps1", "anchor lost after removal"))
else:
    failed.append(("L16", "install.ps1", "guard block not found"))

# ── L13(豆包): selfcheck docstring 已知盲区清单 ──
patch("scripts/selfcheck.py",
      'Python 3.7+ stdlib only. Exit: 0=all passed, 1=failed, 2=usage.\n"""',
      '''Python 3.7+ stdlib only. Exit: 0=all passed, 1=failed, 2=usage.

Known blind spots (literal-layer checks only, documented by design after the
2026-09-10 external reviews): semantic drift; per-item bilingual parity
(incl. identities/); cross-file field-set unions; claims-vs-reality gaps
(use claim-check.py); install.sh parity; per-round ledger fields. Green
means the literal layer is intact — nothing more.
"""''',
      "L13 blind-spots doc")

# ── L14(豆包): claim-check 绕过面写明 ──
patch("scripts/claim-check.py",
      "Exit codes: 0 = all claims verified, 1 = at least one failed, 2 = usage /\nunreadable claims file.",
      '''Blacklist is best-effort and NOT a sandbox: PowerShell aliases (ri / del with
-Recursion), long options (--recursive --force), and interpreter-indirect
execution (python -c "shutil.rmtree(...)") are NOT covered. The real trust
boundary is a trusted claims source plus human review of every entry.

Exit codes: 0 = all claims verified, 1 = at least one failed, 2 = usage /
unreadable claims file.''',
      "L14 bypass note")

# ── L6(豆包): selftest-runner schema 分隔行 5→6 ──
patch("scripts/selftest-runner.py",
      '"| --- | --- | --- | --- | --- |",',
      '"| --- | --- | --- | --- | --- | --- |",',
      "L6 schema separator")

print("DONE:", len(done))
for d in done:
    print("  ok:", d)
if failed:
    print("FAILED:", len(failed))
    for f in failed:
        print("  FAIL:", f)
else:
    print("no failures")
