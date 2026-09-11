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

Trust model (IMPORTANT, H1): the claims file is UNTRUSTED INPUT — it is
authored by the agent whose completion is being judged. Commands are executed
with shell=True, so a hostile claims file is arbitrary code execution.
Mitigations (2026-09-11, two layers):
  1. destructive-command blacklist (best-effort pattern match);
  2. interpreter default-deny — a command whose FIRST token is an
     interpreter/shell (python/python2/python3/pythonw/py/node/deno/bun/perl/
     ruby/php/powershell/pwsh/cmd/bash/sh/zsh/fish/ksh/npx/uvx/pipx, absolute
     paths included) is BLOCKED unless it matches a narrow safe allowlist
     (`python -m unittest|pytest`, `python --version`) — `-c/-e/-Command`
     payloads and `python script.py` are unauditable from the command line
     (proven live on 2026-09-11: `python -c "shutil.rmtree('victim')"` and
     `python pwn.py` ran unchecked, victim dir deleted, 0 blocked).
     Both layers are overridden only by --allow-dangerous after human review.
Honest limit (NOT a sandbox): the allowlist still executes the project's own
test suite — conftest.py / imported test modules are project code and could
hide payloads there; exec-style tools NOT in the family (go run, cargo run,
make, uv, npm, env, xargs, …) are not covered either. The real trust
boundary remains a trusted claims source plus human review of every entry.
The tool also prints how many commands it executed so the operator can audit.
Content-quality judgement remains human.

Claims file format (minimal markdown):

    # Completion Claims
    ## Files
    - ui.html
    - docs/plans/2026-09-10-brief.md
    ## Commands
    - python -m unittest discover -v   # expect exit 0
    - pytest -q

Usage:
  python scripts/claim-check.py <claims.md> [project-root] [--timeout S]
                                [--allow-dangerous]

  <project-root> (default: current directory) is the base for relative file
  paths and the working directory for commands.

The blacklist stays best-effort and NOT a sandbox: PowerShell aliases (ri /
del with -Recursion), long options (--recursive --force), and other
undetected spellings are NOT covered. The interpreter default-deny closes
the interpreter-indirect hole; it does not turn this tool into a sandbox.

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

# Best-effort destructive-command blacklist (H1). Case-insensitive. Not a
# sandbox — the point is to stop the obvious footguns before a human reviews.
# 2026-09-11: `git restore` and `git checkout .` added — both discard worktree
# changes exactly like the already-blocked `git checkout -- .`; blocking one
# spelling of a destructive op while allowing its synonym was a hole, not a
# judgement call.
DANGEROUS_RES = [
    r"\brm\b[^|;&]*-[a-zA-Z]*[rf]",
    r"\bdel\b\s+/[sq]",
    r"\brmdir\b\s+/s",
    r"\bRemove-Item\b[^|;&]*-Recurs",
    r"\bformat\b\s+[a-zA-Z]:",
    r"\bshutdown\b",
    r"\bgit\s+push\b[^|;&]*(-f\b|--force)",
    r"\bgit\s+push\b[^|;&]*--delete\b",
    r"\bgit\s+push\b[^|;&]*:[a-zA-Z]",          # `git push origin :branch`
    r"\bgit\s+push\b[^|;&]*\s\+",               # `git push origin +branch` (forced)
    r"\bgit\s+reset\s+--hard",
    r"\bgit\s+clean\s+-[a-zA-Z]*[fd]",
    r"\bgit\s+checkout\s+--\s+\.?\s*$",
    r"\bgit\s+checkout\s+\.",                   # `git checkout .` / `./src` == restore
    r"\bgit\s+restore\b(?!.*--staged)",         # discards worktree changes; --staged only unstages
    r"\bgit\s+branch\s+-[a-zA-Z]*(?-i:D)",      # 仅大写 -D 强删；小写 -d 只删已合并分支，放行
    r"\bmkfs\b",
    r"\bdd\b\s+if=",
    r"\btruncate\b\s+(?:-s\s*|--size=)0",
    r"\b(curl|wget)\b[^|;&]*\|\s*(ba)?sh\b",
    r"\b(Invoke-Expression|iex)\b",
    r"\breg\s+(add|delete)\b",
    r"\bschtasks\b",
    r"\bchmod\s+-Rf?\s*777\s+/",
    r"\bSet-ExecutionPolicy\b",
]

