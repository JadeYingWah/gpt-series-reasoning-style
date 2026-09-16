# -*- coding: utf-8 -*-
"""地图生成：随机房间 + L 形走廊 + BFS 连通性保证。"""

import random
from collections import deque

from roguelike import config

TILE_WALL = 0
TILE_FLOOR = 1
TILE_STAIRS = 2


class Room:
    def __init__(self, x, y, w, h):
        self.x1, self.y1 = x, y
        self.x2, self.y2 = x + w, y + h

    def center(self):
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2

    def intersects(self, other):
        # 外扩 1 格保证房间之间永远有墙隔开
        return (self.x1 - 1 <= other.x2 and self.x2 + 1 >= other.x1 and
                self.y1 - 1 <= other.y2 and self.y2 + 1 >= other.y1)

    def random_inside(self, rng):
        x = rng.randint(self.x1 + 1, self.x2 - 2)
        y = rng.randint(self.y1 + 1, self.y2 - 2)
        return x, y


class GameMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [[TILE_WALL] * width for _ in range(height)]
        self.rooms = []

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and self.tiles[y][x] != TILE_WALL

    def is_transparent(self, x, y):
        return self.in_bounds(x, y) and self.tiles[y][x] != TILE_WALL

    def carve_room(self, room):
        for y in range(room.y1, room.y2):
            for x in range(room.x1, room.x2):
                self.tiles[y][x] = TILE_FLOOR
        self.rooms.append(room)

    def carve_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[y][x] = TILE_FLOOR

    def carve_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[y][x] = TILE_FLOOR

    def connect_rooms(self, r1, r2, rng):
        """L 形走廊连接两房间中心，方向随机先后。"""
        x1, y1 = r1.center()
        x2, y2 = r2.center()
        if rng.random() < 0.5:
            self.carve_h_tunnel(x1, x2, y1)
            self.carve_v_tunnel(y1, y2, x2)
        else:
            self.carve_v_tunnel(y1, y2, x1)
            self.carve_h_tunnel(x1, x2, y1)

    # ---- 序列化 ----
    def to_dict(self):
        return {"width": self.width, "height": self.height,
                "tiles": [row[:] for row in self.tiles]}

    @classmethod
    def from_dict(cls, d):
        m = cls(d["width"], d["height"])
        m.tiles = [row[:] for row in d["tiles"]]
        m.stairs_pos = m.find_stairs()
        return m

    def find_stairs(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == TILE_STAIRS:
                    return (x, y)
        return None


def reachable_tiles(game_map, start):
    """BFS：返回从 start 出发所有可达的行走格坐标集合。"""
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if game_map.is_walkable(nx, ny) and (nx, ny) not in seen:
                seen.add((nx, ny))
                q.append((nx, ny))
    return seen


def generate_map(floor, rng=None):
    """生成一整层地图。返回 (game_map, start_pos, stairs_pos)。

    保证：所有房间互相连通、楼梯可达。重试直到满足（带上限）。
    """
    rng = rng or random.Random()
    for _ in range(config.MAP_GEN_MAX_TRIES):
        gmap = _try_generate(floor, rng)
        if gmap is not None:
            return gmap
    raise RuntimeError("地图生成失败：超过最大重试次数")


def _try_generate(floor, rng):
    gmap = GameMap(config.MAP_W, config.MAP_H)
    n_rooms = rng.randint(config.ROOMS_MIN, config.ROOMS_MAX)

    for _ in range(n_rooms * 6):
        if len(gmap.rooms) >= n_rooms:
            break
        w = rng.randint(config.ROOM_MIN_W, config.ROOM_MAX_W)
        h = rng.randint(config.ROOM_MIN_H, config.ROOM_MAX_H)
        x = rng.randint(1, config.MAP_W - w - 1)
        y = rng.randint(1, config.MAP_H - h - 1)
        new_room = Room(x, y, w, h)
        if any(new_room.intersects(r) for r in gmap.rooms):
            continue
        gmap.carve_room(new_room)
        if len(gmap.rooms) > 1:
            gmap.connect_rooms(gmap.rooms[-2], new_room, rng)

    if len(gmap.rooms) < 2:
        return None

    start = gmap.rooms[0].center()
    stairs = gmap.rooms[-1].center()

    # 连通性：从起点 BFS，楼梯必须可达
    reach = reachable_tiles(gmap, start)
    if stairs not in reach:
        return None

    gmap.tiles[stairs[1]][stairs[0]] = TILE_STAIRS
    gmap.start_pos = start
    gmap.stairs_pos = stairs
    return gmap
