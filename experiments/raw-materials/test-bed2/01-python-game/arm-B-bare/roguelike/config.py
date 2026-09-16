"""全局配置常量。"""

# 地图尺寸
MAP_W = 40
MAP_H = 20

# 视野半径
FOV_RADIUS = 8

# 房间生成参数
MAX_ROOMS = 12
ROOM_MIN_SIZE = 4
ROOM_MAX_SIZE = 9
MIN_ROOMS = 5

# 楼层数量（至少 3 层）
FLOOR_COUNT = 3

# 暴击几率
CRIT_CHANCE = 0.10

# 经验曲线：升到下一级所需经验 = XP_BASE + XP_GROWTH * (level - 1)
XP_BASE = 25
XP_GROWTH = 25

# 玩家初始属性
PLAYER_TEMPLATE = {
    "hp": 50,
    "atk": 6,
    "dfn": 1,
}

# 每层敌人配置: [(enemy_key, 数量), ...]
FLOOR_ENEMIES = [
    [("slime", 4), ("bat", 3)],
    [("goblin", 5), ("skeleton", 4)],
    [("orc", 5), ("hellhound", 4)],
]

# 每层地面道具数量
FLOOR_ITEMS = [3, 4, 5]

# 存档文件名
SAVE_FILE = "save.json"
