"""玩家与敌人实体：属性、经验成长、敌人生成模板。"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import config
from .items import Item


@dataclass
class Player:
    x: int
    y: int
    hp: int
    max_hp: int
    base_atk: int
    base_def: int
    level: int = 1
    xp: int = 0
    xp_next: int = config.XP_BASE
    gold: int = 0
    inventory: list[Item] = field(default_factory=list)
    weapon: Item | None = None
    armor: Item | None = None

    @property
    def atk(self) -> int:
        return self.base_atk + (self.weapon.atk if self.weapon else 0)

    @property
    def dfn(self) -> int:
        return self.base_def + (self.armor.dfn if self.armor else 0)

    def add_xp(self, amount: int) -> list[str]:
        """增加经验并处理升级，返回升级消息列表。"""
        msgs: list[str] = []
        self.xp += amount
        while self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self.level += 1
            self.xp_next = config.XP_BASE + config.XP_GROWTH * (self.level - 1)
            gain_hp = 12
            self.max_hp += gain_hp
            self.base_atk += 2
            self.base_def += 1
            self.hp = min(self.max_hp, self.hp + gain_hp)
            msgs.append(
                f"升级了！现在是 {self.level} 级（生命+12 攻击+2 防御+1）"
            )
        return msgs


@dataclass
class Enemy:
    key: str
    name: str
    glyph: str
    x: int
    y: int
    hp: int
    max_hp: int
    atk: int
    dfn: int
    xp_reward: int
    detect: int
    tier: int
    state: str = "sleep"      # sleep / wander / chase
    boss: bool = False
    attack_count: int = 0


ENEMY_TEMPLATES: dict[str, dict] = {
    # detect: 发现玩家的视野距离；init_state: 初始状态
    "slime":     dict(name="史莱姆",   glyph="s", hp=14, atk=4,  dfn=0, xp_reward=8,   detect=4,  tier=1, init_state="sleep"),
    "bat":       dict(name="洞穴蝙蝠", glyph="b", hp=10, atk=5,  dfn=0, xp_reward=10,  detect=7,  tier=1, init_state="wander"),
    "goblin":    dict(name="哥布林",   glyph="g", hp=22, atk=7,  dfn=1, xp_reward=16,  detect=6,  tier=2, init_state="sleep"),
    "skeleton":  dict(name="骷髅兵",   glyph="k", hp=28, atk=8,  dfn=3, xp_reward=20,  detect=5,  tier=2, init_state="sleep"),
    "orc":       dict(name="兽人战士", glyph="o", hp=40, atk=11, dfn=3, xp_reward=30,  detect=6,  tier=3, init_state="wander"),
    "hellhound": dict(name="地狱犬",   glyph="h", hp=34, atk=13, dfn=2, xp_reward=32,  detect=8,  tier=3, init_state="sleep"),
    "boss":      dict(name="暗影魔王", glyph="B", hp=90, atk=15, dfn=5, xp_reward=100, detect=12, tier=3, init_state="sleep"),
}


def spawn_enemy(key: str, x: int, y: int) -> Enemy:
    t = ENEMY_TEMPLATES[key]
    return Enemy(
        key=key, name=t["name"], glyph=t["glyph"],
        x=x, y=y, hp=t["hp"], max_hp=t["hp"],
        atk=t["atk"], dfn=t["dfn"],
        xp_reward=t["xp_reward"], detect=t["detect"], tier=t["tier"],
        state=t.get("init_state", "sleep"),
        boss=(key == "boss"),
    )
