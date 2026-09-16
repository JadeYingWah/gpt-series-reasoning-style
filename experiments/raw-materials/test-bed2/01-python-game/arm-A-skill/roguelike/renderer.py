# -*- coding: utf-8 -*-
"""终端渲染：ANSI 颜色、地图绘制、侧栏信息、消息日志。"""

import os
import sys

from roguelike.map_gen import TILE_FLOOR, TILE_STAIRS, TILE_WALL

# Windows 终端启用 ANSI 转义（os.system("") 触发 VT 处理）
if os.name == "nt":
    os.system("")

_COLORS = {
    "red": "31", "green": "32", "yellow": "33", "blue": "34",
    "magenta": "35", "cyan": "36", "white": "37", "gray": "90",
    "orange": "33", "pink": "35",
}


def colored(text, color):
    code = _COLORS.get(color, "37")
    return f"\033[{code}m{text}\033[0m"


def bold(text):
    return f"\033[1m{text}\033[0m"


def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def draw_map(gmap, fov, player, monsters, ground_items):
    """绘制整层地图。可见格全彩；已探索不可见格画暗色记忆。"""
    # 实体与物品按坐标索引
    ents = {}
    for m in monsters:
        if not m.fighter.is_dead():
            ents.setdefault((m.x, m.y), []).append(m)
    for gi in ground_items:
        ents.setdefault((gi["x"], gi["y"]), []).append(gi["item"])

    lines = []
    for y in range(gmap.height):
        row = []
        for x in range(gmap.width):
            if not fov.explored[y][x]:
                row.append(" ")
                continue
            visible = fov.visible[y][x]
            tile = gmap.tiles[y][x]
            here = ents.get((x, y))
            if (x, y) == (player.x, player.y):
                row.append(colored("@", "white") if visible else bold("@"))
            elif visible and here:
                obj = here[0]
                if isinstance(obj, str):
                    row.append(colored(obj.char, obj.color))
                else:  # Item
                    row.append(colored(obj.char, obj.color))
            elif visible:
                if tile == TILE_WALL:
                    row.append(colored("#", "gray"))
                elif tile == TILE_STAIRS:
                    row.append(colored(">", "yellow"))
                else:
                    row.append(colored(".", "gray"))
            else:  # 记忆区
                if tile == TILE_WALL:
                    row.append("\033[30m#\033[0m")
                elif tile == TILE_STAIRS:
                    row.append("\033[33m>\033[0m")
                else:
                    row.append("\033[30m.\033[0m")
        lines.append("".join(row))
    return "\n".join(lines)


def status_panel(game):
    """右侧状态栏文本（与地图并排由 main 输出逻辑处理，这里只生成内容）。"""
    p = game.player
    f = p.fighter
    from roguelike.entities import player_attack_power, player_defense
    atk = player_attack_power(p)
    dfn = player_defense(p)
    w = p.equipment["weapon"]
    a = p.equipment["armor"]
    lines = [
        bold(colored(f" 层: B{game.floor} / B{game.max_floors}", "cyan")),
        bold(f" 冒险者  Lv.{f.level}"),
        colored(f" HP: {f.hp}/{f.max_hp}", "red" if f.hp <= f.max_hp // 3 else "green"),
        f" EXP: {f.exp}/{f.exp_to_next}",
        f" 攻: {atk}" + (f" (+{w.power} {w.name})" if w else ""),
        f" 防: {dfn}" + (f" (+{a.power} {a.name})" if a else ""),
        f" 背包: {len(p.inventory.items)}/{p.inventory.capacity}",
        "",
        " [方向] wasd/hjkl/箭头",
        " [g] 拾取  [i] 背包  [.]等待",
        " [>] 下楼  [s] 存档  [l] 读档",
        " [q] 保存并退出",
        "",
    ]
    return "\n".join(lines)


def render(game):
    """完整一帧：地图 + 侧栏 + 消息日志。返回字符串。"""
    map_text = draw_map(game.gmap, game.fov, game.player,
                        game.monsters, game.ground_items)
    panel = status_panel(game)

    map_rows = map_text.split("\n")
    panel_rows = panel.split("\n")
    height = max(len(map_rows), len(panel_rows))
    # 地图右侧留 2 格空白再画面板
    out = []
    for i in range(height):
        left = map_rows[i] if i < len(map_rows) else ""
        right = panel_rows[i] if i < len(panel_rows) else ""
        out.append(f"{left}  {right}")

    visible_monsters = [m for m in game.monsters
                        if game.fov.visible[m.y][m.x] and not m.fighter.is_dead()]
    if visible_monsters:
        names = ", ".join(f"{m.name}({m.fighter.hp})" for m in visible_monsters[:6])
        out.append(colored(f" 视野内: {names}", "yellow"))
    out.append(" " + "-" * 100)
    for msg in game.messages[-5:]:
        out.append(" " + msg)
    return "\n".join(out)
