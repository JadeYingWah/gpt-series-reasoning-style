"""Adventure verification - Decoupled"""
import json
from collections import deque

STORY = r"<实验根目录>\ab-decoupled-adventure\Decoupled\story.json"

with open(STORY, encoding="utf-8") as f:
    s = json.load(f)

nodes = s["nodes"]
print("=== Adventure Verification ===")

# 1. Node count
c1 = len(nodes) >= 5
print(f"  {'PASS' if c1 else 'FAIL'} - Nodes: {len(nodes)} (>=5)")

# 2. Ending count
endings = [n for n in nodes.values() if n.get("ending")]
c2 = len(endings) >= 2
print(f"  {'PASS' if c2 else 'FAIL'} - Endings: {len(endings)} (>=2)")

# 3. Valid references
bad_ref = [(n, c["next"]) for n, node in nodes.items() for c in node.get("choices", []) if c["next"] not in nodes]
c3 = len(bad_ref) == 0
print(f"  {'PASS' if c3 else 'FAIL'} - Valid refs: {len(bad_ref)} bad")

# 4. Choice count (non-ending >= 2)
bad_choice = [(n, len(node.get("choices", []))) for n, node in nodes.items() if not node.get("ending") and len(node.get("choices", [])) < 2]
c4 = len(bad_choice) == 0
print(f"  {'PASS' if c4 else 'FAIL'} - Choice count: {len(bad_choice)} nodes <2")

# 5. No dead ends
dead = [n for n, node in nodes.items() if not node.get("ending") and len(node.get("choices", [])) == 0]
c5 = len(dead) == 0
print(f"  {'PASS' if c5 else 'FAIL'} - Dead ends: {len(dead)}")

# 6. Reachability
visited, q = set(), deque([s["start"]])
while q:
    cur = q.popleft()
    if cur in visited: continue
    visited.add(cur)
    for c in nodes[cur].get("choices", []):
        if c["next"] not in visited: q.append(c["next"])
unreach = {n for n, node in nodes.items() if node.get("ending")} - visited
c6 = len(unreach) == 0
print(f"  {'PASS' if c6 else 'FAIL'} - Endings reachable: {len(endings)-len(unreach)}/{len(endings)}")

allok = all([c1, c2, c3, c4, c5, c6])
print(f"\nOverall: {'ALL PASS' if allok else 'ISSUES'}")
