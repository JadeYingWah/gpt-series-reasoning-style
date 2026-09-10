"""Patch SB6: clean escaped-fence detection (no regex; avoid multi-layer escaping)."""
import pathlib

p = pathlib.Path("scripts/selfcheck.py")
t = p.read_text(encoding="utf-8")

bad_re = '''    bad = []
    escaped = []
    ESCAPED_FENCE_RE = re.compile(r"^\\s*\\\\```")
    for p in sorted(REPO_ROOT.rglob("*.md")):
        if ".git" in p.parts:
            continue
        raw_lines = p.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(raw_lines, 1):
            if ESCAPED_FENCE_RE.match(line):
                escaped.append("{}:{}".format(p.relative_to(REPO_ROOT), idx))
        n = sum(1 for line in raw_lines if FENCE_RE.match(line))
        if n % 2 != 0:
            bad.append(str(p.relative_to(REPO_ROOT)) + " (" + str(n) + ")")
    if escaped:
        bad.append("escaped fences (invisible to parser): " + ", ".join(escaped[:4]))'''

good = '''    bad = []
    escaped = []
    backslash_fence = chr(92) + chr(96) * 3  # a fence written as \\`\\`\\` — invisible to the parser
    for p in sorted(REPO_ROOT.rglob("*.md")):
        if ".git" in p.parts:
            continue
        raw_lines = p.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(raw_lines, 1):
            if line.lstrip().startswith(backslash_fence):
                escaped.append("{}:{}".format(p.relative_to(REPO_ROOT), idx))
        n = sum(1 for line in raw_lines if FENCE_RE.match(line))
        if n % 2 != 0:
            bad.append(str(p.relative_to(REPO_ROOT)) + " (" + str(n) + ")")
    if escaped:
        bad.append("escaped fences (invisible to parser): " + ", ".join(escaped[:4]))'''

assert bad_re in t, "SB6 block not found"
t = t.replace(bad_re, good, 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("SB6 escaped-fence check rewritten cleanly")
