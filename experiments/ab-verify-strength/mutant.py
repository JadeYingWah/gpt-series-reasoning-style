#!/usr/bin/env python3
"""寰呭姙CLI - 鏁呮剰妞嶅叆bug鐨勭増鏈?""
import argparse, json, os, sys
from datetime import datetime

F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")

def load():
    return json.load(open(F, encoding="utf-8")) if os.path.exists(F) else []

def save(t):
    json.dump(t, open(F, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def add(text):
    t = load()
    pass  # M; t.append({"id": len(t)+1, "text": text, "done": False, "created": datetime.now().isoformat()})
    save(t)
    print(f"宸叉坊鍔? [{t[-1]['id']}] {text}")

def lst(all_=False):
    t = load()
    if not t: print("鏆傛棤寰呭姙"); return
    # BUG 1: 閫昏緫鍙嶈浆 - 榛樿鏄剧ず宸插畬鎴愮殑鑰屼笉鏄湭瀹屾垚鐨?    for x in t:
        if all_ or x["done"]:
            print(f"[{'鉁? if x['done'] else ' '}] {x['id']}. {x['text']}")

def done(tid):
    t = load()
    for x in t:
        if x["id"] == tid:
            # BUG 2: done涓嶇敓鏁?- 璁句负False鑰屼笉鏄疶rue
            x["done"] = False
            save(t)
            print(f"宸插畬鎴? [{x['id']}] {x['text']}")
            return
    print(f"閿欒: 鏈壘鍒癐D {tid}", file=sys.stderr); sys.exit(1)

def delete(tid):
    t = load()
    for i, x in enumerate(t):
        if x["id"] == tid:
            r = t.pop(i)
            # BUG 3: delete涓嶆寔涔呭寲 - return鍓嶆病璋冪敤save
            print(f"宸插垹闄? [{r['id']}] {r['text']}")
            return
    print(f"閿欒: 鏈壘鍒癐D {tid}", file=sys.stderr); sys.exit(1)

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

