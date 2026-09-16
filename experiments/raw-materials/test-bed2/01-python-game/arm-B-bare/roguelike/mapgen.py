"""随机地图生成：房间 + 走廊的经典 Roguelike 算法。"""

from __future__ import annotations

import random

from . import config


class Tile:
    __slots__ = ("char", "walkable", "transparent")

    def __init__(self, char: str, walkable: bool, transparent: bool):
        self.char = char
        self.walkable = walkable
        self.transparent = transparent


WALL = Tile("#", False, False)
FLOOR = Tile(".", True, True)
STAIRS = Tile(">", True, True)   # 下行楼梯（可走、可通视）


class Rect:
    """矩形房间；x2/y2 为开区间边界。"""

    def __init__(self, x: int, y: int, w: int, h: int):
        self.x1, self.y1 = x, y
        self.x2, self.y2 = x + w, y + h

    @property
    def center(self) -> tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    def intersects(self, other: "Rect", pad: int = 1) -> bool:
        return (
            self.x1 - pad < other.x2 and self.x2 + pad > other.x1
            and self.y1 - pad < other.y2 and self.y2 + pad > other.y1
        )


class GameMap:
    def __init__(self, w: int, h: int):
        self.w = w
        self.h = h
        self.tiles: list[list[Tile]] = [
            [WALL for _ in range(w)] for _ in range(h)
        ]
        self.rooms: list[Rect] = []

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def walkable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self.tiles[y][x].walkable

    def transparent(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self.tiles[y][x].transparent

    def carve_room(self, r: Rect) -> None:
        for y in range(r.y1, r.y2):
            for x in range(r.x1, r.x2):
                self.tiles[y][x] = FLOOR
        self.rooms.append(r)

    def carve_h(self, x0: int, x1: int, y: int) -> None:
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.tiles[y][x] = FLOOR

    def carve_v(self, y0: int, y1: int, x: int) -> None:
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.tiles[y][x] = FLOOR


def generate_dungeon(
    rng: random.Random, w: int | None = None, h: int | None = None
) -> GameMap:
    """生成房间互相连通的地下城；房间过少时自动重试。"""
    w = w or config.MAP_W
    h = h or config.MAP_H
    for _attempt in range(60):
        gm = GameMap(w, h)
        for _ in range(config.MAX_ROOMS):
            rw = rng.randint(config.ROOM_MIN_SIZE, config.ROOM_MAX_SIZE)
            rh = rng.randint(config.ROOM_MIN_SIZE, config.ROOM_MAX_SIZE)
            rx = rng.randint(1, w - rw - 2)
            ry = rng.randint(1, h - rh - 2)
            r = Rect(rx, ry, rw, rh)
            if any(r.intersects(o) for o in gm.rooms):
                continue
            gm.carve_room(r)
            if len(gm.rooms) > 1:
                px, py = gm.rooms[-2].center
                cx, cy = r.center
                if rng.random() < 0.5:
                    gm.carve_h(px, cx, py)
                    gm.carve_v(py, cy, cx)
                else:
                    gm.carve_v(py, cy, px)
                    gm.carve_h(px, cx, cy)
        if len(gm.rooms) >= config.MIN_ROOMS:
            return gm
    # 兜底：即使房间不足也返回（实际几乎不会触发）
    return gm
