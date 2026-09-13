#!/usr/bin/env python3
"""文件备份工具 - 支持增量备份和恢复"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime

BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".backups")
MANIFEST = os.path.join(BACKUP_DIR, "manifest.json")

def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_manifest():
    if not os.path.exists(MANIFEST):
        return {"backups": []}
    with open(MANIFEST, "r", encoding="utf-8") as f:
        return json.load(f)

def save_manifest(m):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

def do_backup(source):
    if not os.path.exists(source):
        print(f"错误: 源路径不存在 {source}", file=sys.stderr)
        sys.exit(1)
    m = load_manifest()
    bid = datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = os.path.join(BACKUP_DIR, bid)
    os.makedirs(bdir, exist_ok=True)
    files = []
    if os.path.isfile(source):
        files = [source]
    else:
        for root, _, fnames in os.walk(source):
            for fn in fnames:
                files.append(os.path.join(root, fn))
    copied = 0
    skipped = 0
    last_hash = {}
    if m["backups"]:
        last = m["backups"][-1]
        last_hash = {f["path"]: f["hash"] for f in last["files"]}
    for fpath in files:
        rel = os.path.relpath(fpath, os.path.dirname(source) if os.path.isfile(source) else source)
        h = file_hash(fpath)
        if rel in last_hash and last_hash[rel] == h:
            skipped += 1
            continue
        dest = os.path.join(bdir, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(fpath, dest)
        copied += 1
    m["backups"].append({"id": bid, "source": source, "time": datetime.now().isoformat(),
                         "files": [{"path": os.path.relpath(f, os.path.dirname(source) if os.path.isfile(source) else source),
                                    "hash": file_hash(f)} for f in files],
                         "copied": copied, "skipped": skipped})
    save_manifest(m)
    print(f"备份完成: {bid} (复制{copied}个, 跳过{skipped}个)")

def do_list():
    m = load_manifest()
    if not m["backups"]:
        print("暂无备份")
        return
    for b in m["backups"]:
        print(f"{b['id']} | {b['source']} | {b['time']} | {len(b['files'])}文件 | 复制{b['copied']} 跳过{b['skipped']}")

def do_restore(bid, dest):
    m = load_manifest()
    b = next((x for x in m["backups"] if x["id"] == bid), None)
    if not b:
        print(f"错误: 未找到备份 {bid}", file=sys.stderr)
        sys.exit(1)
    bdir = os.path.join(BACKUP_DIR, bid)
    os.makedirs(dest, exist_ok=True)
    restored = 0
    for f in b["files"]:
        src = os.path.join(bdir, f["path"])
        if os.path.exists(src):
            dst = os.path.join(dest, f["path"])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            restored += 1
    print(f"恢复完成: {restored}个文件 -> {dest}")

def main():
    p = argparse.ArgumentParser(description="文件备份工具")
    s = p.add_subparsers(dest="cmd", required=True)
    b = s.add_parser("backup"); b.add_argument("source")
    s.add_parser("list")
    r = s.add_parser("restore"); r.add_argument("bid"); r.add_argument("dest")
    args = p.parse_args()
    if args.cmd == "backup": do_backup(args.source)
    elif args.cmd == "list": do_list()
    elif args.cmd == "restore": do_restore(args.bid, args.dest)

if __name__ == "__main__":
    main()
