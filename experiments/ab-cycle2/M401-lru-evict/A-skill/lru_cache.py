# -*- coding: utf-8 -*-
"""极简 LRU 缓存（已修复淘汰语义）。"""


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = {}
        self.order = []          # 早 -> 晚（末尾 = 最近使用）

    def get(self, key):
        if key not in self.data:
            return None
        # 命中即刷新使用顺序：把 key 移到末尾（最近使用）
        self.order.remove(key)
        self.order.append(key)
        return self.data[key]

    def put(self, key, value):
        if self.capacity <= 0:
            # 无容量：不缓存任何键，避免 order[0] 越界
            return
        if key in self.data:
            self.data[key] = value
            # 命中已有 key 也刷新使用顺序
            self.order.remove(key)
            self.order.append(key)
            return
        if len(self.data) >= self.capacity:
            # LRU 淘汰：order 头部是最久未使用者
            victim = self.order[0]
            del self.data[victim]
            self.order.pop(0)
        self.data[key] = value
        self.order.append(key)
