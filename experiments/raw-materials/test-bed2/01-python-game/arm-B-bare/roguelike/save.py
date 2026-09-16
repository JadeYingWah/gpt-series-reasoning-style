"""存档 / 读档：完整游戏状态与 RNG 状态序列化为 JSON。"""

from __future__ import annotations

import json
import os
import random
from collections import deque
from dataclasses import asdict

from . import config
from .entities import Enemy, Player
from .engine import FloorData, GameState
from .items import Item
from .mapgen import FLOOR, STAIRS, WALL, GameMap

SAVE_VERSION = 1


# ---------- RNG 状态 ----------

def _rng_to_json(rng: random.Random) -> dict:
    ver, internal, gauss = rng.getstate()
    return {"ver": ver, "internal": list(internal), "gauss": gauss}


def _rng_from_json(d: dict) -> random.Random:
    r = random.Random()
    r.setstate((d["ver"], tuple(d["internal"]), d["gauss"]))
    return r


# ---------- 地图 ----------

def _map_rows(gm: GameMap) -> list[str]:
    return ["".join(t.char for t in row) for row in gm.tiles]


def _map_from_rows(rows: list[str]) -> GameMap:
    gm = GameMap(len(rows[0]), len(rows))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == ">":
                gm.tiles[y][x] = STAIRS
            elif ch == ".":
                gm.tiles[y][x] = FLOOR
            else:
                gm.tiles[y][x] = WALL
    return gm


# ---------- 序列化 ----------

def serialize(state: GameState) -> dict:
    p = state.player
    player_dict = {
        "x": p.x, "y": p.y,
        "hp": p.hp, "max_hp": p.max_hp,
        "base_atk": p.base_atk, "base_def": p.base_def,
        "level": p.level, "xp": p.xp, "xp_next": p.xp_next,
        "gold": p.gold,
        "inventory": [asdict(it) for it in p.inventory],
        "weapon": asdict(p.weapon) if p.weapon else None,
        "armor": asdict(p.armor) if p.armor else None,
    }
    floors = []
    for f in state.floors:
        floors.append({
            "map_rows": _map_rows(f.map),
            "enemies": [asdict(e) for e in f.enemies],
            "items": [[x, y, asdict(it)] for (x, y, it) in f.ground_items],
            "stairs": list(f.stairs) if f.stairs else None,
            "start": list(f.start),
            "explored": sorted(f.explored),
        })
    return {
        "version": SAVE_VERSION,
        "seed": state.seed,
        "current": state.current,
        "turn": state.turn,
        "over": state.over,
        "victory": state.victory,
        "rng": _rng_to_json(state.rng),
        "player": player_dict,
        "floors": floors,
        "messages": list(state.messages),
    }


def deserialize(data: dict) -> GameState:
    if data.get("version") != SAVE_VERSION:
        raise ValueError("存档版本不兼容")
    st = GameState.__new__(GameState)   # 手工装配，跳过 __init__
    st.rng = _rng_from_json(data["rng"])
    st.seed = data["seed"]
    st.current = data["current"]
    st.turn = data["turn"]
    st.over = data["over"]
    st.victory = data["victory"]
    st.autosave_flag = False
    st.messages = deque(data["messages"], maxlen=200)
    st.visible = set()

    pd = data["player"]
    p = Player(
        x=pd["x"], y=pd["y"], hp=pd["hp"], max_hp=pd["max_hp"],
        base_atk=pd["base_atk"], base_def=pd["base_def"],
    )
    p.level = pd["level"]
    p.xp = pd["xp"]
    p.xp_next = pd["xp_next"]
    p.gold = pd["gold"]
    p.inventory = [Item(**d) for d in pd["inventory"]]
    p.weapon = Item(**pd["weapon"]) if pd["weapon"] else None
    p.armor = Item(**pd["armor"]) if pd["armor"] else None
    st.player = p

    st.floors = []
    for fd in data["floors"]:
        f = FloorData(
            map=_map_from_rows(fd["map_rows"]),
            enemies=[], ground_items=[],
            stairs=tuple(fd["stairs"]) if fd["stairs"] else None,
            start=tuple(fd["start"]),
        )
        for ed in fd["enemies"]:
            f.enemies.append(Enemy(**ed))
        f.ground_items = [
            (x, y, Item(**d)) for x, y, d in fd["items"]
        ]
        f.explored = set(map(tuple, fd["explored"]))
        st.floors.append(f)
    st.recompute_fov()
    return st


# ---------- 文件 IO ----------

def save_game(state: GameState, path: str | None = None) -> str:
    path = path or config.SAVE_FILE
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(serialize(state), fp, ensure_ascii=False, indent=1)
    return path


def load_game(path: str | None = None) -> GameState:
    path = path or config.SAVE_FILE
    with open(path, encoding="utf-8") as fp:
        return deserialize(json.load(fp))


def has_save(path: str | None = None) -> bool:
    return os.path.exists(path or config.SAVE_FILE)
