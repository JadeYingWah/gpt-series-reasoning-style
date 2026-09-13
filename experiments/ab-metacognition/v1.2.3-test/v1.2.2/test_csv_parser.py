#!/usr/bin/env python3
"""
Comprehensive verification suite for csv_parser.py.

Covers:
  1. Functional tests (7 requirements from TASK.md)
  2. Edge-case tests (6 requirements from TASK.md)
  3. Oracle cross-validation (against Python stdlib csv module)
  4. Mutation / anti-example tests (inject bugs → verify suite catches them)

Input-domain coverage (enumerated before test execution):
  Equivalence classes:
    E1  standard unquoted fields          E2  quoted fields with commas
    E3  quoted fields with newlines       E4  quoted fields with escaped quotes
    E5  empty fields (consecutive commas) E6  empty lines (blank rows)
    E7  line endings \n                    E8  line endings \r\n
    E9  line endings \r (old Mac)         E10 mixed line endings
    E11 UTF-8 BOM + content               E12 leading/trailing spaces in fields
    E13 spaces inside quoted fields        E14 single-character fields
    E15 last line without trailing newline E16 empty file
    E17 file with only newline(s)          E18 unclosed quote (error path)
    E19 quote in middle of unquoted field  E20 content after closing quote

  Boundary values:
    B1  empty string input                 B2  BOM-only input
    B3  single field, no comma             B4  quoted empty field ""
    B5  only escaped quotes (4 quotes -> one ") B6  multiple consecutive blank lines
    B7  trailing comma on last line        B8  leading comma on first line

  Abnormal inputs:
    A1  unclosed quote → ValueError        A2  unclosed quote at EOF
    A3  file not found (CLI)               A4  non-UTF-8 file (CLI)

Zero external dependencies.  Fixed inputs (no randomness).
Reproduce:  python test_csv_parser.py
"""

from __future__ import annotations

import csv
import importlib.util
import io
import os
import sys
import tempfile
import textwrap
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
PARSER_PATH = os.path.join(HERE, "csv_parser.py")
REPORT_PATH = os.path.join(HERE, "evidence", "test_report.txt")

# ---------------------------------------------------------------------------
# Load the parser under test (independent import, no package dependency)
# ---------------------------------------------------------------------------

def load_parser(path: str = PARSER_PATH):
    """Load csv_parser module from *path* without installing it."""
    spec = importlib.util.spec_from_file_location("csv_parser_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Test framework (tiny, zero-dep)
# ---------------------------------------------------------------------------

class TestResult:
    def __init__(self) -> None:
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []  # (name, error)
        self.errors: List[Tuple[str, str]] = []   # (name, traceback)

    def ok(self, name: str) -> None:
        self.passed.append(name)

    def fail(self, name: str, msg: str) -> None:
        self.failed.append((name, msg))

    def err(self, name: str, tb: str) -> None:
        self.errors.append((name, tb))

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed) + len(self.errors)

    @property
    def all_pass(self) -> bool:
        return not self.failed and not self.errors


def assert_eq(actual: Any, expected: Any, name: str, result: TestResult) -> None:
    if actual == expected:
        result.ok(name)
    else:
        result.fail(name, f"expected {expected!r}, got {actual!r}")


def assert_raises(exc_type: type, fn: Callable, name: str, result: TestResult,
                   match: Optional[str] = None) -> None:
    try:
        fn()
    except exc_type as e:
        if match and match not in str(e):
            result.fail(name, f"raised {exc_type.__name__} but message {e!r} does not contain {match!r}")
        else:
            result.ok(name)
    except Exception as e:
        result.fail(name, f"expected {exc_type.__name__}, got {type(e).__name__}: {e}")
    else:
        result.fail(name, f"expected {exc_type.__name__} but no exception raised")


# ---------------------------------------------------------------------------
# Section 1: Functional tests (TASK.md 功能要求 1-7)
# ---------------------------------------------------------------------------

