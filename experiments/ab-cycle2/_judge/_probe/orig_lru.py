# -*- coding: utf-8 -*-
"""极简 LRU 缓存（存在缺陷）。"""


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = {}
        self.order = []          # 早 -> 晚

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
