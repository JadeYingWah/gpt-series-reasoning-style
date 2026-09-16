"""游戏状态与回合引擎：楼层构建、玩家行动、敌人回合、胜负判定。"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field, replace

from . import ai, combat, config, fov
from . import items as items_mod
from . import mapgen
from .entities import Enemy, Player, spawn_enemy
from .items import Item
from .mapgen import GameMap, STAIRS


@dataclass
class FloorData:
    map: GameMap
    enemies: list[Enemy]
    ground_items: list[tuple[int, int, Item]]   # (x, y, Item)
    stairs: tuple[int, int] | None              # 下行楼梯位置
    start: tuple[int, int]                      # 本层出生点
    explored: set = field(default_factory=set)


class GameState:
    def __init__(self, seed: int | None = None):
        self.seed = seed if seed is not None else random.randrange(2 ** 31)
        self.rng = random.Random(self.seed)
        self.floors: list[FloorData] = []
        self.current = 0
        self.player: Player | None = None
        self.messages: deque[str] = deque(maxlen=200)
        self.visible: set[tuple[int, int]] = set()
        self.turn = 0
        self.over = False
        self.victory = False
        self.autosave_flag = False

    # ---------- 基础 ----------

    @property
    def floor(self) -> FloorData:
        return self.floors[self.current]

    def push(self, msg: str) -> None:
        self.messages.append(msg)

    def enemy_at(self, x: int, y: int) -> Enemy | None:
        for e in self.floor.enemies:
            if e.hp > 0 and e.x == x and e.y == y:
                return e
        return None

    def recompute_fov(self) -> None:
        self.visible = fov.compute_fov(
            self.floor.map, self.player.x, self.player.y, config.FOV_RADIUS
        )
        self.floor.explored |= self.visible

    # ---------- 开局 ----------

    def new_game(self) -> None:
        self.floors = [self._build_floor(i) for i in range(config.FLOOR_COUNT)]
        self.current = 0
        start = self.floors[0].start
        t = config.PLAYER_TEMPLATE
        self.player = Player(
            x=start[0], y=start[1],
            hp=t["hp"], max_hp=t["hp"],
            base_atk=t["atk"], base_def=t["dfn"],
        )
        self.messages = deque(maxlen=200)
        self.turn = 0
        self.over = False
        self.victory = False
        self.autosave_flag = False
        self.push("你醒来时已身处幽暗的地穴…… 深处传来魔王的低吼。")
        self.push("目标：抵达第 3 层，击败暗影魔王。输入 ? 查看帮助。")
        self.recompute_fov()

    def _build_floor(self, idx: int) -> FloorData:
        rng = self.rng
        gm = mapgen.generate_dungeon(rng)
        rooms = gm.rooms
        start = rooms[0].center

        # 楼梯：放在距出生点最远的房间
        stairs: tuple[int, int] | None = None
        if idx < config.FLOOR_COUNT - 1:
            stairs_room = max(
                rooms, key=lambda r: ai.manhattan(*r.center, *start)
            )
            stairs = stairs_room.center
            gm.tiles[stairs[1]][stairs[0]] = STAIRS

        floor = FloorData(
            map=gm, enemies=[], ground_items=[],
            stairs=stairs, start=start,
        )

        def occupied(x: int, y: int) -> bool:
            return (
                self.enemy_on(floor, x, y) is not None
                or any(ix == x and iy == y for ix, iy, _ in floor.ground_items)
            )

        # 普通敌人
        for key, n in config.FLOOR_ENEMIES[idx]:
            for _ in range(n):
                pos = self._random_floor_pos(
                    rng, floor, avoid=[start], min_dist=6, occupied=occupied
                )
                if pos:
                    floor.enemies.append(spawn_enemy(key, *pos))

        # 魔王（仅第 3 层）：放在距出生点最远的房间中心
        if idx == config.FLOOR_COUNT - 1:
            boss_room = max(
                rooms, key=lambda r: ai.manhattan(*r.center, *start)
            )
            bx, by = boss_room.center
            if occupied(bx, by):
                spot = self._spot_in_room(rng, floor, boss_room, occupied)
                if spot:
                    bx, by = spot
            floor.enemies.append(spawn_enemy("boss", bx, by))

        # 地面道具
        for _ in range(config.FLOOR_ITEMS[idx]):
            avoid = [start] + ([stairs] if stairs else [])
            pos = self._random_floor_pos(
                rng, floor, avoid=avoid, min_dist=3, occupied=occupied
            )
            if pos:
                it = items_mod.roll_loot(rng, idx + 1)
                floor.ground_items.append((pos[0], pos[1], it))
        return floor

    @staticmethod
    def enemy_on(floor: FloorData, x: int, y: int) -> Enemy | None:
        for e in floor.enemies:
            if e.hp > 0 and e.x == x and e.y == y:
                return e
        return None

    def _random_floor_pos(
        self, rng, floor: FloorData,
        avoid: list[tuple[int, int]], min_dist: int, occupied,
    ) -> tuple[int, int] | None:
        gm = floor.map
        for _ in range(300):
            x = rng.randint(1, gm.w - 2)
            y = rng.randint(1, gm.h - 2)
            if not gm.walkable(x, y):
                continue
            if occupied(x, y):
                continue
            if any(ai.manhattan(x, y, ax, ay) < min_dist for ax, ay in avoid):
                continue
            return (x, y)
        return None

    def _spot_in_room(self, rng, floor: FloorData, room, occupied):
        candidates = [
            (x, y)
            for y in range(room.y1, room.y2)
            for x in range(room.x1, room.x2)
            if floor.map.walkable(x, y) and not occupied(x, y)
        ]
        return rng.choice(candidates) if candidates else None

    # ---------- 玩家行动 ----------

    def player_move_or_attack(self, dx: int, dy: int) -> bool:
        """移动或攻击；撞墙不消耗回合。返回是否消耗了回合。"""
        p = self.player
        nx, ny = p.x + dx, p.y + dy
        enemy = self.enemy_at(nx, ny)
        if enemy:
            combat.player_attack(self, enemy)
            return True
        if not self.floor.map.walkable(nx, ny):
            self.push("前方是墙壁。")
            return False
        p.x, p.y = nx, ny
        self._on_enter_tile()
        return True

    def _on_enter_tile(self) -> None:
        p = self.player
        fl = self.floor
        remaining = []
        for (x, y, it) in fl.ground_items:
            if (x, y) == (p.x, p.y) and it.kind == "gold":
                p.gold += it.value
                self.push(f"捡到 {it.value} 金币。")
            else:
                remaining.append((x, y, it))
        fl.ground_items = remaining
        for (x, y, it) in fl.ground_items:
            if (x, y) == (p.x, p.y):
                self.push(f"脚边有 {it.name}（按 g 拾取）。")
                break
        if fl.stairs and (p.x, p.y) == fl.stairs:
            self.push("这里有一道向下的楼梯（按 e 下楼）。")

    def pickup(self) -> bool:
        p = self.player
        fl = self.floor
        for idx, (x, y, it) in enumerate(fl.ground_items):
            if (x, y) == (p.x, p.y):
                fl.ground_items.pop(idx)
                if it.kind == "gold":
                    p.gold += it.value
                    self.push(f"捡到 {it.value} 金币。")
                else:
                    p.inventory.append(it)
                    self.push(f"拾取了 {it.name}。")
                return True
        self.push("这里没有可拾取的东西。")
        return False

    def use_inventory(self, index: int) -> bool:
        """使用药水 / 装备武器护甲；返回是否消耗了回合。"""
        p = self.player
        inv = p.inventory
        if not (0 <= index < len(inv)):
            self.push("无效的序号。")
            return False
        it = inv[index]
        if it.kind == "potion":
            if p.hp >= p.max_hp:
                self.push("生命值已满，无需使用。")
                return False
            p.hp = min(p.max_hp, p.hp + it.heal)
            inv.pop(index)
            self.push(f"使用了{it.name}，恢复 {it.heal} 点生命。")
            return True
        if it.kind == "elixir":
            p.base_atk += it.atk
            inv.pop(index)
            self.push("力量涌遍全身，攻击永久 +1！")
            return True
        if it.kind in ("weapon", "armor"):
            old = p.weapon if it.kind == "weapon" else p.armor
            inv.pop(index)
            if it.kind == "weapon":
                p.weapon = it
            else:
                p.armor = it
            if old is not None:
                inv.append(old)
            self.push(f"装备了 {it.name}。")
            return True
        self.push("这件东西无法使用。")
        return False

    def descend(self) -> bool:
        p = self.player
        st = self.floor.stairs
        if st and (p.x, p.y) == st:
            self.current += 1
            p.x, p.y = self.floor.start
            self.push(f"你沿楼梯下行，来到了第 {self.current + 1} 层。")
            if self.current + 1 == config.FLOOR_COUNT:
                self.push("魔王的气息弥漫在空气中…… 小心！")
            self.recompute_fov()
            self.autosave_flag = True
            return True
        self.push("这里没有下行楼梯。")
        return False

    # ---------- 结算 ----------

    def kill_enemy(self, enemy: Enemy) -> None:
        self.push(f"{enemy.name}被击败了！")
        if enemy in self.floor.enemies:
            self.floor.enemies.remove(enemy)
        if enemy.boss:
            for it in items_mod.BOSS_DROPS:
                self.floor.ground_items.append(
                    (enemy.x, enemy.y, replace(it))
                )
            self.victory = True
            self.over = True
            self.push("暗影魔王倒下了！地穴的诅咒随之消散——你胜利了！")
        else:
            drop = items_mod.roll_loot(self.rng, enemy.tier)
            if drop is not None:
                self.floor.ground_items.append((enemy.x, enemy.y, drop))
                self.push(f"{enemy.name}掉下了 {drop.name}。")
        self.push(f"获得 {enemy.xp_reward} 点经验。")
        for m in self.player.add_xp(enemy.xp_reward):
            self.push(m)

    def enemies_turn(self) -> None:
        for enemy in list(self.floor.enemies):
            if self.over:
                break
            if enemy.hp > 0:
                ai.take_enemy_turn(self, enemy)
        if self.player.hp <= 0:
            self.player.hp = 0
            self.over = True
