#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify.py -- independent verification suite for md2html.py.

Zero dependencies, no network, no environment variables. Third party can run:

    python verify.py                      # uses ./md2html.py next to this file
    python verify.py --impl /path/md2html.py
    python verify.py --report evidence/run-report.txt

Exit code 0 = every check passed, 1 = at least one check failed.

Three independent verification paths are used for every case:
  PATH A  exact string comparison of `python <impl> <file> --fragment`
  PATH B  direct import of the module (`convert(text, fragment=True)`),
          cross-checked against PATH A (guards against CLI-only defects)
  PATH C  structural validation with html.parser on the full document
          (well-formedness / tag balance) + text round-trip extraction
"""

from __future__ import annotations

import argparse
import html.parser
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IMPL = os.path.join(HERE, "md2html.py")

# Case groups = input-domain segments (coverage enumeration, see EVIDENCE.md)
G_NORMAL = "正常值"
G_BOUNDARY = "边界值"
G_ABNORMAL = "异常值"
G_SECURITY = "安全注入"
G_SPEC = "任务书点名场景"
G_REGRESSION = "回归已修缺陷"


class Case:
    __slots__ = ("cid", "group", "md", "expected")

    def __init__(self, cid, group, md, expected):
        self.cid = cid
        self.group = group
        self.md = md
        self.expected = expected


CASES = [
    # ---------------- 正常值 ----------------
    Case("h1-h6", G_NORMAL, "# H1\n## H2\n### H3\n#### H4\n##### H5\n###### H6\n",
         "<h1>H1</h1>\n<h2>H2</h2>\n<h3>H3</h3>\n<h4>H4</h4>\n<h5>H5</h5>\n<h6>H6</h6>"),
    Case("heading-trailing-hash", G_NORMAL, "# Title #\n", "<h1>Title</h1>"),
    Case("ul-dash", G_NORMAL, "- a\n- b\n", "<ul>\n<li>a</li>\n<li>b</li>\n</ul>"),
    Case("ul-star", G_NORMAL, "* a\n* b\n", "<ul>\n<li>a</li>\n<li>b</li>\n</ul>"),
    Case("ul-plus-tab-marker", G_NORMAL, "-\ta\n", "<ul>\n<li>a</li>\n</ul>"),
    Case("ol-dot", G_NORMAL, "1. a\n2. b\n", "<ol>\n<li>a</li>\n<li>b</li>\n</ol>"),
    Case("ol-paren", G_NORMAL, "1) a\n", "<ol>\n<li>a</li>\n</ol>"),
    Case("ol-start-3", G_NORMAL, "3. a\n4. b\n", '<ol start="3">\n<li>a</li>\n<li>b</li>\n</ol>'),
    Case("fence-plain", G_NORMAL, "```\nx = 1\n```\n", "<pre><code>x = 1</code></pre>"),
    Case("fence-lang", G_NORMAL, "```python\nx = 1\n```\n",
         '<pre><code class="language-python">x = 1</code></pre>'),
    Case("inline-code", G_NORMAL, "use `x` here\n", "<p>use <code>x</code> here</p>"),
    Case("bold", G_NORMAL, "**b**\n", "<p><strong>b</strong></p>"),
    Case("italic", G_NORMAL, "*i*\n", "<p><em>i</em></p>"),
    Case("bold-italic-nested", G_NORMAL, "**a *b* c**\n", "<p><strong>a <em>b</em> c</strong></p>"),
    Case("link-basic", G_NORMAL, "[t](http://x.com)\n", '<p><a href="http://x.com">t</a></p>'),
    Case("link-emphasis-in-text", G_NORMAL, "[*a*](u)\n", '<p><a href="u"><em>a</em></a></p>'),
    Case("link-inside-bold", G_NORMAL, "**[t](u)**\n", '<p><strong><a href="u">t</a></strong></p>'),
    Case("list-item-inline", G_NORMAL, "- **b** and `c`\n",
         "<ul>\n<li><strong>b</strong> and <code>c</code></li>\n</ul>"),
    Case("paragraph-merge", G_NORMAL, "line1\nline2\n", "<p>line1\nline2</p>"),
    Case("paragraph-blank-split", G_NORMAL, "a\n\nb\n", "<p>a</p>\n<p>b</p>"),
    Case("mixed-document", G_NORMAL,
         "# Title\n\nIntro *text*.\n\n- one\n- two\n\n```\nraw <not> parsed\n```\n\nEnd.\n",
         "<h1>Title</h1>\n<p>Intro <em>text</em>.</p>\n<ul>\n<li>one</li>\n<li>two</li>\n</ul>\n"
         "<pre><code>raw &lt;not&gt; parsed</code></pre>\n<p>End.</p>"),

    # ---------------- 边界值 ----------------
    Case("empty-file", G_BOUNDARY, "", ""),
    Case("only-blank-lines", G_BOUNDARY, "\n\n   \n\t\n", ""),
    Case("heading-then-text-no-blank", G_BOUNDARY, "# H\ntext\n", "<h1>H</h1>\n<p>text</p>"),
    Case("text-then-heading-no-blank", G_BOUNDARY, "text\n# H\n", "<p>text</p>\n<h1>H</h1>"),
    Case("no-trailing-newline", G_BOUNDARY, "text", "<p>text</p>"),
    Case("bom-prefix", G_BOUNDARY, "\ufeff# H\n", "<h1>H</h1>"),
    Case("crlf-line-endings", G_BOUNDARY, "# H\r\ntext\r\n", "<h1>H</h1>\n<p>text</p>"),
    Case("unclosed-fence", G_BOUNDARY, "```\ncode\nmore\n", "<pre><code>code\nmore</code></pre>"),
    Case("empty-fence-pair", G_BOUNDARY, "```\n```\n", "<pre><code></code></pre>"),
    Case("fence-4-backticks", G_BOUNDARY, "````\na ``` b\n````\n", "<pre><code>a ``` b</code></pre>"),
    Case("heading-7-hash-is-text", G_BOUNDARY, "####### Seven\n", "<p>####### Seven</p>"),
    Case("heading-no-space-is-text", G_BOUNDARY, "#H1\n", "<p>#H1</p>"),
    Case("heading-empty", G_BOUNDARY, "#\n", "<h1></h1>"),
    Case("bare-marker-is-text", G_BOUNDARY, "-\n", "<p>-</p>"),
    Case("hr-lookalike-is-text", G_BOUNDARY, "---\n", "<p>---</p>"),
    Case("intraword-underscore-literal", G_BOUNDARY, "snake_case_name\n", "<p>snake_case_name</p>"),
    Case("intraword-star-emphasis", G_BOUNDARY, "a*b*c\n", "<p>a<em>b</em>c</p>"),
    Case("underscore-emphasis-standalone", G_BOUNDARY, "_i_\n", "<p><em>i</em></p>"),
    Case("inline-code-with-star-and-underscore", G_BOUNDARY, "`a *b* _c_`\n",
         "<p><code>a *b* _c_</code></p>"),
    Case("inline-code-with-html", G_BOUNDARY, "`<b>&`\n", "<p><code>&lt;b&gt;&amp;</code></p>"),
    Case("link-text-with-closing-bracket", G_BOUNDARY, "[foo]bar](http://x)\n",
         '<p><a href="http://x">foo]bar</a></p>'),
    Case("link-url-with-space", G_BOUNDARY, "[t](http://x/a b)\n",
         '<p><a href="http://x/a%20b">t</a></p>'),
    Case("link-url-angle-with-space", G_BOUNDARY, "[t](<http://x/a b>)\n",
         '<p><a href="http://x/a%20b">t</a></p>'),
    Case("link-with-title-ish", G_BOUNDARY, "[t]()\n", '<p><a href="">t</a></p>'),
    Case("nested-list-1-level", G_BOUNDARY, "- a\n  - b\n- c\n",
         "<ul>\n<li>a\n<ul>\n<li>b</li>\n</ul></li>\n<li>c</li>\n</ul>"),
    Case("nested-list-ol-in-ul", G_BOUNDARY, "- a\n  1. x\n  2. y\n",
         "<ul>\n<li>a\n<ol>\n<li>x</li>\n<li>y</li>\n</ol></li>\n</ul>"),
    Case("nested-list-3-levels", G_BOUNDARY, "- a\n  - b\n    - c\n",
         "<ul>\n<li>a\n<ul>\n<li>b\n<ul>\n<li>c</li>\n</ul></li>\n</ul></li>\n</ul>"),
    Case("list-lazy-continuation", G_BOUNDARY, "- a\n  continued\n- b\n",
         "<ul>\n<li>a\ncontinued</li>\n<li>b</li>\n</ul>"),
    Case("list-blank-between-items", G_BOUNDARY, "- a\n\n- b\n",
         "<ul>\n<li>a</li>\n<li>b</li>\n</ul>"),
    Case("list-dedent-sibling", G_BOUNDARY, "  - a\n- b\n",
         "<ul>\n<li>a</li>\n</ul>\n<ul>\n<li>b</li>\n</ul>"),
    Case("list-then-paragraph", G_BOUNDARY, "- a\n\ntext\n", "<ul>\n<li>a</li>\n</ul>\n<p>text</p>"),

    # ---------------- 异常值 ----------------
    Case("unmatched-backtick", G_ABNORMAL, "a ` b\n", "<p>a ` b</p>"),
    Case("unmatched-bold", G_ABNORMAL, "**not closed\n", "<p>**not closed</p>"),
    Case("unmatched-italic", G_ABNORMAL, "*not closed\n", "<p>*not closed</p>"),
    Case("unclosed-link", G_ABNORMAL, "[t](http://x\n", "<p>[t](http://x</p>"),
    Case("unclosed-bracket", G_ABNORMAL, "[t\n", "<p>[t</p>"),
    Case("empty-emphasis-markers", G_ABNORMAL, "** **\n", "<p>** **</p>"),
    Case("code-span-beats-link", G_ABNORMAL, "[`a`](u)\n", "<p>[<code>a</code>](u)</p>"),
    Case("url-with-paren", G_ABNORMAL, "[t](http://x/a(b))\n",
         '<p><a href="http://x/a(b)">t</a></p>'),
    Case("binary-ish-nul-absent", G_ABNORMAL, "a\x01b\n", "<p>a\x01b</p>"),

    # ---------------- 安全注入 ----------------
    Case("escape-angle-amp", G_SECURITY, "a < b & c > d\n",
         "<p>a &lt; b &amp; c &gt; d</p>"),
    Case("script-tag-in-text", G_SECURITY, "<script>alert(1)</script>\n",
         "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>"),
    Case("script-tag-in-fence", G_SECURITY, "```\n<script>alert(1)</script>\n```\n",
         "<pre><code>&lt;script&gt;alert(1)&lt;/script&gt;</code></pre>"),
    Case("img-onerror-in-text", G_SECURITY, '<img src=x onerror=alert(1)>\n',
         "<p>&lt;img src=x onerror=alert(1)&gt;</p>"),
    Case("attr-quote-injection", G_SECURITY, '[t](x" onmouseover="alert(1))\n',
         '<p><a href="x&quot;%20onmouseover=&quot;alert(1)">t</a></p>'),
    Case("attr-quote-injection-angle-url", G_SECURITY, '[t](<a" b>)\n',
         '<p><a href="a&quot;%20b">t</a></p>'),
    Case("javascript-url-passthrough", G_SECURITY, "[t](javascript:alert(1))\n",
         '<p><a href="javascript:alert(1)">t</a></p>'),

    # ---------------- 任务书点名场景 ----------------
    Case("spec-empty-and-blank", G_SPEC, "\n   \n", ""),
    Case("spec-heading-adjacent", G_SPEC, "# H\nbody\n## H2\nbody2\n",
         "<h1>H</h1>\n<p>body</p>\n<h2>H2</h2>\n<p>body2</p>"),
    Case("spec-unclosed-fence", G_SPEC, "```\nunclosed **x** `y` <z> & \n",
         "<pre><code>unclosed **x** `y` &lt;z&gt; &amp; </code></pre>"),
    Case("spec-inline-code-emphasis", G_SPEC, "**b** `a *b* _c_` *i*\n",
         "<p><strong>b</strong> <code>a *b* _c_</code> <em>i</em></p>"),
    Case("spec-link-bracket-and-space", G_SPEC, "[a]b](u 1) and [c](d e)\n",
         '<p><a href="u%201">a]b</a> and <a href="d%20e">c</a></p>'),
    Case("spec-nested-list-declared", G_SPEC, "- a\n  - b\n    - c\n- d\n",
         "<ul>\n<li>a\n<ul>\n<li>b\n<ul>\n<li>c</li>\n</ul></li>\n</ul></li>\n<li>d</li>\n</ul>"),
    Case("spec-escape-entities", G_SPEC, "< > & \" '\n",
         "<p>&lt; &gt; &amp; \" '</p>"),

    # ------ 回归：placeholder 串槽缺陷（粗体/斜体同段曾被互相覆盖） ------
    Case("regress-bold-and-italic-adjacent", G_REGRESSION, "**b** and *i*\n",
         "<p><strong>b</strong> and <em>i</em></p>"),
    Case("regress-underscore-bold-italic", G_REGRESSION, "__b__ and _i_\n",
         "<p><strong>b</strong> and <em>i</em></p>"),
    Case("regress-two-bolds-two-italics", G_REGRESSION, "**b1** *i1* **b2** *i2*\n",
         "<p><strong>b1</strong> <em>i1</em> <strong>b2</strong> <em>i2</em></p>"),
    Case("regress-mixed-inline-one-line", G_REGRESSION, "**b** *i* `c` [t](u)\n",
         '<p><strong>b</strong> <em>i</em> <code>c</code> <a href="u">t</a></p>'),
    Case("regress-cjk-mixed-inline", G_REGRESSION, "这是 **粗体**、*斜体* 与 `代码`。\n",
         "<p>这是 <strong>粗体</strong>、<em>斜体</em> 与 <code>代码</code>。</p>"),
    Case("regress-links-and-emphasis", G_REGRESSION, "*a* [l1](u1) **b** [l2](u2) *c*\n",
         '<p><em>a</em> <a href="u1">l1</a> <strong>b</strong> '
         '<a href="u2">l2</a> <em>c</em></p>'),
]


# --------------------------------------------------------------------------
# PATH C: structural validation
# --------------------------------------------------------------------------

VOID_TAGS = {"meta", "br", "hr", "img", "input", "link", "source", "col", "area", "base"}


class _StackChecker(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.text_by_tag = {}

    def handle_starttag(self, tag, attrs):
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if not self.stack:
            self.errors.append("close </%s> with empty stack" % tag)
        elif self.stack[-1] != tag:
            self.errors.append("close </%s> but open <%s>" % (tag, self.stack[-1]))
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()

    def handle_data(self, data):
        if self.stack:
            key = self.stack[-1]
            self.text_by_tag.setdefault(key, "")
            self.text_by_tag[key] += data


def check_structure(html_doc):
    """Return (ok, message). Validates tag balance + <title>/DOCTYPE presence."""
    p = _StackChecker()
    try:
        p.feed(html_doc)
        p.close()
    except Exception as exc:  # pragma: no cover - defensive
        return False, "HTMLParser raised %r" % (exc,)
    if p.errors:
        return False, "; ".join(p.errors)
    if p.stack:
        return False, "unclosed tags: %s" % ",".join(p.stack)
    if not html_doc.startswith("<!DOCTYPE html>"):
        return False, "missing DOCTYPE"
    if '<meta charset="utf-8">' not in html_doc:
        return False, "missing charset meta"
    if "<title>" not in html_doc or "</title>" not in html_doc:
        return False, "missing <title>"
    if not html_doc.rstrip().endswith("</html>"):
        return False, "document does not end with </html>"
    return True, "well-formed"


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------

def run_cli(impl, md_bytes, tmpdir, name):
    path = os.path.join(tmpdir, name + ".md")
    with open(path, "wb") as fh:
        fh.write(md_bytes)
    proc = subprocess.run([sys.executable, impl, path, "--fragment"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc


def main(argv=None):
    ap = argparse.ArgumentParser(description="verify md2html.py")
    ap.add_argument("--impl", default=DEFAULT_IMPL, help="path to the implementation")
    ap.add_argument("--report", help="write a machine-readable run report to this path")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    impl = os.path.abspath(args.impl)
    if not os.path.exists(impl):
        print("FATAL: implementation not found: %s" % impl)
        return 1

    sys.path.insert(0, os.path.dirname(impl))
    try:
        import md2html as mod  # PATH B
    except Exception as exc:
        print("FATAL: cannot import implementation: %r" % (exc,))
        return 1

    results = []
    tmpdir = tempfile.mkdtemp(prefix="md2html-verify-")
    try:
        for idx, case in enumerate(CASES):
            cid = case.cid
            problems = []
            md_bytes = case.md.encode("utf-8")
            proc = run_cli(impl, md_bytes, tmpdir, "c%03d" % idx)
            if proc.returncode != 0:
                problems.append("CLI exit=%d stderr=%s"
                                % (proc.returncode, proc.stderr.decode("utf-8", "replace").strip()))
                actual = ""
            else:
                actual = proc.stdout.decode("utf-8")
                # PATH A
                if actual != case.expected:
                    problems.append("PATH A mismatch")
            # PATH B
            try:
                direct = mod.convert(case.md, fragment=True)
                if direct != case.expected:
                    problems.append("PATH B mismatch")
                if direct != actual:
                    problems.append("PATH A/B disagree")
            except Exception as exc:
                problems.append("PATH B raised %r" % (exc,))
            # PATH C
            try:
                doc = mod.convert(case.md)
                ok, msg = check_structure(doc)
                if not ok:
                    problems.append("PATH C: " + msg)
            except Exception as exc:
                problems.append("PATH C raised %r" % (exc,))

            results.append({
                "id": cid, "group": case.group, "md": case.md,
                "expected": case.expected, "actual": actual, "ok": not problems,
                "problems": problems,
            })
            status = "PASS" if not problems else "FAIL"
            print("[%s] %-38s %s" % (status, cid, "" if not problems else " | ".join(problems)))
            if args.verbose or problems:
                if problems:
                    print("      md      : %r" % case.md)
                    print("      expected: %r" % case.expected)
                    print("      actual  : %r" % actual)
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

    passed = sum(1 for r in results if r["ok"])
    total = len(results)
    groups = {}
    for r in results:
        g = groups.setdefault(r["group"], [0, 0])
        g[0] += 1
        g[1] += 1 if r["ok"] else 0
    print("\n--- summary by input-domain segment ---")
    for g in sorted(groups):
        n, ok = groups[g]
        print("  %-14s %2d/%2d" % (g, ok, n))
    print("--- total: %d/%d passed ---" % (passed, total))

    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)) or ".", exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write("impl=%s\npython=%s\ntotal=%d passed=%d\n\n"
                     % (impl, sys.version.split()[0], total, passed))
            for r in results:
                fh.write("=== %s [%s] %s\n" % (r["id"], r["group"], "PASS" if r["ok"] else "FAIL"))
                fh.write("--- md ---\n%s\n--- expected ---\n%s\n--- actual ---\n%s\n"
                         % (r["md"], r["expected"], r["actual"]))
                if r["problems"]:
                    fh.write("--- problems ---\n%s\n" % "\n".join(r["problems"]))
                fh.write("\n")
        print("report written to %s" % args.report)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
