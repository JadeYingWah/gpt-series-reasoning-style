# -*- coding: utf-8 -*-
"""游戏引擎：状态机、回合驱动、层数推进、序列化。"""

import random

from roguelike import config
from roguelike.ai import MonsterAI
from roguelike.combat import attack, gain_exp
from roguelike.entities import (Entity, Fighter, make_player,
                                player_attack_power)
from roguelike.fov import FOVMap
from roguelike.items import Item, random_item
from roguelike.map_gen import (TILE_FLOOR, TILE_STAIRS, generate_map,
                               reachable_tiles)
from roguelike.save_load import rng_state_from_json, rng_state_to_json


class LevelState:
    """一层的完整状态：地图 + 探索记忆 + 怪物 + 地面物品。"""

    def __init__(self, gmap, fov, monsters, ground_items):
        self.gmap = gmap
        self.fov = fov
        self.monsters = monsters
        self.ground_items = ground_items

    def to_dict(self):
        return {
            "map": self.gmap.to_dict(),
            "fov": self.fov.to_dict(),
            "monsters": [m.to_dict() for m in self.monsters],
            "items": [{"x": g["x"], "y": g["y"],
                       "item": g["item"].to_dict()} for g in self.ground_items],
        }

    @classmethod
    def from_dict(cls, d):
        from roguelike.map_gen import GameMap
        gmap = GameMap.from_dict(d["map"])
        fov = FOVMap.from_dict(d["fov"], gmap.width, gmap.height)
        monsters = [entity_from_dict(m) for m in d["monsters"]]
        monsters = [m for m in monsters if m is not None]
        ground = [{"x": g["x"], "y": g["y"], "item": Item.from_dict(g["item"])}
                  for g in d["items"]]
        return cls(gmap, fov, monsters, ground)


def entity_from_dict(d):
    """从存档 dict 重建 Entity（含 fighter/ai/inventory）。"""
    e = Entity(d["x"], d["y"], d["char"], d["color"], d["name"],
               blocks=d["blocks"])
    if d.get("fighter"):
        e.fighter = Fighter.from_dict(d["fighter"])
    if d.get("ai"):
        e.ai = MonsterAI.from_dict(d["ai"])
    if d.get("inventory"):
        from roguelike.entities import Inventory
        e.inventory = Inventory.from_dict(d["inventory"])
    return e


def make_monster(floor, rng, template=None):
    """按楼层深度构造一只怪物。"""
    if template is None:
        pool = [t for t in config.MONSTER_TEMPLATES
                if t["min_floor"] <= floor] or config.MONSTER_TEMPLATES[:1]
        template = rng.choice(pool)
    scale = 1 + config.DEPTH_SCALE * (floor - 1)
    hp = max(3, int(template["hp"] * scale))
    atk = max(1, int(template["atk"] * scale))
    dfn = template["defense"]
    m = Entity(0, 0, template["char"], template["color"], template["name"])
    m.fighter = Fighter(hp, atk, dfn,
                        level=floor, exp=int(template["exp"] * scale),
                        owner_name=template["name"])
    m.ai = MonsterAI(fast=template.get("fast", False))
    return m


