# -*- coding: utf-8 -*-
"""全局平衡与常量配置。所有关键数字集中在此，便于平衡调整与审查。"""

# ---------- 地图 ----------
MAP_W = 72
MAP_H = 28
ROOMS_MIN = 9
ROOMS_MAX = 13
ROOM_MIN_W = 6
ROOM_MIN_H = 4
ROOM_MAX_W = 12
ROOM_MAX_H = 8
MAP_GEN_MAX_TRIES = 50  # 连通性不合格时的重生成上限

MAX_FLOORS = 5          # 至少 3 层，实际做 5 层，第 5 层有 Boss

# ---------- 视野 ----------
FOV_RADIUS = 8

# ---------- 玩家 ----------
PLAYER_BASE = {
    "hp": 30,
    "atk": 4,
    "defense": 1,
    "sight": FOV_RADIUS,
}
LEVEL_HP_GAIN = 6
LEVEL_ATK_GAIN = 1
LEVEL_DEF_GAIN = 1      # 每 2 级 +1（用奇偶控制）
EXP_BASE = 10           # 升到 2 级所需
EXP_GROWTH = 8          # 每级递增：exp_to_next = EXP_BASE + (level-1)*EXP_GROWTH

INVENTORY_CAPACITY = 12

# ---------- 战斗 ----------
CRIT_CHANCE = 0.10      # 暴击率
CRIT_MULT = 2.0
DMG_VARIANCE = 2        # 伤害随机浮动 0..DMG_VARIANCE
MIN_DAMAGE = 1          # 保底伤害

# ---------- 敌人 ----------
# base 模板；实际数值按楼层深度缩放 depth_scale = 1 + 0.35 * (floor-1)
MONSTER_TEMPLATES = [
    # name, char, hp, atk, defense, exp, ai_speed, color, min_floor
    {"name": "哥布林", "char": "g", "hp": 8,  "atk": 3, "defense": 0, "exp": 5,  "color": "green",  "min_floor": 1},
    {"name": "洞穴蝙蝠", "char": "b", "hp": 5,  "atk": 2, "defense": 0, "exp": 4,  "color": "magenta", "min_floor": 1, "fast": True},
    {"name": "骷髅兵", "char": "s", "hp": 12, "atk": 4, "defense": 1, "exp": 8,  "color": "white",  "min_floor": 2},
    {"name": "兽人战士", "char": "O", "hp": 18, "atk": 6, "defense": 1, "exp": 14, "color": "yellow", "min_floor": 3},
    {"name": "石像鬼", "char": "D", "hp": 24, "atk": 7, "defense": 3, "exp": 22, "color": "cyan",   "min_floor": 4},
]
BOSS_TEMPLATE = {"name": "远古魔龙", "char": "W", "hp": 60, "atk": 10, "defense": 3, "exp": 80, "color": "red"}
DEPTH_SCALE = 0.35

# 每层怪物数量与物品数量
MONSTERS_PER_FLOOR = lambda f: 5 + f          # noqa: E731
ITEMS_PER_FLOOR = lambda f: 3 + f // 2        # noqa: E731

# ---------- 存档 ----------
SAVE_FILE = "save.json"
