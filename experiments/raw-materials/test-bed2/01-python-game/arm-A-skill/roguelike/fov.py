# -*- coding: utf-8 -*-
"""视野（FOV）与探索记忆。"""

from roguelike import config
from roguelike.ai import line_of_sight


class FOVMap:
    """explored[y][x]：是否曾见过；visible[y][x]：本回合是否可见。"""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.explored = [[False] * width for _ in range(height)]
        self.visible = [[False] * width for _ in range(height)]

    def compute(self, gmap, px, py):
        """以玩家为中心重算可见集合并叠加到探索记忆。"""
        for y in range(self.height):
            for x in range(self.width):
                self.visible[y][x] = False
        r = config.FOV_RADIUS
        for y in range(max(0, py - r), min(gmap.height, py + r + 1)):
            for x in range(max(0, px - r), min(gmap.width, px + r + 1)):
                if (x - px) ** 2 + (y - py) ** 2 > r * r:
                    continue
                if line_of_sight(gmap, px, py, x, y):
                    self.visible[y][x] = True
                    self.explored[y][x] = True

    # ---- 序列化 ----
    def to_dict(self):
        return {"explored": self.explored}

    @classmethod
    def from_dict(cls, d, width, height):
        f = cls(width, height)
        rows = d.get("explored")
        if rows and len(rows) == height and len(rows[0]) == width:
            f.explored = rows
        return f
