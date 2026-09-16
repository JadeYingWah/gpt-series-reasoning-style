# -*- coding: utf-8 -*-
"""lru_cache.py 验证脚本（证据产物，留在交付目录）。

用途：
1) 对修复版 LRUCache 跑功能用例（任务给定场景 + 边界），要求全部通过；
2) 用**同一批断言**跑「原始缺陷版」，要求出现失败（RED）——证明本验证有鉴别力
   （拿得动「淘汰顺序反了」这个要防的错误）；
3) 用 OrderedDict 作参考模型（oracle）做固定种子的差分随机测试，比对返回值、
   键集合与使用顺序。

运行： python verify_lru.py   （在 A-skill 目录下）
退出码：0 = 修复版全过 且 缺陷版确实被判红；1 = 不满足。
"""

import collections
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lru_cache import LRUCache  # noqa: E402


class BuggyLRUCache:
    """原始缺陷版（逐字复刻自阶段 1 读到的 lru_cache.py），仅用于 RED 检验。"""

    def __init__(self, capacity):
        self.capacity = capacity
        self.data = {}
        self.order = []

    def get(self, key):
        if key not in self.data:
            return None
        return self.data[key]

    def put(self, key, value):
        if key in self.data:
            self.data[key] = value
            return
        if len(self.data) >= self.capacity:
            victim = self.order[-1]
            del self.data[victim]
            self.order.remove(victim)
        self.data[key] = value
        self.order.append(key)


# ---------------- 用例：每个函数接受一个缓存类，失败即抛 AssertionError ---------------- #

def case_task_scenario(C):
    """任务原文场景：cap=2, put(1);put(2);get(1);put(3) -> get(2) 应为 None，get(1)==1。"""
    c = C(2)
    c.put(1, "a")
    c.put(2, "b")
    assert c.get(1) == "a"
    c.put(3, "c")
    assert c.get(2) is None, "2 应被淘汰，实际=%r" % (c.get(2),)
    assert c.get(1) == "a", "刚访问过的 1 不应被淘汰"
    assert c.get(3) == "c"


def case_evict_pure(C):
    """纯写入淘汰：最久未用者先走。"""
    c = C(2)
    c.put(1, "a")
    c.put(2, "b")
    c.put(3, "c")
    assert c.get(1) is None
    assert c.get(2) == "b"
    assert c.get(3) == "c"


def case_get_refreshes(C):
    """get 命中刷新最近使用顺序。"""
    c = C(3)
    for k in (1, 2, 3):
        c.put(k, k)
    assert c.get(1) == 1          # 1 变为最近使用
    c.put(4, 4)                   # 应淘汰 2
    assert c.get(2) is None
    assert c.get(1) == 1 and c.get(3) == 3 and c.get(4) == 4


def case_put_existing_refreshes(C):
    """put 命中已有 key：更新值且刷新顺序。"""
    c = C(2)
    c.put(1, "a")
    c.put(2, "b")
    c.put(1, "a2")                # 1 变为最近使用
    c.put(3, "c")                 # 应淘汰 2
    assert c.get(2) is None
    assert c.get(1) == "a2"


def case_capacity_one(C):
    c = C(1)
    c.put(1, "a")
    assert c.get(1) == "a"
    c.put(2, "b")
    assert c.get(1) is None
    assert c.get(2) == "b"


def case_capacity_zero_no_crash(C):
    """cap<=0 时不应崩溃，且不缓存任何键。"""
    c = C(0)
    c.put(1, "a")
    assert c.get(1) is None
    assert c.data == {}


def case_miss_returns_none(C):
    c = C(2)
    assert c.get(42) is None


CASES = [
    case_task_scenario,
    case_evict_pure,
    case_get_refreshes,
    case_put_existing_refreshes,
    case_capacity_one,
    case_capacity_zero_no_crash,
    case_miss_returns_none,
]


def run_cases(C, label):
    print("== %s ==" % label)
    passed = 0
    for fn in CASES:
        try:
            fn(C)
            print("  PASS  %s" % fn.__name__)
            passed += 1
        except Exception as e:
            print("  FAIL  %s -> %s: %s" % (fn.__name__, type(e).__name__, e))
    print("  小计: %d/%d 通过" % (passed, len(CASES)))
    return passed


def run_differential(C, label, seed=12345, steps=3000, cap=3, keymax=6):
    """差分测试：与 OrderedDict 参考模型逐步比对（含返回值和内部顺序）。"""
    print("== %s 差分测试 (seed=%d, steps=%d, cap=%d, keymax=%d) ==" % (label, seed, steps, cap, keymax))
    rnd = random.Random(seed)
    c = C(cap)
    ref = collections.OrderedDict()
    for i in range(steps):
        k = rnd.randint(1, keymax)
        if rnd.random() < 0.5:
            v = rnd.randint(100, 999)
            c.put(k, v)
            if cap > 0:
                if k in ref:
                    ref.move_to_end(k)
                    ref[k] = v
                else:
                    if len(ref) >= cap:
                        ref.popitem(last=False)
                    ref[k] = v
        else:
            got = c.get(k)
            if cap > 0 and k in ref:
                exp = ref[k]
                ref.move_to_end(k)
            else:
                exp = None
            assert got == exp, "step=%d get(%d): got=%r exp=%r" % (i, k, got, exp)
    assert set(c.data.keys()) == set(ref.keys()), "键集合不一致"
    assert c.order == list(ref.keys()), "使用顺序不一致: %r vs %r" % (c.order, list(ref.keys()))
    print("  差分一致（返回值 / 键集合 / 使用顺序 全部与 oracle 相同）")


def main():
    ok = True

    fixed_passed = run_cases(LRUCache, "修复版 LRUCache · 功能用例")
    try:
        run_differential(LRUCache, "修复版 LRUCache")
    except AssertionError as e:
        print("  DIFF-FAIL: %s" % e)
        ok = False
    if fixed_passed != len(CASES):
        ok = False

    print()
    buggy_passed = run_cases(BuggyLRUCache, "原始缺陷版 BuggyLRUCache · 同一批断言（应判红）")
    try:
        run_differential(BuggyLRUCache, "原始缺陷版 BuggyLRUCache")
        print("  DIFF-PASS（缺陷版竟通过差分——说明验证不足，需加严）")
        diff_killed = False
    except AssertionError as e:
        print("  DIFF-FAIL（如期判红）: %s" % e)
        diff_killed = True

    killed = (len(CASES) - buggy_passed) + (1 if diff_killed else 0)
    total = len(CASES) + 1
    print()
    print("注：case_task_scenario（task.md 原文场景）在**缺陷版上也是 PASS** ——")
    print("    即 task.md 自述的复现序列 put(1);put(2);get(1);put(3) 并不能区分修复版与缺陷版；")
    print("    真正能判红缺陷版的是 case_evict_pure / case_get_refreshes / case_capacity_zero 与差分测试。")
    print("杀伤率（缺陷版被判红的检查数 / 总检查数）: %d/%d" % (killed, total))
    print("修复版全过: %s" % (fixed_passed == len(CASES)))

    if not (ok and fixed_passed == len(CASES) and killed > 0):
        print("结论: 未通过")
        return 1
    print("结论: 通过（修复版 7/7 + 差分一致；缺陷版被判红 %d/%d，验证有鉴别力）" % (killed, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