def run_functional_tests(parse_fn: Callable[[str], List[List[str]]],
                          result: TestResult) -> None:
    """F1-F7: the seven functional requirements from TASK.md."""

    # F1: standard CSV (comma-separated, quote-wrapped)
    assert_eq(parse_fn("a,b,c\n"), [["a", "b", "c"]], "F1.1 basic three fields", result)
    assert_eq(parse_fn('"x","y","z"\n'), [["x", "y", "z"]], "F1.2 all quoted fields", result)
    assert_eq(parse_fn('a,"b",c\n'), [["a", "b", "c"]], "F1.3 mixed quoted/unquoted", result)

    # F2: quoted fields with commas, newlines, escaped quotes
    assert_eq(parse_fn('"a,b",c\n'), [["a,b", "c"]], "F2.1 comma inside quotes", result)
    assert_eq(parse_fn('"a\nb",c\n'), [["a\nb", "c"]], "F2.2 newline inside quotes", result)
    assert_eq(parse_fn('"a""b",c\n'), [["a\"b", "c"]], "F2.3 escaped quote inside quotes", result)
    assert_eq(parse_fn('"a,b\nc""d",e\n'), [["a,b\nc\"d", "e"]], "F2.4 combined special chars in quotes", result)

    # F3: empty fields, empty lines
    assert_eq(parse_fn("a,,b\n"), [["a", "", "b"]], "F3.1 empty middle field", result)
    assert_eq(parse_fn(",a\n"), [["", "a"]], "F3.2 empty leading field", result)
    assert_eq(parse_fn("a,\n"), [["a", ""]], "F3.3 empty trailing field", result)
    assert_eq(parse_fn("a,b\n\nc,d\n"), [["a", "b"], [], ["c", "d"]], "F3.4 empty line between rows", result)

    # F4: different line endings
    assert_eq(parse_fn("a,b\nc,d\n"), [["a", "b"], ["c", "d"]], "F4.1 LF line endings", result)
    assert_eq(parse_fn("a,b\r\nc,d\r\n"), [["a", "b"], ["c", "d"]], "F4.2 CRLF line endings", result)
    assert_eq(parse_fn("a,b\rc,d\r"), [["a", "b"], ["c", "d"]], "F4.3 CR-only line endings", result)

    # F5: UTF-8 BOM detection and skipping
    assert_eq(parse_fn("\ufeffa,b\n"), [["a", "b"]], "F5.1 BOM + normal content", result)
    assert_eq(parse_fn("\ufeff"), [], "F5.2 BOM-only input", result)
    assert_eq(parse_fn("\ufeff\n"), [[]], "F5.3 BOM + newline", result)

    # F6: parse() returns list of lists
    r = parse_fn("a,b\n")
    assert_eq(isinstance(r, list), True, "F6.1 returns list", result)
    assert_eq(isinstance(r[0], list), True, "F6.2 each row is list", result)
    assert_eq(all(isinstance(f, str) for f in r[0]), True, "F6.3 each field is str", result)

    # F7: CLI interface (tested separately in run_cli_tests)
    #   covered by run_cli_tests()


# ---------------------------------------------------------------------------
# Section 2: Edge-case tests (TASK.md 边界情况)
# ---------------------------------------------------------------------------

