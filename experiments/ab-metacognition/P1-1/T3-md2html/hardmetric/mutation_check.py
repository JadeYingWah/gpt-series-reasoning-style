#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mutation_check.py -- anti-example / discrimination test for verify.py.

For every declared mutant (a ONE-LINE change to md2html.py) this script:
  1. creates the mutated copy in a temp directory (outside the delivery dir),
  2. runs `verify.py --impl <mutant>` and collects the failing case ids,
  3. asserts the mutant is CAUGHT (verify.py exits non-zero) and names at
     least one failing case.

A mutant that survives (verify.py still green) means the suite has a blind
spot -> this script exits 1 and prints the coverage hole.

Usage:  python mutation_check.py           exit 0 = every mutant caught
"""

from __future__ import annotations

import concurrent.futures as _futures
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL = os.path.join(HERE, "md2html.py")
VERIFY = os.path.join(HERE, "verify.py")

# (id, description, old_snippet, new_snippet)  -- exactly one occurrence each
MUTANTS = [
    ("M1-no-amp-escape",
     "do not escape & (drop entity escaping of ampersand)",
     'return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")',
     'return s.replace("<", "&lt;").replace(">", "&gt;")'),
    ("M2-parse-inline-in-fence",
     "apply inline parsing inside fenced code blocks",
     'code = "\\n".join(escape_text(x) for x in buf)  # D1',
     'code = "\\n".join(render_inline(x) for x in buf)'),
    ("M3-italic-before-bold",
     "apply emphasis in the wrong order (italic first)",
     '    s = BOLD_STAR_RE.sub(strong, s)\n    s = BOLD_UNDER_RE.sub(strong, s)\n    s = _italic(s)',
     '    s = _italic(s)\n    s = BOLD_STAR_RE.sub(strong, s)\n    s = BOLD_UNDER_RE.sub(strong, s)'),
    ("M4-no-paragraph-merge",
     "emit one <p> per line instead of merging consecutive lines",
     '        body.append("<p>" + render_inline("\\n".join(para)) + "</p>")',
     '        body.extend("<p>" + render_inline(x) + "</p>" for x in para)'),
    ("M5-drop-unclosed-fence",
     "silently drop an unterminated code fence",
     '                buf.append(lines[i])\n                i += 1',
     '                if CLOSE_FENCE_RE.match(lines[i]) is None and i == n - 1:\n'
     '                    buf = []\n                else:\n'
     '                    buf.append(lines[i])\n                i += 1'),
    ("M6-heading-up-to-7",
     "accept 7 levels of # as a heading",
     'HEADING_RE = re.compile(r"^(#{1,6})(?:[ \\t]+(.*?))?[ \\t]*$")',
     'HEADING_RE = re.compile(r"^(#{1,7})(?:[ \\t]+(.*?))?[ \\t]*$")'),
    ("M7-no-attr-escape",
     "do not escape quotes in an href attribute",
     '    s = escape_text(s).replace(\'"\', "&quot;")',
     '    s = escape_text(s)'),
    ("M8-code-span-emphasis",
     "let emphasis be parsed inside inline code spans",
     '            parts.append("<code>" + escape_text(chunk) + "</code>")',
     '            parts.append("<code>" + _emphasis(escape_text(chunk)) + "</code>")'),
    ("M9-slot-id-collision",
     "give every placeholder slot-set the same id (nested renders overwrite "
     "each other -- the defect this suite caught during development)",
     "        self.sid = next(_SLOT_IDS)",
     "        self.sid = 0"),
    ("M10-no-gt-escape",
     "do not escape > in text",
     'return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")',
     'return s.replace("&", "&amp;").replace("<", "&lt;")'),
]


def _run_one(tmpdir, source, mutant):
    """Create the mutated copy in tmpdir and run verify.py against it."""
    mid, desc, old, new = mutant
    n = source.count(old)
    if n != 1:
        return mid, desc, None, "pattern occurs %d times, expected 1: %r" % (n, old[:60])
    mpath = os.path.join(tmpdir, mid + ".py")
    with open(mpath, "w", encoding="utf-8") as fh:
        fh.write(source.replace(old, new, 1))
    proc = subprocess.run([sys.executable, VERIFY, "--impl", mpath],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = proc.stdout.decode("utf-8", "replace")
    fails = [ln[7:].split()[0] for ln in out.splitlines() if ln.startswith("[FAIL]")]
    return mid, desc, (proc.returncode, fails), None


def main(argv=None):
    if not os.path.exists(IMPL):
        print("FATAL: %s not found" % IMPL)
        return 1
    with open(IMPL, "r", encoding="utf-8") as fh:
        source = fh.read()

    tmpdir = tempfile.mkdtemp(prefix="md2html-mutants-")
    caught, survived, broken = [], [], []
    workers = max(1, min(len(MUTANTS), os.cpu_count() or 4))
    try:
        with _futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_run_one, tmpdir, source, m) for m in MUTANTS]
            for fut in futures:  # declared order keeps the report deterministic
                mid, desc, result, err = fut.result()
                if err is not None:
                    broken.append((mid, err))
                    print("[BROKEN] %-24s %s" % (mid, err))
                    continue
                code, fails = result
                if code != 0 and fails:
                    caught.append((mid, desc, fails))
                    print("[CAUGHT] %-24s exit=%d  failing cases: %s"
                          % (mid, code, ", ".join(fails[:6])
                             + ("" if len(fails) <= 6 else " (+%d)" % (len(fails) - 6))))
                else:
                    survived.append((mid, desc))
                    print("[SURVIVED] %-24s verify.py still green -- SUITE HAS A BLIND SPOT" % mid)
    finally:
        for fn in os.listdir(tmpdir):
            try:
                os.remove(os.path.join(tmpdir, fn))
            except OSError:
                pass
        try:
            os.rmdir(tmpdir)
        except OSError:
            pass

    print("\n--- mutation summary ---")
    print("  mutants declared : %d" % len(MUTANTS))
    print("  caught (red)     : %d" % len(caught))
    print("  survived (green) : %d" % len(survived))
    print("  broken (n/a)     : %d" % len(broken))
    for mid, _ in survived:
        print("  BLIND SPOT: %s" % mid)
    for mid, why in broken:
        print("  BROKEN MUTANT: %s -- %s" % (mid, why))
    ok = not survived and not broken
    print("mutation check: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
