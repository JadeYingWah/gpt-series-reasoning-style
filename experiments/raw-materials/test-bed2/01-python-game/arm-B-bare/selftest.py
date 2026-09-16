"""自动化自检：地图/视野/战斗/AI/成长/存读档/烟雾测试/通关路径。

运行：python selftest.py
全部通过时退出码为 0，否则为 1。
"""

from __future__ import annotations

import json
import os
import random
import sys
from dataclasses import replace

if sys.platform == "win32":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from roguelike import ai, combat, config, engine, fov, items, mapgen, render, save
from roguelike.entities import spawn_enemy
from roguelike.mapgen import FLOOR, GameMap

RESULTS: list[tuple[bool, str, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((bool(cond), name, detail))
    tag = "PASS" if cond else "FAIL"
    line = f"[{tag}] {name}"
    if detail:
        line += f"  —— {detail}"
    print(line)


def make_open_floor(w: int, h: int, start: tuple[int, int]) -> engine.FloorData:
    """构造一张全地面的开放地图，用于 AI 精确测试。"""
    gm = GameMap(w, h)
    for y in range(h):
        for x in range(w):
            gm.tiles[y][x] = FLOOR
    return engine.FloorData(
        map=gm, enemies=[], ground_items=[], stairs=None, start=start
    )


def bfs_reachable(gm: mapgen.GameMap, sx: int, sy: int) -> set:
    seen = {(sx, sy)}
    queue = [(sx, sy)]
    while queue:
        cx, cy = queue.pop()
        for dx, dy in ai.DIRS4:
            nx, ny = cx + dx, cy + dy
            if gm.walkable(nx, ny) and (nx, ny) not in seen:
                seen.add((nx, ny))
                queue.append((nx, ny))
    return seen


def free_adjacent(st: engine.GameState) -> tuple[int, int] | None:
    p = st.player
    for dx, dy in ai.DIRS4:
        nx, ny = p.x + dx, p.y + dy
        if st.floor.map.walkable(nx, ny) and st.enemy_at(nx, ny) is None:
            return (nx, ny)
    return None


# ============ 1. 模块导入 ============
try:
    _mods = (config, fov, items, engine, combat, ai, render, save, mapgen)
    check("模块全部可导入", True, f"{len(_mods)} 个模块")
except Exception as exc:
    check("模块全部可导入", False, repr(exc))
    sys.exit(1)

# ============ 2. 三层地图生成 ============
st = engine.GameState(seed=11)
st.new_game()
check("生成至少 3 层地下城", len(st.floors) == config.FLOOR_COUNT,
      f"层数={len(st.floors)}")
check("每层出生点位于可走格",
      all(f.map.walkable(*f.start) for f in st.floors))

# ============ 3. 楼梯与魔王 ============
ok_stairs = (st.floors[0].stairs is not None
             and st.floors[1].stairs is not None
             and st.floors[0].map.walkable(*st.floors[0].stairs)
             and st.floors[1].map.walkable(*st.floors[1].stairs))
check("第 1/2 层均有下行楼梯", ok_stairs)
check("第 3 层没有楼梯（终点层）", st.floors[2].stairs is None)
bosses = [e for e in st.floors[2].enemies if e.boss]
check("第 3 层存在魔王 Boss", len(bosses) == 1,
      f"敌人总数={len(st.floors[2].enemies)}")

# ============ 4. 全图连通性 ============
ok_conn, detail = True, []
for i, f in enumerate(st.floors):
    reach = bfs_reachable(f.map, *f.start)
    targets = [(e.x, e.y) for e in f.enemies]
    if f.stairs:
        targets.append(f.stairs)
    targets += [(x, y) for (x, y, _) in f.ground_items]
    unreachable = [t for t in targets if t not in reach]
    if unreachable:
        ok_conn = False
        detail.append(f"第{i+1}层不可达:{unreachable[:3]}")
check("楼梯/敌人/道具全部可达（连通性）", ok_conn, "; ".join(detail))

# ============ 5. 视野 ============
p = st.player
check("玩家自身格在视野内", (p.x, p.y) in st.visible)
check("视野非空且已并入探索记录",
      len(st.visible) > 10 and st.floor.explored >= st.visible,
      f"可见={len(st.visible)}")
wall_seen = any(
    st.floor.map.tiles[y][x].char == "#" for (x, y) in st.visible
)
check("视野内包含墙面（ LOS 终点可见墙）", wall_seen)

# ============ 6. 伤害公式 ============
rng = random.Random(123)
ok_dmg, bad = True, ""
for _ in range(300):
    dmg, crit = combat.roll_damage(rng, 10, 3)
    if (crit and not (12 <= dmg <= 18)) or \
            (not crit and not (6 <= dmg <= 9)):
        ok_dmg, bad = False, f"越界 dmg={dmg} crit={crit}"
        break
    if dmg < 1:
        ok_dmg, bad = False, f"伤害<1 dmg={dmg}"
        break
check("伤害公式在边界内（含暴击翻倍）", ok_dmg, bad)
dmg2, _ = combat.roll_damage(rng, 1, 100, force_crit=True)
check("强制暴击最小伤害=2", dmg2 == 2, f"dmg={dmg2}")

# ============ 7. 战斗击杀与经验 ============
st7 = engine.GameState(seed=5)
st7.new_game()
adj = free_adjacent(st7)
enemy7 = spawn_enemy("slime", *adj)
st7.floor.enemies.append(enemy7)
xp0 = st7.player.xp
for _ in range(30):
    if enemy7.hp > 0:
        dx = enemy7.x - st7.player.x
        dy = enemy7.y - st7.player.y
        st7.player_move_or_attack(dx, dy)
    else:
        break
check("攻击相邻敌人直至击杀，获得经验",
      enemy7.hp <= 0 and enemy7 not in st7.floor.enemies
      and st7.player.xp >= xp0 + 8,
      f"xp {xp0}->{st7.player.xp}")

# ============ 8. 升级成长 ============
lv0 = st7.player.level
st7.player.add_xp(1000)
lv1 = st7.player.level
check("大量经验触发多次升级",
      lv1 >= lv0 + 5
      and st7.player.max_hp == config.PLAYER_TEMPLATE["hp"] + 12 * (lv1 - 1)
      and st7.player.base_atk == config.PLAYER_TEMPLATE["atk"] + 2 * (lv1 - 1),
      f"等级 {lv0}->{lv1}")

# ============ 9-12. 敌人 AI 四态 ============
# 9. 沉睡不醒
st9 = engine.GameState(seed=1)
st9.new_game()
fl9 = make_open_floor(40, 20, (5, 5))
st9.floors[st9.current] = fl9
st9.player.x, st9.player.y = 5, 5
e9 = spawn_enemy("slime", 15, 15)
fl9.enemies.append(e9)
st9.enemies_turn()
check("AI-睡眠：远距敌人保持沉睡", e9.state == "sleep" and (e9.x, e9.y) == (15, 15))

# 10. 发现惊醒
e10 = spawn_enemy("slime", 7, 5)
fl9.enemies.append(e10)
st9.enemies_turn()
check("AI-惊醒：进入视野后转入追击", e10.state == "chase",
      f"pos=({e10.x},{e10.y})")

# 11. BFS 追击逼近（orc 视距 6，摆放在距离 5 处确保真实触发追击）
st11 = engine.GameState(seed=2)
st11.new_game()
fl11 = make_open_floor(24, 8, (2, 3))
st11.floors[st11.current] = fl11
st11.player.x, st11.player.y = 2, 3
e11 = spawn_enemy("orc", 7, 3)
fl11.enemies.append(e11)
d0 = ai.manhattan(e11.x, e11.y, 2, 3)
for _ in range(3):
    st11.enemies_turn()
d1 = ai.manhattan(e11.x, e11.y, 2, 3)
check("AI-追击：三回合内显著逼近", e11.state == "chase" and d1 < d0,
      f"距离 {d0}->{d1}")

# 12. 相邻攻击（独立状态：敌人直接摆在玩家旁边）
st12 = engine.GameState(seed=3)
st12.new_game()
fl12 = make_open_floor(24, 8, (2, 3))
st12.floors[st12.current] = fl12
st12.player.x, st12.player.y = 2, 3
e12 = spawn_enemy("slime", 3, 3)
fl12.enemies.append(e12)
hp0 = st12.player.hp
st12.enemies_turn()
check("AI-攻击：相邻敌人对玩家造成伤害", st12.player.hp < hp0,
      f"hp {hp0}->{st12.player.hp}")

# ============ 13. 存读档一致性（序列化往返） ============
st13 = engine.GameState(seed=42)
st13.new_game()
for _ in range(8):
    opts = [(dx, dy) for dx, dy in ai.DIRS4
            if st13.floor.map.walkable(st13.player.x + dx, st13.player.y + dy)]
    if opts:
        st13.player_move_or_attack(*random.Random(0).choice(opts))
st13.player.hp = 10
st13.player.inventory.append(replace(items.ITEMS["potion_s"]))
st13.use_inventory(len(st13.player.inventory) - 1)
st13.recompute_fov()   # 对齐主循环时序：每回合行动后刷新视野再存档
d1 = json.dumps(save.serialize(st13), sort_keys=True, ensure_ascii=False)
loaded = save.deserialize(json.loads(d1))
d2 = json.dumps(save.serialize(loaded), sort_keys=True, ensure_ascii=False)
check("序列化往返完全一致（地图/敌人/道具/消息/RNG）",
      d1 == d2 and loaded.player.hp == st13.player.hp
      and loaded.current == st13.current)
loaded.player.gold += 999
check("读档副本独立（修改副本不影响原状态）",
      loaded.player.gold == st13.player.gold + 999)

# ============ 14. 存档文件 IO ============
tmp_save = "selftest_save.json"
save.save_game(st13, tmp_save)
ok_io = os.path.exists(tmp_save)
loaded2 = save.load_game(tmp_save)
check("存档写盘并可重新读入", ok_io and loaded2.player.hp == st13.player.hp)
os.remove(tmp_save)

# ============ 15. 道具使用与装备 ============
st15 = engine.GameState(seed=6)
st15.new_game()
st15.player.inventory = [replace(items.ITEMS["w0"]), replace(items.ITEMS["w1"])]
atk0 = st15.player.atk
st15.use_inventory(1)           # 装备铁剑(+4)
ok_equip = st15.player.weapon.name == "铁剑" and st15.player.atk == atk0 + 4
st15.use_inventory(0)           # 换装木剑(+2)，铁剑回到背包
ok_equip = ok_equip and st15.player.weapon.name == "木剑" \
    and st15.player.atk == atk0 + 2 \
    and any(it.name == "铁剑" for it in st15.player.inventory)
st15.player.hp = 10
st15.player.inventory.append(replace(items.ITEMS["potion_s"]))
ok_potion = st15.use_inventory(len(st15.player.inventory) - 1)
ok_potion = ok_potion and st15.player.hp == 30
st15.player.hp = st15.player.max_hp
st15.player.inventory.append(replace(items.ITEMS["potion_s"]))  # 补一支新药水
idx_full = len(st15.player.inventory) - 1
ok_full = (not st15.use_inventory(idx_full)) and \
    len(st15.player.inventory) == idx_full + 1
check("装备更换与药水使用/满血拒绝", ok_equip and ok_potion and ok_full)

# ============ 16. 楼层下降 ============
st16 = engine.GameState(seed=8)
st16.new_game()
st16.player.x, st16.player.y = st16.floors[0].stairs
ok_desc = st16.descend() and st16.current == 1 \
    and (st16.player.x, st16.player.y) == st16.floors[1].start
ok_desc2 = (not st16.descend()) and st16.current == 1
check("楼梯下行进入下一层并落在出生点", ok_desc and ok_desc2)

# ============ 17. 随机烟雾测试（400 回合随机代理） ============
def agent_turn(st: engine.GameState, rng: random.Random) -> tuple[bool, bool]:
    """返回 (是否消耗回合, 是否发生了战斗)。"""
    p = st.player
    fl = st.floor
    # 残血优先喝药
    if p.hp < p.max_hp * 0.4:
        for i, it in enumerate(p.inventory):
            if it.kind == "potion":
                return st.use_inventory(i), False
    # 攻击相邻敌人
    for dx, dy in ai.DIRS4:
        if st.enemy_at(p.x + dx, p.y + dy):
            before = {id(e): e.hp for e in fl.enemies}
            acted = st.player_move_or_attack(dx, dy)
            fought = acted and any(
                id(e) not in before or e.hp < before[id(e)] for e in fl.enemies
            )
            return acted, fought
    r = rng.random()
    if r < 0.05:
        return st.pickup(), False
    if r < 0.08:
        st.push("原地警戒。")
        return True, False
    # 追击最近敌人
    targets = [(e.x, e.y) for e in fl.enemies if e.hp > 0]
    if targets and rng.random() < 0.6:
        nearest = min(targets,
                      key=lambda t: ai.manhattan(t[0], t[1], p.x, p.y))
        blocked = {(e.x, e.y) for e in fl.enemies if e.hp > 0}
        step = ai.bfs_step(fl.map, blocked, p.x, p.y, *nearest)
        if step:
            return st.player_move_or_attack(*step), False
    options = [(dx, dy) for dx, dy in ai.DIRS4
               if fl.map.walkable(p.x + dx, p.y + dy)]
    if options:
        return st.player_move_or_attack(*rng.choice(options)), False
    return False, False


st17 = engine.GameState(seed=7)
st17.new_game()
rng17 = random.Random(7)
fights = descents = 0
crash = None
try:
    for _ in range(400):
        if st17.over:
            break
        acted, fought = agent_turn(st17, rng17)
        if fought:
            fights += 1
        if acted:
            if st17.floor.stairs and \
                    (st17.player.x, st17.player.y) == st17.floor.stairs:
                descents += 1
            st17.enemies_turn()
            st17.turn += 1
except Exception as exc:  # noqa: BLE001
    crash = repr(exc)
explored_total = sum(len(f.explored) for f in st17.floors)
check("随机代理 400 回合无崩溃",
      crash is None and fights >= 1 and explored_total > 60,
      f"战斗={fights} 下楼={descents} 探索={explored_total} "
      f"结局={'存活' if not st17.over else ('胜利' if st17.victory else '死亡')}")

# ============ 18. 通关路径 ============
st18 = engine.GameState(seed=9)
st18.new_game()
st18.current = 2                # 关键：切到第 3 层再传送/作战
boss18 = next(e for e in st18.floors[2].enemies if e.boss)
# 传送玩家到魔王相邻格（清掉占据该格的杂兵保证可达）
adj18 = None
for dx, dy in ai.DIRS4:
    nx, ny = boss18.x + dx, boss18.y + dy
    if st18.floors[2].map.walkable(nx, ny):
        adj18 = (nx, ny)
        break
st18.floors[2].enemies = [
    e for e in st18.floors[2].enemies
    if (e.x, e.y) != adj18 or e is boss18
]
st18.player.x, st18.player.y = adj18
st18.player.base_atk = 100
guard = 0
while not st18.over and guard < 10:
    dx = (boss18.x > st18.player.x) - (boss18.x < st18.player.x)
    dy = (boss18.y > st18.player.y) - (boss18.y < st18.player.y)
    st18.player_move_or_attack(dx, dy)
    guard += 1
drops = [it.name for (_, _, it) in st18.floors[2].ground_items]
check("击败魔王触发胜利结算并掉落神器",
      st18.over and st18.victory and "影魔之刃" in drops,
      f"掉落={drops}")

# ============ 19. 渲染冒烟 ============
try:
    text = render.render_text(st17)
    check("渲染输出包含地图与玩家", "@" in text and "#" in text)
except Exception as exc:  # noqa: BLE001
    check("渲染输出包含地图与玩家", False, repr(exc))

# ============ 汇总 ============
passed = sum(1 for ok, _, _ in RESULTS if ok)
total = len(RESULTS)
print("\n" + "=" * 52)
print(f"自检结果：{passed}/{total} 通过")
print("=" * 52)
for ok, name, detail in RESULTS:
    if not ok:
        print(f"  未通过：{name} {detail}")
sys.exit(0 if passed == total else 1)
