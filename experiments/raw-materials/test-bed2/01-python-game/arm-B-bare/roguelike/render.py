"""终端渲染：地图、HUD、消息、背包、帮助。"""

from __future__ import annotations

from . import config

LEGEND = (
    "@你  s/b/g/k/o/h敌人  B魔王  !药剂  /武器  ]护甲  $金币  >下楼"
    "（仅当前视野内的内容可见，已探索区域显示地形）"
)

GAME_TITLE = "暗影地穴 · Shadow Crypt"

TITLE_TEXT = f"""\
==================================================
        {GAME_TITLE}
        终 端 R o g u e l i k e  地 下 城
=================================================="""

HELP_TEXT = """\
================ 玩 法 说 明 ================
目标
  深入 3 层地下城，击败第 3 层的暗影魔王即获胜；
  生命归零则冒险失败。

操作（区分大小写）
  W/A/S/D   向 上/左/下/右 移动（撞上敌人即为攻击）
  . 或空格   原地等待一回合
  g         拾取脚下的道具
  e 或 >    站在楼梯上时下行到下一层
  i         打开背包（输入序号使用药水/装备武器护甲）
  S         保存游戏（大写 S；小写 s 是向下移动）
  ?         显示本帮助
  Q         退出（可选择先保存）

系统规则
  * 回合制：你行动一次，所有敌人行动一次。
  * 视野：只能看到周围 8 格内的景象，走过的地方会被记住。
  * 伤害 = 攻击 - 防御 + 随机浮动(-1~2)，10% 概率暴击（翻倍）。
  * 击败敌人获得经验，升级提升生命/攻击/防御。
  * 魔王每第 3 次攻击必定释放蓄力重击，注意节奏。
  * 下楼时会自动存档；敌人掉落装备、药水与金币。
  * 金币踩上去自动拾取；装备药水需按 g 拾取后按 i 使用。
============================================="""


def _glyph_at(state, x: int, y: int) -> str:
    fl = state.floor
    p = state.player
    if (x, y) == (p.x, p.y):
        return "@"
    e = state.enemy_at(x, y)
    if e:
        return e.glyph
    for (ix, iy, it) in fl.ground_items:
        if (ix, iy) == (x, y):
            return it.glyph
    return fl.map.tiles[y][x].char


def map_lines(state) -> list[str]:
    fl = state.floor
    lines = []
    for y in range(fl.map.h):
        row = []
        for x in range(fl.map.w):
            if (x, y) in state.visible:
                row.append(_glyph_at(state, x, y))
            elif (x, y) in fl.explored:
                row.append(fl.map.tiles[y][x].char)
            else:
                row.append(" ")
        lines.append("".join(row))
    return lines


def _hp_bar(hp: int, mx: int, width: int = 20) -> str:
    filled = int(width * hp / mx) if mx else 0
    return "[" + "#" * filled + "." * (width - filled) + "]"


def hud_lines(state) -> list[str]:
    p = state.player
    wname = f"{p.weapon.name}(+{p.weapon.atk})" if p.weapon else "空手"
    aname = f"{p.armor.name}(+{p.armor.dfn})" if p.armor else "无"
    return [
        f"{GAME_TITLE} · 第 {state.current + 1} 层 · 回合 {state.turn}",
        f"生命 {p.hp:>3}/{p.max_hp:<3}{_hp_bar(p.hp, p.max_hp)}"
        f" 攻击 {p.atk:<2} 防御 {p.dfn:<2} 等级 {p.level}"
        f" 经验 {p.xp}/{p.xp_next} 金币 {p.gold}",
        f"武器 {wname}  护甲 {aname}",
    ]


def message_lines(state, n: int = 5) -> list[str]:
    return list(state.messages)[-n:]


def render_text(state) -> str:
    lines = []
    lines += hud_lines(state)
    lines.append("-" * config.MAP_W)
    lines += map_lines(state)
    lines.append("-" * config.MAP_W)
    lines += message_lines(state)
    lines.append(LEGEND)
    lines.append(
        "[WASD]移动 [.]等待 [g]拾取 [e]下楼 [i]背包 [S]存档 [?]帮助 [Q]退出"
    )
    return "\n".join(lines)


def inventory_text(state) -> str:
    p = state.player
    lines = ["========== 背 包 =========="]
    if not p.inventory:
        lines.append("（空空如也）")
    kind_tag = {
        "potion": "药剂", "elixir": "药剂", "weapon": "武器",
        "armor": "护甲", "gold": "金币",
    }
    for i, it in enumerate(p.inventory, 1):
        lines.append(
            f"  {i}. [{kind_tag.get(it.kind, '?')}] {it.name} — {it.desc}"
        )
    lines.append("输入序号 使用/装备，0 返回。")
    return "\n".join(lines)