def run_edge_tests(parse_fn: Callable[[str], List[List[str]]],
                    result: TestResult) -> None:
    """E1-E6: the six edge cases from TASK.md."""

    # E1: unclosed quotes
    assert_raises(ValueError, lambda: parse_fn('"a,b\n'), "E1.1 unclosed quote mid-file", result)
    assert_raises(ValueError, lambda: parse_fn('"a'), "E1.2 unclosed quote at EOF", result)
    assert_raises(ValueError, lambda: parse_fn('a,"b\nc\nd'), "E1.3 unclosed quote spanning lines", result)

    # E2: field leading/trailing spaces (RFC 4180: spaces are field content)
    assert_eq(parse_fn(" a , b \n"), [[" a ", " b "]], "E2.1 spaces preserved in unquoted fields", result)
    assert_eq(parse_fn('" a "," b "\n'), [[" a ", " b "]], "E2.2 spaces preserved in quoted fields", result)
    assert_eq(parse_fn("  a  \n"), [["  a  "]], "E2.3 single field with surrounding spaces", result)
    # E2.4: space after comma before a quote → quote is literal (RFC 4180)
    assert_eq(parse_fn('" a ", " b "\n'), [[" a ", ' " b "']], "E2.4 space-before-quote is literal", result)

    # E3: last line without trailing newline
    assert_eq(parse_fn("a,b\nc,d"), [["a", "b"], ["c", "d"]], "E3.1 last line no newline", result)
    assert_eq(parse_fn("a,b"), [["a", "b"]], "E3.2 single line no newline", result)
    assert_eq(parse_fn("a"), [["a"]], "E3.3 single field no newline", result)

    # E4: file with only newline(s)
    assert_eq(parse_fn("\n"), [[]], "E4.1 single newline", result)
    assert_eq(parse_fn("\n\n"), [[], []], "E4.2 two newlines", result)
    assert_eq(parse_fn("\n\n\n"), [[], [], []], "E4.3 three newlines", result)

    # E5: mixed line endings
    assert_eq(parse_fn("a,b\r\nc,d\ne,f\r"),
              [["a", "b"], ["c", "d"], ["e", "f"]],
              "E5.1 CRLF + LF + CR mixed", result)
    assert_eq(parse_fn("a\rb\nc\r\nd"),
              [["a"], ["b"], ["c"], ["d"]],
              "E5.2 CR + LF + CRLF mixed single-field", result)

    # E6: BOM + normal content (also in F5, here with multi-row + edge)
    assert_eq(parse_fn("\ufeffname,age\nAlice,30\nBob,25"),
              [["name", "age"], ["Alice", "30"], ["Bob", "25"]],
              "E6.1 BOM + multi-row no trailing newline", result)
    assert_eq(parse_fn("\ufeff\"a,b\"\n"), [["a,b"]], "E6.2 BOM + quoted field with comma", result)


# ---------------------------------------------------------------------------
# Section 3: Additional boundary & abnormal tests
# ---------------------------------------------------------------------------

def run_boundary_tests(parse_fn: Callable[[str], List[List[str]]],
                        result: TestResult) -> None:
    """B1-B8 + A1-A4: boundary values and abnormal inputs from coverage enum."""

    # B1: empty string
    assert_eq(parse_fn(""), [], "B1.1 empty string", result)

    # B2: BOM-only (covered in F5.2, re-verify with type check)
    r = parse_fn("\ufeff")
    assert_eq(r, [], "B2.1 BOM-only returns empty list", result)

    # B3: single field no comma
    assert_eq(parse_fn("hello\n"), [["hello"]], "B3.1 single field", result)
    assert_eq(parse_fn("hello"), [["hello"]], "B3.2 single field no newline", result)

    # B4: quoted empty field
    assert_eq(parse_fn('""\n'), [[""]], "B4.1 quoted empty field", result)
    assert_eq(parse_fn('a,"",b\n'), [["a", "", "b"]], "B4.2 quoted empty field between others", result)

    # B5: only escaped quotes  """"  →  a single "  (inside quotes: "" → ")
    assert_eq(parse_fn('""""\n'), [["\""]], "B5.1 four quotes = one literal quote", result)

    # B6: multiple consecutive blank lines
    assert_eq(parse_fn("a\n\n\n\nb\n"), [["a"], [], [], [], ["b"]], "B6.1 three blank lines between", result)

    # B7: trailing comma on last line (no newline)
    assert_eq(parse_fn("a,b,"), [["a", "b", ""]], "B7.1 trailing comma no newline", result)
    assert_eq(parse_fn("a,b,\n"), [["a", "b", ""]], "B7.2 trailing comma with newline", result)

    # B8: leading comma
    assert_eq(parse_fn(",a,b\n"), [["", "a", "b"]], "B8.1 leading comma", result)

    # A1-A2: unclosed quote (covered in E1, additional variants)
    assert_raises(ValueError, lambda: parse_fn('"'), "A1.1 single lone quote", result)
    assert_raises(ValueError, lambda: parse_fn('a,"b,c'), "A2.1 unclosed quote after comma", result)

    # Additional: quote in middle of unquoted field (literal)
    assert_eq(parse_fn('a"b,c\n'), [["a\"b", "c"]], "X1.1 quote in middle of unquoted field is literal", result)

    # Additional: content after closing quote
    assert_eq(parse_fn('"a"b,c\n'), [["ab", "c"]], "X2.1 content after closing quote", result)

    # Additional: large field (stress, 10000 chars)
    big = "x" * 10000
    assert_eq(parse_fn(big + "\n"), [[big]], "X3.1 large 10000-char field", result)

    # Additional: many rows (1000)
    many = "\n".join(f"r{i},v{i}" for i in range(1000))
    expected = [[f"r{i}", f"v{i}"] for i in range(1000)]
    assert_eq(parse_fn(many), expected, "X4.1 1000 rows", result)


