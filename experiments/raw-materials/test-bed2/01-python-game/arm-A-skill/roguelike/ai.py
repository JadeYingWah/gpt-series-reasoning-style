# -*- coding: utf-8 -*-
"""敌人 AI：视野感知 → 追击（视距内 BFS 寻路）→ 相邻攻击；失联后游荡。"""

import random
from collections import deque

from roguelike import config
from roguelike.map_gen import reachable_tiles


def line_of_sight(gmap, x1, y1, x2, y2):
    """Bresenham 视线：起点到终点之间无墙即可见（不含终点障碍判断）。"""
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    x, y = x1, y1
    while (x, y) != (x2, y2):
        # 起点之后的中间格必须透明；终点本身不查（目标可以站在可见格上）
        if (x, y) != (x1, y1) and not gmap.is_transparent(x, y):
            return False
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    return True


def find_path(gmap, start, goal, blocked, max_nodes=2500):
    """BFS 最短路。blocked：不可通行的实体占位集合。返回下一步坐标或 None。

    max_nodes 默认覆盖整图（72×28=2016 格），大跨度寻路不被截断。
    """
    if start == goal:
        return None
    seen = {start}
    parent = {}
    q = deque([start])
    nodes = 0
    while q and nodes < max_nodes:
        x, y = q.popleft()
        nodes += 1
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not gmap.is_walkable(nx, ny) or (nx, ny) in seen:
                continue
            if (nx, ny) in blocked and (nx, ny) != goal:
                continue
            seen.add((nx, ny))
            parent[(nx, ny)] = (x, y)
            if (nx, ny) == goal:
                # 回溯到起点的下一步
                cur = (nx, ny)
                while parent[cur] != start:
                    cur = parent[cur]
                return cur
            q.append((nx, ny))
    return None


class MonsterAI:
    def __init__(self, fast=False):
        self.fast = fast                  # 蝙蝠：一回合动两次
        self.state = "idle"               # idle | chase | wander
        self.wander_dir = None

    # ---- 序列化 ----
    def to_dict(self):
        return {"fast": self.fast, "state": self.state,
                "wander_dir": list(self.wander_dir) if self.wander_dir else None}

    @classmethod
    def from_dict(cls, d):
        ai = cls(d["fast"])
        ai.state = d["state"]
        wd = d.get("wander_dir")
        ai.wander_dir = tuple(wd) if wd else None
        return ai

    def take_turn(self, monster, game):
        """一回合行动。game 需提供：gmap, player, monsters, rng, 事件回调 attack。"""
        moves = 2 if self.fast else 1
        for _ in range(moves):
            if monster.fighter.is_dead():
                break
            self._single_step(monster, game)

    def _single_step(self, monster, game):
        gmap = game.gmap
        player = game.player
        mx, my = monster.x, monster.y
        px, py = player.x, player.y
        dist2 = (mx - px) ** 2 + (my - py) ** 2

        # 感知：视距内且视线无遮挡 → 进入/保持追击并更新目标位置
        if dist2 <= config.FOV_RADIUS ** 2 and line_of_sight(gmap, mx, my, px, py):
            self.state = "chase"
            self.last_known = (px, py)

        if self.state == "chase":
            target = getattr(self, "last_known", (px, py))
            if (mx, my) == target:
                self.state = "wander"
                return
            # 相邻 → 攻击
            if abs(mx - player.x) <= 1 and abs(my - player.y) <= 1 and \
               (abs(mx - px) + abs(my - py)) == 1:
                game.monster_attack(monster)
                return
            blocked = {(m.x, m.y) for m in game.monsters
                       if m is not monster and m.blocks}
            if (player.x, player.y) in blocked:
                blocked.discard((player.x, player.y))
            nxt = find_path(gmap, (mx, my), target, blocked)
            if nxt:
                game.move_monster(monster, nxt[0], nxt[1])
            return

        # idle / wander：小概率游荡一步
        rng = game.rng
        if rng.random() < 0.4:
            if not self.wander_dir or rng.random() < 0.3:
                self.wander_dir = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            nx, ny = mx + self.wander_dir[0], my + self.wander_dir[1]
            if gmap.is_walkable(nx, ny):
                game.move_monster(monster, nx, ny)
