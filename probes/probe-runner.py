#!/usr/bin/env python3
"""Probe runner: drive the adversarial light-channel / form-declaration scenarios.

The three rounds in this skill share ONE controlled prompt (see
probe-scenarios.json) re-run against successive rule states. This tool does NOT
execute a host model — a human/agent runs each probe prompt against the skill
under test and records the verdict in an archive file (default "probes/last-run.md").
This runner turns the method into a repeatable regression instrument:

  python scripts/probe-runner.py list          # print scenario table
  python scripts/probe-runner.py report [id]   # print the archive (or one round)
  python scripts/probe-runner.py archive <id> <PASS|FAIL> <evidence...>
                                               # append one round's verdict to the archive

No verdict is auto-computed from prompts: pass/fail is decided by the human
reading the host output against pass_conditions/fail_patterns. The runner only
records honestly and keeps the archive append-only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
PROBES = BASE / "probes"
SCEN = PROBES / "probe-scenarios.json"
ARCHIVE = PROBES / "last-run.md"


def load():
    if not SCEN.exists():
        sys.exit("missing " + str(SCEN))
    try:
        return json.loads(SCEN.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit("malformed JSON in " + str(SCEN) + " -- line %d col %d: %s"
                 % (exc.lineno, exc.colno, exc.msg))


def cmd_list(_):
    d = load()
    print("# Probe scenarios (schema %s)" % d["schema_version"])
    print("Probe prompt: %s\n" % d["probe_prompt"])
    print("| # | Round | Title | Attack target | Pass conditions | Last verified |")
    print("|---|-------|-------|---------------|-----------------|---------------|")
    for s in d["scenarios"]:
        print("| {} | {} | {} | {} | {} | {} |".format(
            s["id"], s["round"], s["title"], s["attack_target"],
            "; ".join(s["pass_conditions"]), s["last_verified_on"]))
    return 0


def cmd_archive(args):
    if len(args.id) != 1:
        sys.exit("need exactly one scenario id")
    scid = args.id[0]
    d = load()
    sc = next((s for s in d["scenarios"] if s["id"] == scid), None)
    if not sc:
        sys.exit("unknown scenario id: " + scid)
    if args.verdict not in ("PASS", "FAIL"):
        sys.exit("verdict must be PASS or FAIL")
    evidence = " ".join(args.evidence)
    if not evidence:
        sys.exit("evidence is required")
    # Keep every archive entry on ONE line (append-only format invariant):
    # embedded newlines in evidence would corrupt the line-oriented archive
    # and silently break cmd_report's per-line filtering.
    evidence = " ".join(evidence.split())
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with ARCHIVE.open("a", encoding="utf-8") as f:
        f.write("- [{stamp}] **{scid} ({round_}; since rule {rule_ver})** "
                "{verdict} — {evidence}\n"
                .format(stamp=stamp, scid=scid, round_=sc["round"], rule_ver=sc["history_rule_version"],
                        verdict=args.verdict, evidence=evidence))
    print("appended -> " + str(ARCHIVE))
    return 0


def cmd_report(args):
    if not ARCHIVE.exists():
        print("no archive yet:", str(ARCHIVE))
        return 0
    text = ARCHIVE.read_text(encoding="utf-8")
    if args.id:
        # args.id is a plain string (nargs="?"), not a list like archive's
        # nargs=1 — indexing it would filter on the id's first character.
        scid = args.id
        keep = [l for l in text.splitlines() if "**%s " % scid in l]
        text = "\n".join(keep) if keep else ("no entries for " + scid)
    print(text)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe runner (append-only archive)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    ar = sub.add_parser("archive")
    ar.add_argument("id", nargs=1, help="scenario id, e.g. P2")
    ar.add_argument("verdict", help="PASS or FAIL")
    ar.add_argument("evidence", nargs="+", help="what the host actually did")
    ar.set_defaults(fn=cmd_archive)
    rep = sub.add_parser("report")
    rep.add_argument("id", nargs="?", default=None)
    rep.set_defaults(fn=cmd_report)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