# ---------------------------------------------------------------------------
# Section 4: Oracle cross-validation (against Python stdlib csv)
# ---------------------------------------------------------------------------

def run_oracle_tests(parse_fn: Callable[[str], List[List[str]]],
                      result: TestResult) -> None:
    """
    Multi-path cross-validation: for each test input, compare our parser
    output with Python stdlib csv.reader.  BOM inputs are excluded from
    direct comparison because TASK.md requires BOM stripping (stdlib csv
    does not strip BOM) — this is an intentional, documented difference.
    """
    oracle_inputs = [
        # (label, input_string)
        ("O01 basic", "a,b,c\n"),
        ("O02 quoted comma", '"a,b",c\n'),
        ("O03 quoted newline", '"a\nb",c\n'),
        ("O04 escaped quote", '"a""b",c\n'),
        ("O05 empty middle", "a,,b\n"),
        ("O06 empty leading", ",a,b\n"),
        ("O07 empty trailing", "a,b,\n"),
        ("O08 blank line", "a,b\n\nc,d\n"),
        ("O09 CRLF", "a,b\r\nc,d\r\n"),
        ("O10 CR only", "a,b\rc,d\r"),
        ("O11 mixed endings", "a\r\nb\nc\r"),
        ("O12 no trailing newline", "a,b\nc,d"),
        ("O13 single newline", "\n"),
        ("O14 two newlines", "\n\n"),
        ("O15 spaces", " a , b \n"),
        ("O16 quoted spaces", '" a ", " b "\n'),
        ("O17 quoted empty", '""\n'),
        ("O18 four quotes", '""""\n'),
        ("O19 single field", "hello\n"),
        ("O20 mixed quote types", 'a,"b,c",d\n'),
        ("O21 nested specials", '"a,b\nc""d",e\n'),
        ("O22 trailing comma", "a,b,\n"),
        ("O23 leading comma", ",a,b\n"),
        ("O24 only commas", ",,\n"),
        ("O25 quoted with CR inside", '"a\rb",c\n'),
        ("O26 large field", "x" * 5000 + "\n"),
        ("O27 many rows", "\n".join(f"r{i}" for i in range(500))),
        ("O28 content after quote", '"a"b,c\n'),
        ("O29 quote in middle", 'a"b,c\n'),
        ("O30 empty string", ""),
    ]

    diff_count = 0
    for label, text in oracle_inputs:
        ours = parse_fn(text)
        # Oracle: use csv.reader on StringIO (matches how files are read)
        oracle = list(csv.reader(io.StringIO(text, newline="")))
        if ours == oracle:
            result.ok(f"oracle.{label}")
        else:
            diff_count += 1
            result.fail(f"oracle.{label}",
                        f"mismatch:\n  ours   = {ours!r}\n  oracle = {oracle!r}")

    # Summary assertion: all oracle inputs must match (BOM excluded by design)
    if diff_count == 0:
        result.ok("oracle.summary_all_match")
    else:
        result.fail("oracle.summary_all_match", f"{diff_count} oracle mismatch(es)")


