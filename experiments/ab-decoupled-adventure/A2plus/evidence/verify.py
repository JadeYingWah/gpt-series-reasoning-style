"""冒险类验证脚本 - A2+配置"""
import json
from collections import deque

STORY = r"<实验根目录>\ab-decoupled-adventure\A2plus\story.json"

def load_story():
    with open(STORY, encoding="utf-8") as f:
        return json.load(f)

def check_json_syntax():
    try:
        load_story()
        return True, "JSON语法正确"
    except json.JSONDecodeError as e:
        return False, f"JSON语法错误: {e}"

def check_node_count(story):
    count = len(story["nodes"])
    return count >= 5, f"{count}个节点（要求≥5）"

def check_ending_count(story):
    endings = [n for n in story["nodes"].values() if n.get("ending")]
    return len(endings) >= 2, f"{len(endings)}个结局（要求≥2）"

def check_valid_references(story):
    """检查所有选项引用的节点是否存在"""
    nodes = story["nodes"]
    bad = []
    for name, node in nodes.items():
        for choice in node.get("choices", []):
            if choice["next"] not in nodes:
                bad.append((name, choice["next"]))
    return len(bad) == 0, f"{len(bad)}个无效引用"

def check_choice_count(story):
    """非结局节点至少2个选项"""
    bad = []
    for name, node in story["nodes"].items():
        if not node.get("ending") and len(node.get("choices", [])) < 2:
            bad.append((name, len(node.get("choices", []))))
    return len(bad) == 0, f"{len(bad)}个节点选项不足2个"

def check_no_dead_ends(story):
    """非结局节点不能没有出口"""
    bad = []
    for name, node in story["nodes"].items():
        if not node.get("ending") and len(node.get("choices", [])) == 0:
            bad.append(name)
    return len(bad) == 0, f"{len(bad)}个死路"

def check_ending_reachability(story):
    """从起点BFS，检查所有结局是否可达"""
    nodes = story["nodes"]
    start = story["start"]
    visited = set()
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        for choice in nodes[current].get("choices", []):
            if choice["next"] not in visited:
                queue.append(choice["next"])
    endings = {name for name, node in nodes.items() if node.get("ending")}
    unreachable = endings - visited
    return len(unreachable) == 0, f"可达{len(endings - unreachable)}/{len(endings)}个结局，不可达: {unreachable}"

def check_start_exists(story):
    return story["start"] in story["nodes"], f"起点'{story['start']}'存在"

if __name__ == "__main__":
    print("=== 冒险类验证 ===")
    try:
        story = load_story()
        checks = [
            ("JSON语法", (True, "JSON语法正确")),
            ("起点存在", check_start_exists(story)),
            ("节点数量", check_node_count(story)),
            ("结局数量", check_ending_count(story)),
            ("引用有效", check_valid_references(story)),
            ("选项数量", check_choice_count(story)),
            ("无死路", check_no_dead_ends(story)),
            ("结局可达", check_ending_reachability(story)),
        ]
    except Exception as e:
        checks = [("JSON语法", (False, str(e)))]

    allok = True
    for name, (ok, msg) in checks:
        allok = allok and ok
        print(f"  {'PASS' if ok else 'FAIL'} - {name}: {msg}")
    print(f"\n总体: {'全部通过' if allok else '存在问题'}")
