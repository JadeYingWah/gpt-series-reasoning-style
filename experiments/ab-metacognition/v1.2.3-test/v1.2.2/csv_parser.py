#!/usr/bin/env python3
"""
CSV Parser — single file, zero external dependencies.

Compliant with RFC 4180.  Handles all edge cases listed in TASK.md:
  - quoted fields containing commas / newlines / escaped quotes ("")
  - empty fields and empty lines
  - line endings \\n, \\r\\n, \\r (including mixed)
  - UTF-8 BOM detection and skipping
  - unclosed quotes → ValueError
  - leading / trailing spaces preserved (RFC 4180: spaces are field content)
  - last line without trailing newline
  - file consisting only of newline(s)

Usage:
    python csv_parser.py <file.csv>      # pretty-print parsed rows
    from csv_parser import parse          # library API
"""

from __future__ import annotations

import sys
from typing import List

BOM = "\ufeff"


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------

def parse(text: str) -> List[List[str]]:
    """Parse *text* as CSV and return ``list[list[str]]``.

    Raises ``ValueError`` on an unclosed double-quote.
    """
    # --- UTF-8 BOM ---------------------------------------------------------
    if text.startswith(BOM):
        text = text[1:]

    if not text:
        return []

    # --- state --------------------------------------------------------------
    rows: List[List[str]] = []
    row: List[str] = []
    field_chars: List[str] = []
    in_quotes = False
    row_has_content = False  # True once any non-line-ending char is seen

    i = 0
    n = len(text)

    # --- helpers (closure over state) --------------------------------------
    def _end_field() -> None:
        nonlocal field_chars
        row.append("".join(field_chars))
        field_chars = []

    def _end_row() -> None:
        nonlocal row, row_has_content
        if row_has_content:
            _end_field()
            rows.append(row)
        else:
            # truly blank line (no characters before line ending) → []
            rows.append([])
        row = []
        row_has_content = False

    # --- main loop (character-level state machine) -------------------------
    while i < n:
        c = text[i]

        if in_quotes:
            row_has_content = True
            if c == '"':
                # escaped quote "" → literal "
                if i + 1 < n and text[i + 1] == '"':
                    field_chars.append('"')
                    i += 2
                    continue
                # closing quote
                in_quotes = False
                i += 1
                continue
            # any other char (comma, newline, etc.) is literal inside quotes
            field_chars.append(c)
            i += 1
            continue

        # not in quotes -------------------------------------------------------
        if c == '"':
            row_has_content = True
            # a quote only opens a quoted field when it is the first char
            # of the field (RFC 4180); otherwise it is literal text.
            if not field_chars:
                in_quotes = True
                i += 1
                continue
            field_chars.append(c)
            i += 1
            continue

        if c == ",":
            row_has_content = True
            _end_field()
            i += 1
            continue

        if c == "\r":
            # \r\n → one line ending; lone \r → one line ending
            if i + 1 < n and text[i + 1] == "\n":
                i += 2
            else:
                i += 1
            _end_row()
            continue

        if c == "\n":
            i += 1
            _end_row()
            continue

        # ordinary character (spaces, letters, digits, etc.)
        row_has_content = True
        field_chars.append(c)
        i += 1

    # --- post-loop ----------------------------------------------------------
    if in_quotes:
        raise ValueError("Unclosed quote in CSV input")

    # If the text does *not* end with a line terminator, the last row
    # has not been flushed yet.
    if text and text[-1] not in "\r\n":
        _end_row()

    return rows


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv: List[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: python {argv[0]} <file.csv>", file=sys.stderr)
        return 2

    path = argv[1]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1
    except UnicodeDecodeError as exc:
        print(f"Error: file is not valid UTF-8: {exc}", file=sys.stderr)
        return 1

    try:
        rows = parse(text)
    except ValueError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 1

    for idx, row in enumerate(rows):
        print(f"Row {idx}: {row!r}")
    print(f"Total: {len(rows)} row(s)")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
