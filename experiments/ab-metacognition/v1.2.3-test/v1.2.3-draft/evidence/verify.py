#!/usr/bin/env python3
"""Verification suite for csv_parser.py -- zero-dependency, third-party rerunnable.

Usage:
    python verify.py                      # tests the ../csv_parser.py deliverable
    python verify.py --parser PATH        # tests an arbitrary copy (used by mutation test)

Coverage enumeration (input-domain segments; every segment has >=1 hitting case):
    normal values ......... F1-F7   plain rows, quoted comma / newline / escaped
                                    quote / CRLF inside quotes, empty quoted field
    boundary values ....... B1-B13  empty input, lone \\n / \\r\\n / \\r, no trailing
                                    newline, trailing newline, mixed EOLs, BOM,
                                    empty rows between content, empty fields,
                                    spaces around fields (kept verbatim, RFC 4180)
    error values .......... E1-E2   unclosed quote (simple + spanning a newline)
    task-book specials .... BOM skip (B8/B9/C2), mixed EOLs (B7/C4), unclosed
                                    quote (E1/E2/C5), no trailing newline (B4),
                                    lone-EOL file (B2-B4), spaces (B10-B12)
    CLI end-to-end ........ C1-C6   stdout shape, exit codes 0/1/2, stderr message
"""

import argparse
import importlib.util
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PARSER = os.path.join(os.path.dirname(HERE), "csv_parser.py")

passed = 0
failures = []


def check(name, got, want):
    global passed
    if got == want:
        passed += 1
        print("PASS %s" % name)
    else:
        failures.append(name)
        print("FAIL %s\n  got:  %r\n  want: %r" % (name, got, want))


def check_raises(name, fn):
    global passed
    try:
        fn()
    except ValueError as exc:
        passed += 1
        print("PASS %s (ValueError: %s)" % (name, exc))
    except Exception as exc:  # noqa: BLE001 - report whatever escaped
        failures.append(name)
        print("FAIL %s raised %r instead of ValueError" % (name, exc))
    else:
        failures.append(name)
        print("FAIL %s did not raise ValueError" % name)


def load_parser(path):
    spec = importlib.util.spec_from_file_location("csv_parser_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load parser from %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_cli(parser_path, args):
    return subprocess.run(
        [sys.executable, parser_path] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parser", default=DEFAULT_PARSER,
                    help="path to the csv_parser.py copy under test")
    args = ap.parse_args()

    p = load_parser(args.parser)
    parse = p.parse

    # ---------- normal values (F1-F7) ----------
    check("F1 plain single row", parse("a,b,c"), [["a", "b", "c"]])
    check("F2 plain multi rows", parse("a,b\nc,d"),
          [["a", "b"], ["c", "d"]])
    check("F3 quoted comma", parse('a,"b,c",d'), [["a", "b,c", "d"]])
    check("F4 quoted newline", parse('"l1\nl2",x'), [["l1\nl2", "x"]])
    check("F5 escaped double quote", parse('"a""b",c'), [['a"b', "c"]])
    check("F6 CRLF inside quotes", parse('"a\r\nb"'), [["a\r\nb"]])
    check("F7 empty quoted field", parse('"",'), [["", ""]])

    # ---------- boundary values (B1-B13) ----------
    check("B1 empty input", parse(""), [])
    check("B2 lone \\n", parse("\n"), [[]])
    check("B3 lone \\r\\n", parse("\r\n"), [[]])
    check("B4 no trailing newline", parse("a\nb"), [["a"], ["b"]])
    check("B5 trailing newline", parse("a\n"), [["a"]])
    check("B6 lone \\r", parse("\r"), [[]])
    check("B7 mixed EOLs", parse("a\nb\r\nc\rd"),
          [["a"], ["b"], ["c"], ["d"]])
    check("B8 BOM + content", parse("\ufeffa,b"), [["a", "b"]])
    check("B9 BOM + CRLF rows", parse("\ufeffa\r\nb"),
          [["a"], ["b"]])
    check("B10 empty rows between content", parse("a\n\nb"),
          [["a"], [], ["b"]])
    check("B11 empty fields", parse(",,"), [["", "", ""]])
    check("B12 trailing comma", parse("a,"), [["a", ""]])
    check("B13 spaces kept verbatim (RFC 4180)", parse(" a , b "),
          [[" a ", " b "]])

    # ---------- error values (E1-E2) ----------
    check_raises("E1 unclosed quote", lambda: parse('a,"bc'))
    check_raises("E2 unclosed quote spanning newline",
                 lambda: parse('a,"b\nc'))

    # ---------- CLI end-to-end (C1-C6) ----------
    with tempfile.TemporaryDirectory() as tmp:
        def write(name, data):
            path = os.path.join(tmp, name)
            with open(path, "wb") as f:
                f.write(data)
            return path

        basic = write("basic.csv",
                      b'name,note\na,"x,y"\nb,"multi\nline"\n')
        bom = write("bom.csv", b"\xef\xbb\xbfk,v\r\n1,2\n")
        mixed = write("mixed.csv", b"a\nb\r\nc\rd")
        unclosed = write("unclosed.csv", b'a,"bc')

        r = run_cli(args.parser, [basic])
        check("C1 CLI basic output",
              (r.returncode, r.stdout),
              (0, "['name', 'note']\n['a', 'x,y']\n['b', 'multi\\nline']\n"))

        r = run_cli(args.parser, [bom])
        check("C2 CLI BOM skipped",
              (r.returncode, r.stdout),
              (0, "['k', 'v']\n['1', '2']\n"))

        r = run_cli(args.parser, [mixed])
        check("C3 CLI mixed EOLs",
              (r.returncode, r.stdout),
              (0, "['a']\n['b']\n['c']\n['d']\n"))

        r = run_cli(args.parser, [unclosed])
        check("C4 CLI unclosed quote exit 1 + stderr",
              (r.returncode, "unclosed" in r.stderr), (1, True))

        r = run_cli(args.parser, [])
        check("C5 CLI no args usage exit 2",
              (r.returncode, "usage" in r.stderr), (2, True))

        r = run_cli(args.parser, [os.path.join(tmp, "missing.csv")])
        check("C6 CLI missing file exit 1",
              (r.returncode, "cannot read" in r.stderr), (1, True))

        utf8 = write("utf8.csv",
                     b'name,\xe5\xa4\x87\xe6\xb3\xa8\n'
                     b'1,"\xe5\xbc\x95\xe5\x8f\xb7,\xe6\xb5\x8b\xe8\xaf\x95"\n')
        r = run_cli(args.parser, [utf8])
        check("C7 CLI non-ASCII UTF-8 output",
              (r.returncode, r.stdout),
              (0, "['name', '备注']\n['1', '引号,测试']\n"))

    # ---------- summary ----------
    total = passed + len(failures)
    print("\n%d/%d passed" % (passed, total))
    if failures:
        print("FAILED: %s" % ", ".join(failures))
        return 1
    print("ALL GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