COMPILED_DANGEROUS = [re.compile(p, re.I) for p in DANGEROUS_RES]

# Layer 2 (2026-09-11): interpreter default-deny. A command whose FIRST token
# is an interpreter/shell gets its payload executed in a process the checker
# cannot audit from the command line (`python -c "..."`, `node -e "..."`,
# `python script.py`) — the 2026-09-11 blacklist-only stance let all of these
# run unchecked (proven live: victim dir deleted via shutil.rmtree inside
# `python -c`, 0 blocked). Default-deny closes that class; the narrow
# allowlist below keeps the canonical safe forms (project test suite,
# version query) usable without a flag.
INTERPRETER_NAMES = {
    "python", "python2", "python3", "pythonw", "py",
    "node", "deno", "bun",
    "perl", "ruby", "php",
    "powershell", "pwsh",
    "cmd", "bash", "sh", "zsh", "fish", "ksh",
    "npx", "uvx", "pipx",   # download-and-run package runners
}
# Known limits (documented, best-effort): exec-style tools that compile or
# download and then run code — `go run`, `cargo run`, `make`, `uv`, `npm`,
# `env`, `xargs`, … — are NOT in the family and stay blacklist-only.

# Allowlist: full-command anchored, chaining excluded (`;|&` and backticks /
# `$()` can never reach end-of-line through the negated class). Optional
# surrounding quotes on the executable token are accepted (2026-09-11 audit:
# quoted absolute paths are ordinary on Windows).
_INTERP_TOKEN = (r"[\"']?(?:[a-zA-Z]:[\\/][^\s\"']*[\\/])?"  # optional quotes+absolute path
                 r"(?:python(?:[\d.]+)?|py)(?:\.exe)?[\"']?")
SAFE_INTERPRETER_RES = [
    re.compile(r"^" + _INTERP_TOKEN +
               r"\s+(?:-\d(?:\.\d+)?\s+)?"                  # py -3 / py -3.11
               r"-m\s+(?:unittest|pytest)\b[^\n;|&`$]*$", re.I),
    re.compile(r"^" + _INTERP_TOKEN + r"\s+(?:--version|-V)\s*$", re.I),
]


def _argv0(command: str) -> str:
    """First token of the command, reduced to a bare lowercase name
    (strips surrounding quotes, drive/path and .exe — `C:/.../python.exe`
    and `"C:/.../python.exe"` both reduce to `python`)."""
    stripped = command.strip()
    if not stripped:
        return ""
    tok = stripped.split(None, 1)[0].strip("\"'")
    base = re.split(r"[\\/]", tok)[-1].lower().strip("\"'")
    if base.endswith(".exe"):
        base = base[:-4]
    # Version-suffixed interpreter spellings are the same interpreter:
    # python3.13 / python3 / pythonw3.12 all default-deny like `python`.
    # (2026-09-11 audit RED: `python3.13 -c "…"` sailed past the family set.)
    m = re.fullmatch(r"(pythonw?)(?:\d+(?:\.\d+)*)?", base)
    if m:
        base = m.group(1)
    return base


def interpreter_block_reason(command: str) -> str | None:
    """Return the interpreter name if this command must default-deny, else None."""
    argv0 = _argv0(command)
    if argv0 not in INTERPRETER_NAMES:
        return None
    for res in SAFE_INTERPRETER_RES:
        if res.search(command):
            return None
    return argv0


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
            # M2: word-boundary matching — "Profile" must NOT match Files.
            if re.match(r"^files?\b", title):
                section = "files"
            elif re.match(r"^commands?\b", title):
                section = "commands"
            elif re.match(r"^hash(es)?\b", title):
                section = "hashes"
            else:
                section = None
            continue
        if not line.startswith("- ") or section is None:
            continue
        entry = line[2:].strip()
        claims[section].append(entry)
    return claims


