#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md2html.py -- Markdown -> HTML converter. Single file, zero dependencies.

Supported (block level)
    * ATX headings      # .. ######          -> <h1> .. <h6>
    * fenced code       ``` [lang]           -> <pre><code class="language-lang">
    * unordered lists   - / * / +            -> <ul><li>
    * ordered lists     1. / 1)              -> <ol start="n"><li>
    * paragraphs        consecutive non-blank lines merged into one <p>

Supported (inline level, NOT applied inside fenced code or inline code)
    * inline code  `x`      -> <code>
    * bold         **x** __x__  -> <strong>
    * italic       *x*  _x_     -> <em>
    * links        [text](url)  -> <a href>

Deliberate behaviours / declared degradations (see EVIDENCE.md):
    D1  Fenced code content is emitted verbatim (no inline parsing); only
        & < > are escaped to entities (required for the output to be valid HTML).
    D2  An unterminated ``` fence runs to end of file.
    D3  A code span takes precedence over link recognition: "[`a`](u)" yields
        <code>a</code> plus the literal text "](u)", not a link.
    D4  A link URL may contain one level of balanced parentheses
        ([t](http://x/a(b)) works). Spaces inside a URL are percent-encoded
        (%20); the CommonMark angle form [t](<a b>) is also accepted.
    D5  "_" does not create emphasis inside a word (snake_case stays literal);
        "**" and "*" may appear inside a word.
    D6  A list marker alone on a line ("-" with no content) is NOT a list item
        (it becomes paragraph text).
    D7  A non-blank, non-item line following a list item is a lazy continuation
        of that item (indented or not); a blank line ends the list.
    D8  Nested lists are supported via indentation (tabs expanded to 4 spaces);
        nesting depth is unbounded; loose/tight distinction is not modelled and
        a dedent starts a new sibling list rather than merging back.
    D9  Only & < > are escaped in text; in attribute position " is escaped too.
        Setext headings, block quotes, tables, thematic breaks, images,
        reference links, autolinks and raw HTML blocks are out of scope.

CLI:
    python md2html.py <file.md>              full HTML document to stdout
    python md2html.py <file.md> --fragment   body fragment only
    python md2html.py <file.md> -o out.html  write to file instead of stdout
    echo '# hi' | python md2html.py -        read stdin
"""

from __future__ import annotations

import argparse
import itertools
import re
import sys

__version__ = "1.0.0"

# --------------------------------------------------------------------------
# block level patterns
# --------------------------------------------------------------------------

OPEN_FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,})[ \t]*([^`]*)$")
CLOSE_FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,})[ \t]*$")
HEADING_RE = re.compile(r"^(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
UL_ITEM_RE = re.compile(r"^(?P<ind>[ \t]*)[-*+][ \t]+(?P<content>.*)$")
OL_ITEM_RE = re.compile(r"^(?P<ind>[ \t]*)(?P<num>\d{1,9})[.)][ \t]+(?P<content>.*)$")
TRAILING_HASH_RE = re.compile(r"[ \t]+#+[ \t]*$")

# inline level patterns
# URL: angle form <...> | a run allowing one level of balanced parentheses
LINK_RE = re.compile(
    r"\[(?P<text>.+?)\][ \t]*\([ \t]*(?P<url><[^>]*>|"
    r"(?:[^()]|\([^()]*\))*?)[ \t]*\)")
# emphasis delimiters may not be separated from their content by whitespace
BOLD_STAR_RE = re.compile(r"\*\*(?P<c>\S(?:[\s\S]*?\S)?)\*\*")
BOLD_UNDER_RE = re.compile(r"(?<![\w])__(?P<c>\S(?:[\s\S]*?\S)?)__(?![\w])")
ITALIC_STAR_RE = re.compile(r"\*(?P<c>[^\s*](?:[^*\n]*?[^\s*])?)\*")
ITALIC_UNDER_RE = re.compile(r"(?<![\w])_(?P<c>[^\s_](?:[^_\n]*?[^\s_])?)_(?![\w])")

_SLOT_IDS = itertools.count()


class _Slots:
    """Holds rendered HTML fragments behind unique placeholder tokens.

    The token carries the slot-set id, so nested renders (bold -> italic,
    link -> inner inline) can never overwrite or restore each other's
    fragments. Tokens use NUL, which cannot appear in normal text.
    """

    __slots__ = ("sid", "items")

    def __init__(self):
        self.sid = next(_SLOT_IDS)
        self.items = []

    def protect(self, html_text: str) -> str:
        self.items.append(html_text)
        return "\x00%d:%d\x00" % (self.sid, len(self.items) - 1)

    def restore(self, s: str) -> str:
        if not self.items:
            return s
        prefix = "\x00%d:" % self.sid
        out = []
        pos = 0
        while True:
            i = s.find(prefix, pos)
            if i < 0:
                break
            j = s.find("\x00", i + len(prefix))
            if j < 0:
                break
            try:
                frag = self.items[int(s[i + len(prefix):j])]
            except (ValueError, IndexError):
                pos = j + 1
                continue
            out.append(s[pos:i])
            out.append(frag)
            pos = j + 1
        out.append(s[pos:])
        return "".join(out)


# --------------------------------------------------------------------------
# escaping
# --------------------------------------------------------------------------

def escape_text(s: str) -> str:
    """Escape the three characters required by the task: & < >."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_attr(s: str) -> str:
    """Escape for an HTML attribute value, and percent-encode spaces."""
    s = escape_text(s).replace('"', "&quot;")
    return s.replace(" ", "%20")


# --------------------------------------------------------------------------
# inline level
# --------------------------------------------------------------------------

def _split_code_spans(text: str):
    """Split text into [('plain'|'code', chunk), ...] on inline code spans."""
    segments = []
    plain_start = 0
    i = 0
    n = len(text)
    close_cache = {}
    while i < n:
        if text[i] != "`":
            i += 1
            continue
        j = i
        while j < n and text[j] == "`":
            j += 1
        ticks = text[i:j]
        close_re = close_cache.get(ticks)
        if close_re is None:
            close_re = re.compile(re.escape(ticks) + "(?!`)")
            close_cache[ticks] = close_re
        m = close_re.search(text, j)
        if m is None:  # unmatched backticks -> literal
            i = j
            continue
        if i > plain_start:
            segments.append(("plain", text[plain_start:i]))
        segments.append(("code", text[j:m.start()]))
        i = m.end()
        plain_start = i
    if plain_start < n:
        segments.append(("plain", text[plain_start:]))
    return segments


def _italic(s: str) -> str:
    slots = _Slots()
    s = ITALIC_STAR_RE.sub(lambda m: slots.protect("<em>" + m.group("c") + "</em>"), s)
    s = ITALIC_UNDER_RE.sub(lambda m: slots.protect("<em>" + m.group("c") + "</em>"), s)
    return slots.restore(s)


def _emphasis(s: str) -> str:
    """Apply bold then italic on already-escaped text."""
    slots = _Slots()

    def strong(m):
        return slots.protect("<strong>" + _italic(m.group("c")) + "</strong>")

    s = BOLD_STAR_RE.sub(strong, s)
    s = BOLD_UNDER_RE.sub(strong, s)
    s = _italic(s)
    return slots.restore(s)


def _render_plain(text: str, allow_links: bool = True) -> str:
    """Escape + links + emphasis for a chunk that contains no code span."""
    if not allow_links:
        return _emphasis(escape_text(text))

    slots = _Slots()
    out = []
    pos = 0
    while True:
        m = LINK_RE.search(text, pos)
        if m is None:
            break
        out.append(escape_text(text[pos:m.start()]))
        raw_url = m.group("url")
        if raw_url.startswith("<") and raw_url.endswith(">") and len(raw_url) >= 2:
            raw_url = raw_url[1:-1]
        inner = render_inline(m.group("text"), allow_links=False)
        out.append(slots.protect('<a href="%s">%s</a>' % (escape_attr(raw_url), inner)))
        pos = m.end()
    out.append(escape_text(text[pos:]))
    # Emphasis runs over the whole (masked + escaped) chunk so that delimiters
    # on both sides of a link still pair up: **[t](u)** -> <strong><a..></strong>
    return slots.restore(_emphasis("".join(out)))


def render_inline(text: str, allow_links: bool = True) -> str:
    """Render inline markdown. Code spans win over everything else (D3)."""
    parts = []
    for kind, chunk in _split_code_spans(text):
        if kind == "code":
            parts.append("<code>" + escape_text(chunk) + "</code>")
        else:
            parts.append(_render_plain(chunk, allow_links))
    return "".join(parts)


# --------------------------------------------------------------------------
# list rendering
# --------------------------------------------------------------------------

class _Item:
    __slots__ = ("indent", "tag", "start", "lines")

    def __init__(self, indent, tag, start, first_line):
        self.indent = indent
        self.tag = tag
        self.start = start
        self.lines = [first_line]


def _indent_width(s: str) -> int:
    return len(s.expandtabs(4))


def _list_open_attr(item) -> str:
    if item.tag == "ol" and item.start != "1":
        return 'ol start="%s"' % escape_attr(item.start)
    return item.tag


def _render_list(items, pos, indent):
    tag = items[pos].tag
    out = ["<%s>" % _list_open_attr(items[pos])]
    while pos < len(items):
        it = items[pos]
        if it.indent < indent:
            break
        if it.indent > indent:
            nested, pos = _render_list(items, pos, it.indent)
            if out[-1].endswith("</li>"):
                out[-1] = out[-1][:-len("</li>")] + "\n" + nested + "</li>"
            else:  # nested list as the very first child -- keep it anyway
                out.append(nested)
            continue
        if it.tag != tag:
            break
        out.append("<li>" + render_inline("\n".join(it.lines)) + "</li>")
        pos += 1
    out.append("</%s>" % tag)
    return "\n".join(out), pos


def _read_list_block(lines, i):
    items = []
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n and (UL_ITEM_RE.match(lines[j]) or OL_ITEM_RE.match(lines[j])
                          or (items and lines[j][:1] in (" ", "\t"))):
                i = j
                continue
            i = j
            break
        m = UL_ITEM_RE.match(line)
        tag = "ul"
        start = "1"
        if m is None:
            m = OL_ITEM_RE.match(line)
            tag = "ol"
            if m is not None:
                start = str(int(m.group("num")))
        if m is not None:
            items.append(_Item(_indent_width(m.group("ind")), tag, start,
                               m.group("content")))
            i += 1
        elif items and line[:1] in (" ", "\t"):  # lazy continuation (D7)
            items[-1].lines.append(line.strip())
            i += 1
        else:
            break
    return items, i


def _render_items(items) -> str:
    out = []
    pos = 0
    while pos < len(items):
        html_text, pos = _render_list(items, pos, items[pos].indent)
        out.append(html_text)
    return "\n".join(out)


# --------------------------------------------------------------------------
# block level
# --------------------------------------------------------------------------

def convert(md_text: str, fragment: bool = False, title: str | None = None) -> str:
    """Convert markdown text to HTML."""
    if md_text.startswith("\ufeff"):  # strip a UTF-8 BOM if the caller kept it
        md_text = md_text[1:]
    lines = md_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines and lines[-1] == "":  # a trailing newline does not create a line
        lines.pop()
    body: list = []
    i = 0
    n = len(lines)
    first_h1 = None

    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        fm = OPEN_FENCE_RE.match(line)
        if fm:
            marker = fm.group(1)
            lang = fm.group(2).strip()
            i += 1
            buf = []
            while i < n:
                cm = CLOSE_FENCE_RE.match(lines[i])
                if cm and len(cm.group(1)) >= len(marker):
                    i += 1
                    break
                buf.append(lines[i])
                i += 1
            cls = ""
            info = lang.split()[0] if lang else ""
            if info:
                cls = ' class="language-%s"' % escape_attr(info)
            code = "\n".join(escape_text(x) for x in buf)  # D1
            body.append("<pre><code%s>%s</code></pre>" % (cls, code))
            continue

        hm = HEADING_RE.match(line)
        if hm:
            level = len(hm.group(1))
            content = hm.group(2) or ""
            content = TRAILING_HASH_RE.sub("", content)
            if level == 1 and first_h1 is None:
                first_h1 = content
            body.append("<h%d>%s</h%d>" % (level, render_inline(content), level))
            i += 1
            continue

        if UL_ITEM_RE.match(line) or OL_ITEM_RE.match(line):
            items, i = _read_list_block(lines, i)
            body.append(_render_items(items))
            continue

        # paragraph: consecutive non-blank lines that start no other block
        para = []
        while i < n:
            cur = lines[i]
            if not cur.strip():
                break
            if OPEN_FENCE_RE.match(cur) or HEADING_RE.match(cur) \
                    or UL_ITEM_RE.match(cur) or OL_ITEM_RE.match(cur):
                break
            para.append(cur)
            i += 1
        body.append("<p>" + render_inline("\n".join(para)) + "</p>")

    if fragment:
        return "\n".join(body)

    doc_title = title if title is not None else (escape_text(first_h1) if first_h1 else "Document")
    return (
        '<!DOCTYPE html>\n'
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>%s</title>\n</head>\n<body>\n%s\n</body>\n</html>\n'
    ) % (doc_title, "\n".join(body))


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="md2html.py", description="Markdown -> HTML (single file, zero deps)")
    parser.add_argument("file", help="path to .md file ('-' for stdin)")
    parser.add_argument("--fragment", action="store_true",
                        help="emit the body fragment instead of a full document")
    parser.add_argument("-o", "--output", help="write to this file instead of stdout")
    parser.add_argument("--version", action="version", version="md2html.py " + __version__)
    args = parser.parse_args(argv)

    try:
        if args.file == "-":
            raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        else:
            with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
                raw = fh.read()
    except OSError as exc:
        print("md2html.py: cannot read %s: %s" % (args.file, exc), file=sys.stderr)
        return 1

    out = convert(raw, fragment=args.fragment)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(out)
        except OSError as exc:
            print("md2html.py: cannot write %s: %s" % (args.output, exc), file=sys.stderr)
            return 1
        return 0

    try:
        sys.stdout.buffer.write(out.encode("utf-8"))
        sys.stdout.buffer.flush()
    except (AttributeError, ValueError):  # pragma: no cover - non-standard stdout
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
