# -*- coding: utf-8 -*-
"""极简 LRU 缓存。"""


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = {}
        self.order = []          # 早 -> 晚，order[0] 即最近最少使用

    def get(self, key):
        if key not in self.data:
            return None
        self.order.remove(key)   # 命中即刷新使用顺序
        self.order.append(key)
        return self.data[key]

    def put(self, key, value):
        if key in self.data:
            self.data[key] = value
            self.order.remove(key)   # 覆盖写也算一次使用
            self.order.append(key)
            return
        if len(self.data) >= self.capacity:
            victim = self.order[0]   # 淘汰最早的，即最近最少使用
            del self.data[victim]
            self.order.pop(0)
        self.data[key] = value
        self.order.append(key)