# ---------------------------------------------------------------------------
# Section 5: CLI tests
# ---------------------------------------------------------------------------

def run_cli_tests(module, result: TestResult) -> None:
    """Test the command-line interface (F7)."""
    import subprocess

    # Create a temp CSV file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False,
                                       encoding="utf-8", newline="") as f:
        f.write("name,age\nAlice,30\nBob,25\n")
        tmp_path = f.name

    try:
        # F7.1: normal file parse
        proc = subprocess.run(
            [sys.executable, PARSER_PATH, tmp_path],
            capture_output=True, text=True, timeout=10
        )
        if proc.returncode == 0 and "Alice" in proc.stdout and "Total: 3" in proc.stdout:
            result.ok("F7.1 CLI normal file")
        else:
            result.fail("F7.1 CLI normal file",
                        f"rc={proc.returncode}, stdout={proc.stdout!r}, stderr={proc.stderr!r}")

        # F7.2: missing file → exit code 1
        proc = subprocess.run(
            [sys.executable, PARSER_PATH, "nonexistent_file_xyz.csv"],
            capture_output=True, text=True, timeout=10
        )
        if proc.returncode == 1:
            result.ok("F7.2 CLI missing file returns 1")
        else:
            result.fail("F7.2 CLI missing file returns 1", f"rc={proc.returncode}")

        # F7.3: no arguments → exit code 2
        proc = subprocess.run(
            [sys.executable, PARSER_PATH],
            capture_output=True, text=True, timeout=10
        )
        if proc.returncode == 2:
            result.ok("F7.3 CLI no args returns 2")
        else:
            result.fail("F7.3 CLI no args returns 2", f"rc={proc.returncode}")

        # F7.4: unclosed quote in file → exit code 1
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False,
                                           encoding="utf-8", newline="") as f2:
            f2.write('"unclosed\n')
            bad_path = f2.name
        try:
            proc = subprocess.run(
                [sys.executable, PARSER_PATH, bad_path],
                capture_output=True, text=True, timeout=10
            )
            if proc.returncode == 1 and "Unclosed quote" in proc.stderr:
                result.ok("F7.4 CLI unclosed quote returns 1")
            else:
                result.fail("F7.4 CLI unclosed quote returns 1",
                            f"rc={proc.returncode}, stderr={proc.stderr!r}")
        finally:
            os.unlink(bad_path)

        # F7.5: BOM file via CLI
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False,
                                           encoding="utf-8-sig", newline="") as f3:
            f3.write("a,b\n")
            bom_path = f3.name
        try:
            proc = subprocess.run(
                [sys.executable, PARSER_PATH, bom_path],
                capture_output=True, text=True, timeout=10
            )
            if proc.returncode == 0 and "['a', 'b']" in proc.stdout:
                result.ok("F7.5 CLI BOM file parsed correctly")
            else:
                result.fail("F7.5 CLI BOM file parsed correctly",
                            f"rc={proc.returncode}, stdout={proc.stdout!r}")
        finally:
            os.unlink(bom_path)

    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Section 6: Mutation / anti-example testing
# ---------------------------------------------------------------------------
# This is the "通过率不是鉴别力" check: we inject known bugs into the
# parser and verify that the test suite catches each one.  If a mutated
# parser passes all tests, the suite has a blind spot for that bug class.

