import sys
sys.path.insert(0, r"<实验根目录>/ab-cycle2/_judge/_probe")
from orig_lru import LRUCache

def seq(mod_label):
    c = LRUCache(2)
    c.put(1, "a"); c.put(2, "b"); c.get(1); c.put(3, "c")
    got = c.get(2)
    passed = (got is None)
    print(f"{mod_label}: get(2) = {got!r}  -> 期望 None，{'通过' if passed else '未捕获缺陷'}")
    return passed

print("== 用 task.md 给的复现序列测【原版未修复】==")
seq("原版")
