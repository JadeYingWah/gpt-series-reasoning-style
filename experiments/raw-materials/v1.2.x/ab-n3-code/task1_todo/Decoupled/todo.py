#!/usr/bin/env python3
"""Todo CLI"""
import argparse, json, os, sys
from datetime import datetime

F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")

def load():
    return json.load(open(F, encoding="utf-8")) if os.path.exists(F) else []

def save(t):
    json.dump(t, open(F, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def add(text):
    t = load()
    t.append({"id": len(t)+1, "text": text, "done": False, "created": datetime.now().isoformat()})
    save(t)
    print(f"Added: [{t[-1]['id']}] {text}")

def lst(all_=False):
    t = load()
    if not t: print("Empty"); return
    for x in t:
        if all_ or not x["done"]:
            print(f"[{'x' if x['done'] else ' '}] {x['id']}. {x['text']}")

def done(tid):
    t = load()
    for x in t:
        if x["id"] == tid:
            x["done"] = True
            save(t)
            print(f"Done: [{x['id']}] {x['text']}")
            return
    print(f"Error: id {tid} not found", file=sys.stderr); sys.exit(1)

def delete(tid):
    t = load()
    for i, x in enumerate(t):
        if x["id"] == tid:
            r = t.pop(i)
            save(t)
            print(f"Deleted: [{r['id']}] {r['text']}")
            return
    print(f"Error: id {tid} not found", file=sys.stderr); sys.exit(1)

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="cmd", required=True)
    a = s.add_parser("add"); a.add_argument("text")
    l = s.add_parser("list"); l.add_argument("-a", "--all", action="store_true")
    d = s.add_parser("done"); d.add_argument("id", type=int)
    dl = s.add_parser("delete"); dl.add_argument("id", type=int)
    args = p.parse_args()
    {"add": lambda: add(args.text), "list": lambda: lst(args.all),
     "done": lambda: done(args.id), "delete": lambda: delete(args.id)}[args.cmd]()

if __name__ == "__main__":
    main()