MUTATIONS: Dict[str, str] = {
    # M1: remove BOM stripping
    "M1_no_bom": textwrap.dedent("""\
        # BOM stripping removed by mutation
        pass
    """),
    # M2: remove CR handling (treat \\r as ordinary char)
    "M2_no_cr": textwrap.dedent("""\
        # CR handling removed by mutation: \\r treated as ordinary char
        pass
    """),
    # M3: remove escaped-quote handling ("" → ")
    "M3_no_escape": textwrap.dedent("""\
        # Escaped quote handling removed by mutation
        pass
    """),
    # M4: remove unclosed-quote detection
    "M4_no_unclosed": textwrap.dedent("""\
        # Unclosed quote detection removed by mutation
        pass
    """),
    # M5: strip spaces from fields
    "M5_strip_spaces": textwrap.dedent("""\
        # Space stripping added by mutation
        pass
    """),
    # M6: always append extra empty row at end
    "M6_extra_row": textwrap.dedent("""\
        # Extra empty row appended by mutation
        pass
    """),
}


def apply_mutation(source: str, mutation_id: str) -> str:
    """Return a mutated copy of the parser source."""
    if mutation_id == "M1_no_bom":
        # Remove the BOM check block
        source = source.replace(
            '    if text.startswith(BOM):\n        text = text[1:]\n',
            '    # BOM stripping removed by mutation\n'
        )
    elif mutation_id == "M2_no_cr":
        # Replace CR handling with ordinary char treatment
        source = source.replace(
            '''        if c == "\\r":
            # \\r\\n → one line ending; lone \\r → one line ending
            if i + 1 < n and text[i + 1] == "\\n":
                i += 2
            else:
                i += 1
            _end_row()
            continue''',
            '''        if c == "\\r":
            # CR handling removed: treat as ordinary char
            row_has_content = True
            field_chars.append(c)
            i += 1
            continue'''
        )
    elif mutation_id == "M3_no_escape":
        # Remove the escaped-quote "" check inside quotes
        source = source.replace(
            '''            if c == '"':
                # escaped quote "" → literal "
                if i + 1 < n and text[i + 1] == '"':
                    field_chars.append('"')
                    i += 2
                    continue
                # closing quote
                in_quotes = False
                i += 1
                continue''',
            '''            if c == '"':
                # Escaped quote handling removed: every " closes the field
                in_quotes = False
                i += 1
                continue'''
        )
    elif mutation_id == "M4_no_unclosed":
        # Remove the unclosed quote ValueError
        source = source.replace(
            '    if in_quotes:\n        raise ValueError("Unclosed quote in CSV input")\n',
            '    # Unclosed quote detection removed by mutation\n'
        )
    elif mutation_id == "M5_strip_spaces":
        # Add .strip() to field values in _end_field
        source = source.replace(
            '        row.append("".join(field_chars))',
            '        row.append("".join(field_chars).strip())  # MUTATION: strip spaces'
        )
    elif mutation_id == "M6_extra_row":
        # Append an extra empty row at the end
        source = source.replace(
            '    return rows\n',
            '    rows.append([])  # MUTATION: extra empty row\n    return rows\n'
        )
    return source


