# -*- coding: utf-8 -*-
"""道具与装备系统。Item 为纯数据类，效果由 apply/equip 逻辑统一处理。"""

from roguelike import config


class Item:
    """道具。kind 决定行为：potion/scroll/weapon/armor/amulet。"""

    def __init__(self, name, kind, char="!", color="white", power=0,
                 description="", value=0):
        self.name = name
        self.kind = kind            # potion | scroll | weapon | armor
        self.char = char
        self.color = color
        self.power = power          # 治疗量/伤害量/攻防加成
        self.description = description
        self.value = value          # 分数用价值

    # ---- 序列化 ----
    def to_dict(self):
        return {"name": self.name, "kind": self.kind, "char": self.char,
                "color": self.color, "power": self.power,
                "description": self.description, "value": self.value}

    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d["kind"], d["char"], d["color"],
                   d["power"], d["description"], d["value"])


# ---------- 道具工厂表 ----------
_ITEM_FACTORIES = [
    lambda: Item("治疗药水", "potion", "!", "red", power=12,
                 description="恢复 12 点生命", value=15),
    lambda: Item("大力药水", "potion", "!", "magenta", power=1,
                 description="永久提升 1 点攻击力", value=25),
    lambda: Item("铁皮药水", "potion", "!", "blue", power=1,
                 description="永久提升 1 点防御力", value=25),
    lambda: Item("火焰卷轴", "scroll", "?", "orange", power=10,
                 description="对视野内所有敌人造成 10 点伤害", value=30),
    lambda: Item("治疗卷轴", "scroll", "?", "pink", power=25,
                 description="恢复 25 点生命", value=35),
    lambda: Item("匕首", "weapon", "/", "gray", power=1,
                 description="武器 攻击+1", value=10),
    lambda: Item("长剑", "weapon", "/", "white", power=3,
                 description="武器 攻击+3", value=25),
    lambda: Item("战斧", "weapon", "/", "yellow", power=5,
                 description="武器 攻击+5", value=40),
    lambda: Item("皮甲", "armor", "[", "gray", power=1,
                 description="护甲 防御+1", value=10),
    lambda: Item("锁子甲", "armor", "[", "white", power=2,
                 description="护甲 防御+2", value=25),
    lambda: Item("板金甲", "armor", "[", "yellow", power=3,
                 description="护甲 防御+3", value=40),
]

# 按楼层加权：越深的楼层越容易出高级货
_WEIGHTS_BY_FLOOR = {
    1: [22, 4, 3, 8, 5, 12, 5, 1, 12, 5, 1],
    2: [20, 5, 4, 8, 6, 10, 8, 2, 10, 8, 2],
    3: [18, 6, 5, 8, 7, 7, 10, 4, 7, 10, 4],
    4: [16, 7, 6, 8, 8, 5, 10, 6, 5, 10, 6],
    5: [14, 8, 7, 8, 9, 3, 10, 8, 3, 10, 8],
}


def random_item(rng, floor):
    """按楼层权重随机产出一个道具。"""
    weights = _WEIGHTS_BY_FLOOR.get(floor, _WEIGHTS_BY_FLOOR[5])
    idx = rng.choices(range(len(_ITEM_FACTORIES)), weights=weights, k=1)[0]
    return _ITEM_FACTORIES[idx]()
