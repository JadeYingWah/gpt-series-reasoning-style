# -*- coding: utf-8 -*-
"""实体系统：玩家、怪物、战斗数值块、背包与装备。"""

from roguelike import config
from roguelike.items import Item


class Fighter:
    """战斗数值块，玩家与怪物共用。"""

    def __init__(self, hp, atk, defense, level=1, exp=0, owner_name=""):
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.defense = defense
        self.level = level
        self.exp = exp
        self.owner_name = owner_name

    # ---- 序列化 ----
    def to_dict(self):
        return {"max_hp": self.max_hp, "hp": self.hp, "atk": self.atk,
                "defense": self.defense, "level": self.level,
                "exp": self.exp, "owner_name": self.owner_name}

    @classmethod
    def from_dict(cls, d):
        f = cls(d["max_hp"], d["atk"], d["defense"], d["level"],
                d["exp"], d["owner_name"])
        f.hp = d["hp"]
        return f

    @property
    def exp_to_next(self):
        return config.EXP_BASE + (self.level - 1) * config.EXP_GROWTH

    def is_dead(self):
        return self.hp <= 0


class Inventory:
    """背包：固定容量。"""

    def __init__(self, capacity=config.INVENTORY_CAPACITY):
        self.capacity = capacity
        self.items = []

    def is_full(self):
        return len(self.items) >= self.capacity

    def add(self, item):
        if self.is_full():
            return False
        self.items.append(item)
        return True

    def remove(self, item):
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    # ---- 序列化 ----
    def to_dict(self):
        return {"capacity": self.capacity,
                "items": [i.to_dict() for i in self.items]}

    @classmethod
    def from_dict(cls, d):
        inv = cls(d["capacity"])
        inv.items = [Item.from_dict(i) for i in d["items"]]
        return inv


class Entity:
    """地图上的实体基类。"""

    def __init__(self, x, y, char, color, name, blocks=True, fighter=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.fighter = fighter          # Fighter 或 None
        self.ai = None                  # MonsterAI 或 None
        self.inventory = None           # Inventory 或 None（玩家）

    def to_dict(self):
        return {"x": self.x, "y": self.y, "char": self.char,
                "color": self.color, "name": self.name,
                "blocks": self.blocks,
                "fighter": self.fighter.to_dict() if self.fighter else None,
                "ai": self.ai.to_dict() if self.ai else None,
                "inventory": self.inventory.to_dict() if self.inventory else None,
                "cls": type(self).__name__}


def make_player(x, y):
    """构造玩家实体。"""
    p = Entity(x, y, "@", "white", "冒险者", blocks=True)
    p.fighter = Fighter(config.PLAYER_BASE["hp"], config.PLAYER_BASE["atk"],
                        config.PLAYER_BASE["defense"], owner_name="冒险者")
    p.inventory = Inventory()
    p.equipment = {"weapon": None, "armor": None}
    p.stairs_seen = False
    return p


def player_attack_power(player):
    """玩家实际攻击力 = 基础 + 武器。"""
    w = player.equipment["weapon"]
    return player.fighter.atk + (w.power if w else 0)


def player_defense(player):
    """玩家实际防御 = 基础 + 护甲。"""
    a = player.equipment["armor"]
    return player.fighter.defense + (a.power if a else 0)
