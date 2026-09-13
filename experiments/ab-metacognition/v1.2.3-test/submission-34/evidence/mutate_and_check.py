#!/usr/bin/env python3
"""Mutation (counter-example) test for the csv_parser.py verification suite.

Requirement: the suite must have killing power. Each mutant injects exactly
one fault into a copy of csv_parser.py; the suite must turn RED for every
mutant. If an anchor is missing (source changed), the mutator FAILS loudly
instead of passing silently.

Usage:
    python mutate_and_check.py

Result: prints KILLED/SURVIVED per mutant and MUTATION KILL RATE n/n.
Exit 0 iff every mutant is killed (4/4). Mutant copies live in a system
temp dir and are removed on exit.
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PARSER = os.path.join(os.path.dirname(HERE), "csv_parser.py")
VERIFY = os.path.join(HERE, "verify.py")

MUTANTS = [
    ("M1 remove BOM skip",
     "    if text.startswith(BOM):\n        text = text[1:]",
     "    pass  # MUTANT M1: BOM skip removed"),
    ("M2 break escaped quote",
     'field.append(\'"\')',
     "field.append('')"),
    ("M3 break CRLF merge",
     'if c == "\\r" and i + 1 < n and text[i + 1] == "\\n":',
     "if False:"),
    ("M4 drop last line without newline",
     '    if field_started or row:\n        row.append("".join(field))  # last line without trailing newline',
     "    if False:  # MUTANT M4: last line dropped"),
]


def main():
    with open(PARSER, "r", encoding="utf-8") as f:
        src = f.read()

    killed = 0
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, old, new in MUTANTS:
            if old not in src:
                results.append((name, "MUTATOR-BROKEN (anchor not found)"))
                continue
            mutant_src = src.replace(old, new, 1)
            mutant_path = os.path.join(
                tmp, "mutant_%d.py" % (MUTANTS.index((name, old, new)) + 1))
            with open(mutant_path, "w", encoding="utf-8", newline="") as f:
                f.write(mutant_src)
            r = subprocess.run(
                [sys.executable, VERIFY, "--parser", mutant_path],
                capture_output=True, text=True, encoding="utf-8")
            suite_red = r.returncode != 0 and "FAIL" in r.stdout
            if suite_red:
                killed += 1
                results.append((name, "KILLED"))
            else:
                results.append((name, "SURVIVED (suite stayed green!)"))

    for name, verdict in results:
        print("%-42s %s" % (name, verdict))
    total = len(MUTANTS)
    print("\nMUTATION KILL RATE: %d/%d" % (killed, total))
    if killed != total:
        print("NOT ALL MUTANTS KILLED -- verification lacks discrimination")
        return 1
    print("OK: every mutant turned the suite red")
    return 0


if __name__ == "__main__":
    sys.exit(main())