class Game:
    def __init__(self, seed=None, input_queue=None):
        self.rng = random.Random(seed)
        self.max_floors = config.MAX_FLOORS
        self.floor = 1
        self.levels = {}
        self.messages = []
        self.over = False
        self.result = None           # "dead" | "victory"
        self.turn_count = 0
        self.input_queue = input_queue if input_queue is not None else []
        self.pending_input = None    # 交互 UI 的复合指令（背包选择等）
        self._build_floor(1)

    # ---------- 消息 ----------
    def add_msg(self, text, color="white"):
        self.messages.append(colored_safe(text, color))

    # ---------- 层构建 ----------
    def _build_floor(self, floor, player=None):
        gmap = generate_map(floor, self.rng)
        fov = FOVMap(gmap.width, gmap.height)
        start = gmap.start_pos
        stairs = gmap.stairs_pos

        # 换层沿用既有玩家（保留成长与背包），但坐标必须重置到新层出生点；
        # 新开局才创建玩家
        if player is not None:
            player.x, player.y = start
            self.player = player
        else:
            self.player = make_player(*start)

        reach = reachable_tiles(gmap, start)

        def random_spot(min_dist_from_player, exclude=()):
            spots = [p for p in reach
                     if (p[0] - start[0]) ** 2 + (p[1] - start[1]) ** 2 >= min_dist_from_player ** 2
                     and p not in exclude and p != stairs]
            if not spots:
                spots = [p for p in reach if p != start and p not in exclude]
            return self.rng.choice(spots) if spots else start

        # 怪物
        monsters = []
        n_mon = config.MONSTERS_PER_FLOOR(floor)
        for _ in range(n_mon):
            x, y = random_spot(min_dist_from_player=8,
                               exclude={(m.x, m.y) for m in monsters})
            m = make_monster(floor, self.rng)
            m.x, m.y = x, y
            monsters.append(m)

        # Boss 层：最深处不放楼梯，放 Boss（距玩家最远的可达格）
        if floor >= self.max_floors:
            gmap.tiles[stairs[1]][stairs[0]] = TILE_FLOOR
            gmap.stairs_pos = None
            far = max(reach, key=lambda p: (p[0] - start[0]) ** 2 + (p[1] - start[1]) ** 2)
            boss = make_monster(floor, self.rng, template=config.BOSS_TEMPLATE)
            boss.x, boss.y = far
            boss.fighter.hp = boss.fighter.max_hp = config.BOSS_TEMPLATE["hp"]
            boss.fighter.atk = config.BOSS_TEMPLATE["atk"]
            boss.fighter.defense = config.BOSS_TEMPLATE["defense"]
            boss.fighter.exp = config.BOSS_TEMPLATE["exp"]
            monsters.append(boss)
        else:
            gmap.tiles[stairs[1]][stairs[0]] = TILE_STAIRS

        # 地面物品
        ground = []
        for _ in range(config.ITEMS_PER_FLOOR(floor)):
            x, y = random_spot(min_dist_from_player=3,
                               exclude={(g["x"], g["y"]) for g in ground})
            ground.append({"x": x, "y": y, "item": random_item(self.rng, floor)})

        self.levels[floor] = LevelState(gmap, fov, monsters, ground)
        self._bind_floor()

    def _bind_floor(self):
        """把当前层状态展开为快捷引用。"""
        lv = self.levels[self.floor]
        self.gmap = lv.gmap
        self.fov = lv.fov
        self.monsters = lv.monsters
        self.ground_items = lv.ground_items
        self.fov.compute(self.gmap, self.player.x, self.player.y)

    # ---------- 玩家行动 ----------
    def player_move_or_attack(self, dx, dy):
        if self.over:
            return
        nx, ny = self.player.x + dx, self.player.y + dy
        target = self.monster_at(nx, ny)
        if target:
            power = player_attack_power(self.player)
            dmg, crit, killed = attack(self.player, target, self.rng, power)
            prefix = "暴击！ " if crit else ""
            self.add_msg(f"{prefix}你攻击{target.name}，造成 {dmg} 点伤害", "yellow")
            if killed:
                self._on_monster_death(target)
        elif self.gmap.is_walkable(nx, ny):
            self.player.x, self.player.y = nx, ny
        else:
            self.add_msg("前方是墙壁", "gray")
            return  # 撞墙不消耗回合
        self.end_player_turn()

    def wait(self):
        if not self.over:
            self.add_msg("你原地等待", "gray")
            self.end_player_turn()

    def pickup(self):
        if self.over:
            return
        px, py = self.player.x, self.player.y
        here = [g for g in self.ground_items if g["x"] == px and g["y"] == py]
        if not here:
            self.add_msg("这里没有可拾取的物品", "gray")
            return
        item = here[0]["item"]
        if self.player.inventory.is_full():
            self.add_msg("背包已满，无法拾取", "red")
            return
        self.ground_items.remove(here[0])
        self.player.inventory.add(item)
        self.add_msg(f"拾取了 {item.name}", "cyan")
        self.end_player_turn()

    def use_item(self, idx):
        """使用/装备背包中第 idx 个物品（0 起）。"""
        if self.over:
            return
        inv = self.player.inventory
        if not (0 <= idx < len(inv.items)):
            self.add_msg("无效的物品编号", "red")
            return
        item = inv.items[idx]
        consumed = False

        if item.kind == "potion":
            f = self.player.fighter
            if item.name == "治疗药水":
                before = f.hp
                f.hp = min(f.max_hp, f.hp + item.power)
                self.add_msg(f"恢复了 {f.hp - before} 点生命", "green")
            elif item.name == "大力药水":
                f.atk += item.power
                self.add_msg(f"攻击力永久 +{item.power}！", "magenta")
            elif item.name == "铁皮药水":
                f.defense += item.power
                self.add_msg(f"防御力永久 +{item.power}！", "blue")
            consumed = True
        elif item.kind == "scroll":
            if item.name == "火焰卷轴":
                visible = [m for m in self.monsters
                           if not m.fighter.is_dead()
                           and self.fov.visible[m.y][m.x]]
                if not visible:
                    self.add_msg("视野内没有目标，卷轴没有生效", "gray")
                    return
                for m in visible:
                    m.fighter.hp -= item.power
                    if m.fighter.is_dead():
                        self._on_monster_death(m)
                self.add_msg(f"烈焰席卷四周！对 {len(visible)} 个敌人造成 {item.power} 点伤害", "orange")
            else:  # 治疗卷轴
                f = self.player.fighter
                before = f.hp
                f.hp = min(f.max_hp, f.hp + item.power)
                self.add_msg(f"治愈之光恢复了 {f.hp - before} 点生命", "green")
            consumed = True
        elif item.kind in ("weapon", "armor"):
            slot = "weapon" if item.kind == "weapon" else "armor"
            old = self.player.equipment[slot]
            self.player.equipment[slot] = item
            inv.remove(item)
            if old:
                inv.add(old)
            self.add_msg(f"装备了 {item.name}"
                         + (f"，换下了 {old.name}" if old else ""), "cyan")
            self.end_player_turn()
            return

        if consumed:
            inv.remove(item)
            self.end_player_turn()

    def drop_item(self, idx):
        if self.over:
            return
        inv = self.player.inventory
        if not (0 <= idx < len(inv.items)):
            return
        item = inv.items[idx]
        if inv.remove(item):
            self.ground_items.append({"x": self.player.x, "y": self.player.y,
                                      "item": item})
            self.add_msg(f"丢弃了 {item.name}", "gray")
            self.end_player_turn()

    def descend(self):
        if self.over:
            return False
        p = self.gmap.stairs_pos
        if not p or (self.player.x, self.player.y) != p:
            self.add_msg("这里没有向下的楼梯（需站在 > 上）", "gray")
            return False
        self.floor += 1
        if self.floor not in self.levels:
            self._build_floor(self.floor, player=self.player)
            self.add_msg(f"▼ 进入第 {self.floor} 层……", "cyan")
        else:
            self._bind_floor()
            self.add_msg(f"回到第 {self.floor} 层", "cyan")
        return True

    # ---------- 怪物 API（AI 调用） ----------
    def monster_at(self, x, y):
        for m in self.monsters:
            if (m.x, m.y) == (x, y) and not m.fighter.is_dead():
                return m
        return None

    def move_monster(self, monster, x, y):
        if not self.gmap.is_walkable(x, y):
            return False
        if (x, y) == (self.player.x, self.player.y):
            return False
        if any(m is not monster and (m.x, m.y) == (x, y) and not m.fighter.is_dead()
               for m in self.monsters):
            return False
        monster.x, monster.y = x, y
        return True

    def monster_attack(self, monster):
        dmg, crit, killed = attack(monster, self.player, self.rng)
        prefix = "暴击！ " if crit else ""
        self.add_msg(f"{prefix}{monster.name}攻击你，造成 {dmg} 点伤害", "red")
        if self.player.fighter.is_dead():
            self.over = True
            self.result = "dead"
            self.add_msg("你倒在了地下城中……（游戏结束）", "red")

    def _on_monster_death(self, monster):
        monster.blocks = False
        self.add_msg(f"{monster.name}被击杀！", "green")
        lv = gain_exp(self.player.fighter, monster.fighter.exp,
                      on_level_up=self._on_level_up)
        # 掉落
        if self.rng.random() < 0.4:
            self.ground_items.append({"x": monster.x, "y": monster.y,
                                      "item": Item("治疗药水", "potion", "!", "red",
                                                   power=12, description="恢复 12 点生命",
                                                   value=15)})
            self.add_msg(f"{monster.name}掉落了 治疗药水", "cyan")
        if monster.name == config.BOSS_TEMPLATE["name"]:
            self.over = True
            self.result = "victory"
            self.add_msg("★ 你击败了远古魔龙，地下城恢复了和平！胜利！", "yellow")

    def _on_level_up(self, fighter, new_level):
        self.add_msg(f"★ 升级！Lv.{new_level}  HP上限+{config.LEVEL_HP_GAIN} 攻+{config.LEVEL_ATK_GAIN}", "magenta")

    # ---------- 回合 ----------
    def end_player_turn(self):
        self.turn_count += 1
        for m in list(self.monsters):
            if m.fighter.is_dead() or m.ai is None:
                continue
            if self.over:
                break
            m.ai.take_turn(m, self)
        self.fov.compute(self.gmap, self.player.x, self.player.y)

    # ---------- 序列化 ----------
    def to_save_dict(self):
        return {
            "floor": self.floor,
            "max_floors": self.max_floors,
            "turn_count": self.turn_count,
            "rng": rng_state_to_json(self.rng.getstate()),
            "player": self._player_dict(),
            "levels": {str(k): v.to_dict() for k, v in self.levels.items()},
        }

    def _player_dict(self):
        d = self.player.to_dict()
        d["equipment"] = {
            "weapon": self.player.equipment["weapon"].to_dict()
            if self.player.equipment["weapon"] else None,
            "armor": self.player.equipment["armor"].to_dict()
            if self.player.equipment["armor"] else None,
        }
        return d

    @classmethod
    def from_save_dict(cls, d):
        game = cls.__new__(cls)
        game.rng = random.Random()
        game.rng.setstate(rng_state_from_json(d["rng"]))
        game.max_floors = d["max_floors"]
        game.floor = d["floor"]
        game.turn_count = d.get("turn_count", 0)
        game.messages = []
        game.over = False
        game.result = None
        game.input_queue = []
        game.pending_input = None

        game.levels = {int(k): LevelState.from_dict(v)
                       for k, v in d["levels"].items()}
        pd = d["player"]
        game.player = entity_from_dict(pd)
        from roguelike.entities import Inventory
        if game.player.inventory is None:
            game.player.inventory = Inventory()
        game.player.equipment = {"weapon": None, "armor": None}
        for slot in ("weapon", "armor"):
            if pd.get("equipment", {}).get(slot):
                game.player.equipment[slot] = Item.from_dict(pd["equipment"][slot])
        game._bind_floor()
        return game


def colored_safe(text, color):
    """消息直接存纯文本，渲染端不上色以简化（保留接口便于扩展）。"""
    return text