def split_expect(command: str):
    """Split a `cmd  # expect exit N` trailing comment. Default expectation: 0."""
    m = re.search(r"\#\s*expect\s+exit\s+(\d+)\s*$", command, re.I)
    if m:
        return command[: m.start()].strip(), int(m.group(1))
    return command, 0


def is_dangerous(command: str) -> str | None:
    for cr in COMPILED_DANGEROUS:
        m = cr.search(command)
        if m:
            return m.group(0)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify a completion claim's file/command assertions")
    ap.add_argument("claims", help="markdown claims file (## Files / ## Commands / ## Hashes)")
    ap.add_argument("root", nargs="?", default=".", help="project root for relative paths & command cwd")
    ap.add_argument("--timeout", type=int, default=600,
                    help="per-command timeout in seconds (default 600; M3)")
    ap.add_argument("--allow-dangerous", action="store_true",
                    help="execute commands matching the destructive blacklist OR "
                         "interpreter default-deny (H1 override; review first!)")
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

    executed = 0
    for entry in claims["commands"]:
        cmd, expect = split_expect(entry)
        if not cmd:
            results.append((False, "command: empty command line"))
            continue
        danger = is_dangerous(cmd)
        interp = interpreter_block_reason(cmd)
        if (danger or interp) and not args.allow_dangerous:
            if danger:
                reason = "dangerous pattern `{}`".format(danger)
            else:
                reason = ("interpreter-indirect execution (`{}` …; `-c/-e/script` "
                          "payload is not auditable from the command line)".format(interp))
            results.append((False, "command: `{}` BLOCKED -- {} "
                                   "(review it, then re-run with --allow-dangerous)".format(cmd, reason)))
            continue
        try:
            # H2: explicit UTF-8 — text=True alone uses the Windows locale
            # (cp936) and garbles UTF-8 command output (seen live in R3).
            proc = subprocess.run(cmd, shell=True, cwd=str(root),
                                  capture_output=True, text=True,
                                  encoding="utf-8", errors="replace",
                                  timeout=args.timeout)
            executed += 1
            code = proc.returncode
            tail = (proc.stdout or proc.stderr or "").strip().splitlines()
            hint = tail[-1][:80] if tail else ""
            ok = code == expect
            results.append((ok, "command: `{}` exit={} (expected {}) {}".format(
                cmd, code, expect, "| " + hint if hint else "")))
        except subprocess.TimeoutExpired:
            results.append((False, "command: `{}` TIMEOUT ({}s; adjust --timeout)".format(cmd, args.timeout)))
        except OSError as exc:
            results.append((False, "command: `{}` failed to launch -- {}".format(cmd, exc)))

    for entry in claims["hashes"]:
        m = re.match(r"(.+?)\s*=\s*([0-9a-fA-F]{64})\s*$", entry)
        if not m:
            results.append((False, "hash: malformed entry `{}` (want `<path> = <sha256 hex, 64 chars>`)".format(entry)))
            continue
        rel, want = m.group(1).strip(), m.group(2).lower()
        p = (root / rel) if not pathlib.Path(rel).is_absolute() else pathlib.Path(rel)
        if not p.is_file():
            results.append((False, "hash: {} MISSING".format(rel)))
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        ok = digest == want
        results.append((ok, "hash: {} {}".format(rel, "MATCH" if ok else "MISMATCH (actual " + digest[:16] + "…)")))

    print("Completion-claim check / 完成声明机械核验")
    print("- Claims file: {}".format(claims_path))
    print("- Project root: {}".format(root))
    for ok, line in results:
        print("  [{}] {}".format("PASS" if ok else "FAIL", line))
    fails = sum(1 for ok, _ in results if not ok)
    print("- Result: {}/{} verified".format(len(results) - fails, len(results)))
    print("- Trust note: {} command(s) executed via shell=True; the claims file "
          "is untrusted input (destructive blacklist + interpreter default-deny{}; "
          "saw {} blocked; neither layer is a sandbox).".format(
              executed, " off" if args.allow_dangerous else " on",
              sum(1 for _, l in results if "BLOCKED" in l)))
    if fails:
        print("  The claim is NOT verified; treat the completion as unproven until fixed.")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
