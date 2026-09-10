#!/usr/bin/env python3
"""Claim checker: verify a completion claim's disk/runnable assertions mechanically.

Mechanizes the Honesty Gate "disk self-check list" clause (see
references/series-reasoning-workflow.md): a completion claim must attach a
list of changed files and run commands, each with a concrete path / expected
exit code. This tool takes such a list and verifies every entry FRESH:

  - every file under `## Files` must exist on disk;
  - every command under `## Commands` is re-run now, and its exit code must
    match the expectation (default 0; override with a trailing
    `# expect exit N` comment);
  - optional `## Hashes` entries pin exact content: `- <path> = <sha256>`.

Honesty boundary (same philosophy as selfcheck.py): this proves the DISK and
RUNNABLE assertions only. It does not judge whether the delivered content is
good — that remains a human evidence check.

Claims file format (minimal markdown):

    # Completion Claims
    ## Files
    - ui.html
    - docs/plans/2026-09-10-brief.md
    ## Commands
    - python todo.py list          # expect exit 0
    - python -m unittest test_utils -v

Usage:
  python scripts/claim-check.py <claims.md> [project-root]

  <project-root> (default: current directory) is the base for relative file
  paths and the working directory for commands.

Exit codes: 0 = all claims verified, 1 = at least one failed, 2 = usage /
unreadable claims file.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import subprocess
import sys


def parse_claims(text: str) -> dict:
    claims = {"files": [], "commands": [], "hashes": []}
    section = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        head = re.match(r"^#{1,6}\s*(.+?)\s*$", line)
        if head:
            title = head.group(1).lower()
            if "file" in title:
                section = "files"
            elif "command" in title:
                section = "commands"
            elif "hash" in title:
                section = "hashes"
            else:
                section = None
            continue
        if not line.startswith("- ") or section is None:
            continue
        entry = line[2:].strip()
        if section == "files":
            claims["files"].append(entry)
        elif section == "commands":
            claims["commands"].append(entry)
        elif section == "hashes":
            claims["hashes"].append(entry)
    return claims


def split_expect(command: str):
    """Split a `cmd  # expect exit N` trailing comment. Default expectation: 0."""
    m = re.search(r"\#\s*expect\s+exit\s+(\d+)\s*$", command, re.I)
    if m:
        return command[: m.start()].strip(), int(m.group(1))
    return command, 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify a completion claim's file/command assertions")
    ap.add_argument("claims", help="markdown claims file (## Files / ## Commands / ## Hashes)")
    ap.add_argument("root", nargs="?", default=".", help="project root for relative paths & command cwd")
    args = ap.parse_args()

    claims_path = pathlib.Path(args.claims)
    if not claims_path.is_file():
        print("ERROR: claims file not found: " + str(claims_path))
        return 2
    try:
        text = claims_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print("ERROR: claims file is not valid UTF-8 -- " + str(exc))
        return 2
    root = pathlib.Path(args.root)
    if not root.is_dir():
        print("ERROR: not a directory: " + str(root))
        return 2

    claims = parse_claims(text)
    if not (claims["files"] or claims["commands"] or claims["hashes"]):
        print("ERROR: no `## Files` / `## Commands` / `## Hashes` entries found in " + str(claims_path))
        print("A completion claim without a checkable list is an intention, not a claim.")
        return 2

    results = []  # (ok, line)

    for entry in claims["files"]:
        p = (root / entry) if not pathlib.Path(entry).is_absolute() else pathlib.Path(entry)
        ok = p.is_file()
        results.append((ok, "file exists: {} -> {}".format(entry, "FOUND" if ok else "MISSING")))

    for entry in claims["commands"]:
        cmd, expect = split_expect(entry)
        if not cmd:
            results.append((False, "command: empty command line"))
            continue
        try:
            proc = subprocess.run(cmd, shell=True, cwd=str(root),
                                  capture_output=True, text=True, timeout=600)
            code = proc.returncode
            tail = (proc.stdout or proc.stderr or "").strip().splitlines()
            hint = tail[-1][:80] if tail else ""
            ok = code == expect
            results.append((ok, "command: `{}` exit={} (expected {}) {}".format(
                cmd, code, expect, "| " + hint if hint else "")))
        except subprocess.TimeoutExpired:
            results.append((False, "command: `{}` TIMEOUT (600s)".format(cmd)))
        except OSError as exc:
            results.append((False, "command: `{}` failed to launch -- {}".format(cmd, exc)))

    for entry in claims["hashes"]:
        m = re.match(r"(.+?)\s*=\s*([0-9a-fA-F]{8,64})\s*$", entry)
        if not m:
            results.append((False, "hash: malformed entry `{}` (want `<path> = <sha256>`)".format(entry)))
            continue
        rel, want = m.group(1).strip(), m.group(2).lower()
        p = (root / rel) if not pathlib.Path(rel).is_absolute() else pathlib.Path(rel)
        if not p.is_file():
            results.append((False, "hash: {} MISSING".format(rel)))
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        ok = digest.startswith(want)
        results.append((ok, "hash: {} {} (actual {}...)".format(
            rel, "MATCH" if ok else "MISMATCH", digest[:len(want)])))

    print("Completion-claim check / 完成声明机械核验")
    print("- Claims file: {}".format(claims_path))
    print("- Project root: {}".format(root))
    for ok, line in results:
        print("  [{}] {}".format("PASS" if ok else "FAIL", line))
    fails = sum(1 for ok, _ in results if not ok)
    print("- Result: {}/{} verified".format(len(results) - fails, len(results)))
    if fails:
        print("  The claim is NOT verified; treat the completion as unproven until fixed.")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
