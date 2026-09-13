#!/usr/bin/env python3
"""File backup tool with incremental support"""
import argparse, hashlib, json, os, shutil, sys
from datetime import datetime

BD = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".backups")
MF = os.path.join(BD, "manifest.json")

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(8192), b""): h.update(c)
    return h.hexdigest()

def load():
    return json.load(open(MF, encoding="utf-8")) if os.path.exists(MF) else {"backups": []}

def save(m):
    os.makedirs(BD, exist_ok=True)
    json.dump(m, open(MF, "w", encoding="utf-8"), indent=2)

def backup(src):
    if not os.path.exists(src):
        print(f"Error: {src} not found", file=sys.stderr); sys.exit(1)
    m = load()
    bid = datetime.now().strftime("%Y%m%d_%H%M%S")
    bd = os.path.join(BD, bid); os.makedirs(bd, exist_ok=True)
    files = [os.path.join(r, f) for r, _, fs in os.walk(src) for f in fs] if os.path.isdir(src) else [src]
    base = os.path.dirname(src) if os.path.isfile(src) else src
    last = {f["path"]: f["hash"] for f in m["backups"][-1]["files"]} if m["backups"] else {}
    copied = skipped = 0
    for fp in files:
        rel = os.path.relpath(fp, base); h = md5(fp)
        if rel in last and last[rel] == h:
            skipped += 1; continue
        dst = os.path.join(bd, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(fp, dst); copied += 1
    m["backups"].append({"id": bid, "source": src, "files": [{"path": os.path.relpath(f, base), "hash": md5(f)} for f in files], "copied": copied, "skipped": skipped})
    save(m)
    print(f"Backup {bid}: {copied} copied, {skipped} skipped")

def lst():
    m = load()
    if not m["backups"]: print("No backups"); return
    for b in m["backups"]:
        print(f"{b['id']} | {b['source']} | {len(b['files'])} files | c:{b['copied']} s:{b['skipped']}")

def restore(bid, dst):
    m = load()
    b = next((x for x in m["backups"] if x["id"] == bid), None)
    if not b: print(f"Error: backup {bid} not found", file=sys.stderr); sys.exit(1)
    bd = os.path.join(BD, bid); os.makedirs(dst, exist_ok=True)
    n = 0
    for f in b["files"]:
        s = os.path.join(bd, f["path"])
        if os.path.exists(s):
            d = os.path.join(dst, f["path"]); os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d); n += 1
    print(f"Restored {n} files -> {dst}")

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="cmd", required=True)
    b = s.add_parser("backup"); b.add_argument("src")
    s.add_parser("list")
    r = s.add_parser("restore"); r.add_argument("bid"); r.add_argument("dst")
    a = p.parse_args()
    {"backup": lambda: backup(a.src), "list": lst, "restore": lambda: restore(a.bid, a.dst)}[a.cmd]()

if __name__ == "__main__":
    main()
