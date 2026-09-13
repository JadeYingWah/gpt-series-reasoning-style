#!/usr/bin/env python3
"""批量重命名工具 - 解耦版（验证层独立，无流程层）"""
import argparse, os, re, sys
from pathlib import Path

def get_files(d, recursive=False, ext=None):
    if recursive:
        return [str(p) for p in Path(d).rglob("*") if p.is_file() and (not ext or p.suffix == ext)]
    return [str(p) for p in Path(d).iterdir() if p.is_file() and (not ext or p.suffix == ext)]

def new_name(f, prefix=None, pat=None, repl="", num=None, width=3):
    d, base = os.path.split(f)
    name, ext = os.path.splitext(base)
    if pat:
        name = re.sub(pat, repl, name)
    if num is not None:
        name = f"{name}_{str(num).zfill(width)}"
    if prefix:
        name = f"{prefix}{name}"
    return os.path.join(d, name + ext)

def run(files, prefix=None, pat=None, repl="", numbered=False, start=1, width=3, dry=False):
    ops, errs = [], []
    idx = start if numbered else None
    for f in sorted(files):
        try:
            nf = new_name(f, prefix, pat, repl, idx, width)
            if nf == f:
                ops.append((f, nf, "skip")); continue
            if os.path.exists(nf):
                errs.append((f, nf, "exists")); continue
            if not dry:
                os.rename(f, nf)
            ops.append((f, nf, "dry" if dry else "ok"))
        except Exception as e:
            errs.append((f, None, str(e)))
        if numbered:
            idx += 1
    return ops, errs

def main():
    p = argparse.ArgumentParser(description="批量重命名")
    p.add_argument("dir")
    p.add_argument("--prefix")
    p.add_argument("--regex")
    p.add_argument("--replacement", default="")
    p.add_argument("--numbered", action="store_true")
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--width", type=int, default=3)
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--ext")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    if not os.path.isdir(a.dir):
        print(f"错误：目录不存在 {a.dir}", file=sys.stderr); sys.exit(1)
    if not (a.prefix or a.regex or a.numbered):
        print("错误：至少指定 --prefix/--regex/--numbered", file=sys.stderr); sys.exit(1)
    files = get_files(a.dir, a.recursive, a.ext)
    if not files:
        print("未找到匹配文件"); return
    ops, errs = run(files, a.prefix, a.regex, a.replacement, a.numbered, a.start, a.width, a.dry_run)
    for old, new, st in ops:
        print(f"{st:5} {os.path.basename(old):30} -> {os.path.basename(new)}")
    if errs:
        print(f"\n错误 {len(errs)}:")
        for old, new, e in errs:
            print(f"  {os.path.basename(old)}: {e}")
    print(f"\n总计: {len(ops)} 操作, {len(errs)} 错误" + (" (dry-run)" if a.dry_run else ""))

if __name__ == "__main__":
    main()
