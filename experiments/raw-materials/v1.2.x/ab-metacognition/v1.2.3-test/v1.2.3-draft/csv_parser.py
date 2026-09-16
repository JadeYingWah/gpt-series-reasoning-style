#!/usr/bin/env python3
"""csv_parser.py -- single-file, dependency-free CSV parser.

parse(text) -> list of rows, each row a list of str fields.

Semantics (RFC 4180 aligned):
- Comma-separated fields; a double-quoted field may contain commas,
  newlines (\n, \r\n, \r kept verbatim) and escaped quotes ("" -> ").
- Leading/trailing spaces of a field are kept verbatim (RFC 4180: spaces
  are part of the field and are not ignored). A quote only starts a
  quoted field when it is the first character of the field; otherwise it
  is taken as a literal character (lenient behaviour).
- Row separators: \n, \r\n and \r, mixable within one input.
- UTF-8 BOM: the CLI detects and skips a leading EF BB BF byte order
  mark; parse() also strips a leading U+FEFF character.
- Empty input -> []. A lone line break yields one empty row ([]).
- Unclosed quoted field -> ValueError.
"""

import sys

BOM = "\ufeff"


def parse(text):
    """Parse CSV text into a list of rows (list of list of str)."""
    if text.startswith(BOM):
        text = text[1:]

    rows = []
    row = []
    field = []
    field_started = False  # current row has produced content or a separator
    in_quotes = False
    i = 0
    n = len(text)

    while i < n:
        c = text[i]
        if in_quotes:
            if c == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"')  # "" escapes to a literal "
                    i += 2
                else:
                    in_quotes = False  # closing quote
                    i += 1
            else:
                field.append(c)  # commas / newlines kept verbatim
                i += 1
            continue

        if c == '"':
            in_quotes = True
            field_started = True
            i += 1
        elif c == ",":
            row.append("".join(field))
            field = []
            field_started = True  # a comma means the row continues
            i += 1
        elif c == "\n" or c == "\r":
            if field_started or row:
                row.append("".join(field))
            rows.append(row)
            row = []
            field = []
            field_started = False
            if c == "\r" and i + 1 < n and text[i + 1] == "\n":
                i += 2  # \r\n counts as a single row separator
            else:
                i += 1
        else:
            field.append(c)
            field_started = True
            i += 1

    if in_quotes:
        raise ValueError(
            "unclosed quote: quoted field not terminated before end of input"
        )

    if field_started or row:
        row.append("".join(field))  # last line without trailing newline
        rows.append(row)

    return rows


def main(argv):
    if len(argv) != 2:
        print("usage: python csv_parser.py <file.csv>", file=sys.stderr)
        return 2
    path = argv[1]
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as exc:
        print("error: cannot read %s: %s" % (path, exc), file=sys.stderr)
        return 1
    if data.startswith(b"\xef\xbb\xbf"):  # UTF-8 BOM: detect and skip
        data = data[3:]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        print("error: %s is not valid UTF-8: %s" % (path, exc), file=sys.stderr)
        return 1
    try:
        rows = parse(text)
    except ValueError as exc:
        print("error: %s: %s" % (path, exc), file=sys.stderr)
        return 1
    if hasattr(sys.stdout, "reconfigure"):
        # CLI may print non-ASCII UTF-8 content; force UTF-8 so Windows
        # pipe/locale code pages cannot crash the output step.
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for row in rows:
        print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