def run_mutation_tests(result: TestResult) -> None:
    """
    For each mutation: write a mutated parser, run the full test suite
    against it, and verify that at least one test FAILS.  If a mutation
    passes all tests, the suite has a blind spot → report as failure.
    """
    with open(PARSER_PATH, "r", encoding="utf-8") as f:
        original_source = f.read()

    for mutation_id in MUTATIONS:
        mutated_source = apply_mutation(original_source, mutation_id)

        # Write mutated parser to a temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False,
                                           encoding="utf-8") as f:
            f.write(mutated_source)
            mut_path = f.name

        try:
            # Load mutated parser
            mut_spec = importlib.util.spec_from_file_location(f"mut_{mutation_id}", mut_path)
            mut_mod = importlib.util.module_from_spec(mut_spec)
            try:
                mut_spec.loader.exec_module(mut_mod)
                mut_parse = mut_mod.parse
            except Exception as e:
                # Mutation caused a syntax/import error — that's also "caught"
                result.ok(f"mutation.{mutation_id}.caught (import error: {e})")
                continue

            # Run a SUBSET of tests against the mutated parser (fast, focused)
            # We run functional + edge + boundary (not CLI, not oracle for speed)
            mut_result = TestResult()
            run_functional_tests(mut_parse, mut_result)
            run_edge_tests(mut_parse, mut_result)
            run_boundary_tests(mut_parse, mut_result)

            if mut_result.all_pass:
                # BLIND SPOT: mutation passed all tests
                result.fail(f"mutation.{mutation_id}",
                            "BLIND SPOT: mutated parser passed all tests — suite cannot detect this bug class")
            else:
                caught = len(mut_result.failed) + len(mut_result.errors)
                result.ok(f"mutation.{mutation_id}.caught ({caught} test(s) failed)")
        finally:
            os.unlink(mut_path)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main() -> int:
    result = TestResult()

    print("=" * 70)
    print("CSV Parser Verification Suite")
    print(f"Parser: {PARSER_PATH}")
    print(f"Python: {sys.version}")
    print("=" * 70)

    # Load parser
    try:
        module = load_parser()
        parse_fn = module.parse
    except Exception as e:
        print(f"FATAL: cannot load parser: {e}")
        traceback.print_exc()
        return 1

    # Run all sections
    print("\n--- Section 1: Functional Tests (F1-F7) ---")
    run_functional_tests(parse_fn, result)

    print("\n--- Section 2: Edge-Case Tests (E1-E6) ---")
    run_edge_tests(parse_fn, result)

    print("\n--- Section 3: Boundary & Abnormal Tests (B1-B8, A1-A4, X) ---")
    run_boundary_tests(parse_fn, result)

    print("\n--- Section 4: Oracle Cross-Validation (vs stdlib csv) ---")
    run_oracle_tests(parse_fn, result)

    print("\n--- Section 5: CLI Tests ---")
    run_cli_tests(module, result)

    print("\n--- Section 6: Mutation / Anti-Example Tests ---")
    run_mutation_tests(result)

    # --- Report ---
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Total:  {result.total}")
    print(f"  Passed: {len(result.passed)}")
    print(f"  Failed: {len(result.failed)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Status: {'ALL GREEN' if result.all_pass else 'FAILURES DETECTED'}")

    if result.failed:
        print("\n--- FAILURES ---")
        for name, msg in result.failed:
            print(f"  FAIL: {name}")
            print(f"        {msg}")

    if result.errors:
        print("\n--- ERRORS ---")
        for name, tb in result.errors:
            print(f"  ERROR: {name}")
            print(f"         {tb}")

    # Write report file
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("CSV Parser Verification Report\n")
        f.write("=" * 70 + "\n")
        f.write(f"Parser: {PARSER_PATH}\n")
        f.write(f"Python: {sys.version}\n")
        f.write(f"Total: {result.total}, Passed: {len(result.passed)}, "
                f"Failed: {len(result.failed)}, Errors: {len(result.errors)}\n")
        f.write(f"Status: {'ALL GREEN' if result.all_pass else 'FAILURES DETECTED'}\n\n")
        if result.failed:
            f.write("FAILURES:\n")
            for name, msg in result.failed:
                f.write(f"  FAIL: {name}\n        {msg}\n")
        if result.errors:
            f.write("ERRORS:\n")
            for name, tb in result.errors:
                f.write(f"  ERROR: {name}\n         {tb}\n")
        f.write("\nAll passed test names:\n")
        for name in result.passed:
            f.write(f"  {name}\n")

    print(f"\nReport written to: {REPORT_PATH}")

    return 0 if result.all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
