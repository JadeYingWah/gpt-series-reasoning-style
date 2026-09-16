"""道具与装备定义：药水 / 武器 / 护甲 / 金币 / 药剂，以及按层掉落表。"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace


@dataclass
class Item:
    kind: str      # potion / weapon / armor / gold / elixir
    name: str
    glyph: str
    heal: int = 0
    atk: int = 0
    dfn: int = 0
    value: int = 0  # 金币面额
    desc: str = ""


def _i(kind: str, name: str, glyph: str, **kw) -> Item:
    return Item(kind=kind, name=name, glyph=glyph, **kw)


ITEMS: dict[str, Item] = {
    "potion_s": _i("potion", "小治疗药水", "!", heal=20, desc="恢复 20 点生命"),
    "potion_l": _i("potion", "大治疗药水", "!", heal=50, desc="恢复 50 点生命"),
    "elixir":   _i("elixir", "力量药剂", "!", atk=1, desc="永久提升 1 点攻击"),
    "w0": _i("weapon", "木剑", "/", atk=2, desc="攻击 +2"),
    "w1": _i("weapon", "铁剑", "/", atk=4, desc="攻击 +4"),
    "w2": _i("weapon", "精钢剑", "/", atk=6, desc="攻击 +6"),
    "w3": _i("weapon", "骑士剑", "/", atk=9, desc="攻击 +9"),
    "w4": _i("weapon", "影魔之刃", "/", atk=13, desc="攻击 +13，魔王佩剑"),
    "a0": _i("armor", "布甲", "]", dfn=1, desc="防御 +1"),
    "a1": _i("armor", "皮甲", "]", dfn=3, desc="防御 +3"),
    "a2": _i("armor", "锁子甲", "]", dfn=5, desc="防御 +5"),
    "a3": _i("armor", "骑士板甲", "]", dfn=8, desc="防御 +8"),
    "a4": _i("armor", "龙鳞铠", "]", dfn=11, desc="防御 +11"),
}

# 魔王固定掉落
BOSS_DROPS: list[Item] = [replace(ITEMS["w4"]), replace(ITEMS["potion_l"])]

# 各层掉落权重表（tier 从 1 开始）
_LOOT_TABLES: dict[int, list[tuple[str, int]]] = {
    1: [("potion_s", 30), ("w0", 10), ("w1", 8), ("a0", 10), ("a1", 6),
        ("elixir", 3), ("gold_s", 33)],
    2: [("potion_s", 22), ("potion_l", 10), ("w1", 12), ("w2", 8), ("a1", 10),
        ("a2", 7), ("elixir", 5), ("gold_m", 26)],
    3: [("potion_l", 22), ("w2", 12), ("w3", 8), ("a2", 10), ("a3", 7),
        ("elixir", 8), ("gold_l", 33)],
}

_GOLD_RANGE = {"gold_s": (5, 15), "gold_m": (10, 30), "gold_l": (20, 50)}


def roll_loot(rng: random.Random, tier: int) -> Item | None:
    """按层权重随机掉落一件道具（返回副本）。"""
    table = _LOOT_TABLES.get(tier, _LOOT_TABLES[1])
    total = sum(w for _, w in table)
    r = rng.uniform(0, total)
    acc = 0.0
    for key, w in table:
        acc += w
        if r <= acc:
            if key in _GOLD_RANGE:
                lo, hi = _GOLD_RANGE[key]
                return Item(kind="gold", name="金币", glyph="$",
                            value=rng.randint(lo, hi), desc="闪亮的金币")
            return replace(ITEMS[key])
    return None
