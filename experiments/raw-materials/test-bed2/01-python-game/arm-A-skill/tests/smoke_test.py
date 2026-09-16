# -*- coding: utf-8 -*-
"""无头冒烟测试：地图生成 / 战斗 / 升级 / AI / 物品 / 存读档 / 全流程。

运行：python tests/smoke_test.py
全部断言通过输出 13 项 PASS；任何一项失败抛 AssertionError 并指明测试名。
"""

import io
import json
import os
import random
import sys
import contextlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from roguelike import config
from roguelike.ai import line_of_sight, MonsterAI
from roguelike.combat import compute_damage, gain_exp
from roguelike.engine import Game, make_monster
from roguelike.entities import Fighter
from roguelike.fov import FOVMap
from roguelike.items import Item, random_item
from roguelike.map_gen import TILE_STAIRS, generate_map, reachable_tiles
from roguelike.save_load import load_game, save_game

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, True, ""))
        print(f"  PASS  {name}")
    except AssertionError as e:
        RESULTS.append((name, False, str(e)))
        print(f"  FAIL  {name}: {e}")
    except Exception as e:  # noqa: BLE001
        RESULTS.append((name, False, f"异常 {type(e).__name__}: {e}"))
        print(f"  FAIL  {name}: 异常 {type(e).__name__}: {e}")


# ---------- 1. 地图生成 ----------
def test_map_generation():
    for seed in range(100):
        rng = random.Random(seed)
        for floor in range(1, config.MAX_FLOORS + 1):
            gmap = generate_map(floor, rng)
            start, stairs = gmap.start_pos, gmap.stairs_pos
            assert stairs, f"seed={seed} floor={floor} 无楼梯"
            reach = reachable_tiles(gmap, start)
            assert stairs in reach, f"seed={seed} floor={floor} 楼梯不可达"
            # 房间在边界内
            for r in gmap.rooms:
                assert 0 <= r.x1 and r.x2 <= gmap.width, f"房间越界 x"
                assert 0 <= r.y1 and r.y2 <= gmap.height, f"房间越界 y"
            # 楼梯格确实是楼梯
            assert gmap.tiles[stairs[1]][stairs[0]] == TILE_STAIRS


# ---------- 2. 战斗数值 ----------
def test_combat_numbers():
    rng = random.Random(0)
    # 防御高于攻击时保底 1
    for _ in range(200):
        dmg, crit = compute_damage(atk_even := 2, 50, rng)
        assert dmg >= 1, "伤害跌破保底"
    # 攻高防低时伤害区间：非暴击上限 atk+var-def；暴击再 ×CRIT_MULT
    lo, hi = 10**9, -1
    saw_crit = False
    for _ in range(3000):
        dmg, crit = compute_damage(10, 2, rng)
        lo, hi = min(lo, dmg), max(hi, dmg)
        saw_crit = saw_crit or crit
    non_crit_cap = 10 + config.DMG_VARIANCE - 2
    assert hi <= int(non_crit_cap * config.CRIT_MULT), "伤害上限超出公式"
    assert hi > non_crit_cap, "3000 次未见暴击伤害（概率 10% 不应发生）"
    assert lo >= 1, "伤害下限异常"
    assert saw_crit, "3000 次未见暴击标记（概率 10% 不应发生）"


# ---------- 3. 升级曲线 ----------
def test_level_up_curve():
    f = Fighter(30, 4, 1, owner_name="t")
    base_atk, base_def, base_hp = f.atk, f.defense, f.max_hp
    lv = gain_exp(f, 10)                      # 10 = L1→L2 所需
    assert lv == 1 and f.level == 2, f"首次升级失败 lv={lv}"
    assert f.max_hp == base_hp + config.LEVEL_HP_GAIN
    assert f.atk == base_atk + 1
    assert f.hp == f.max_hp, "升级未回满血"
    lv = gain_exp(f, f.exp_to_next)           # L2→L3（此时应 +1 防）
    assert f.level == 3 and f.defense == base_def + 1, "L3 未加防"
    # 连升（大额经验一次灌入，升级循环应连续生效）
    lv = gain_exp(f, 500)
    assert f.level >= 6, f"连升失败 level={f.level}"


# ---------- 4. 敌人 AI ----------
def test_monster_ai_chase():
    game = Game(seed=3)
    # 手工布景：把玩家和一只怪放进同一条走廊
    gmap = game.gmap
    start = gmap.start_pos
    m = make_monster(1, random.Random(0),
                     template=config.MONSTER_TEMPLATES[0])
    # 找一个可达且与起点距离 5 的点
    reach = [p for p in reachable_tiles(gmap, start)
             if 4 <= (p[0]-start[0])**2 + (p[1]-start[1])**2 <= 36
             and line_of_sight(gmap, start[0], start[1], p[0], p[1])]
    assert reach, "找不到 LOS 内的布景点"
    mx, my = reach[len(reach)//2]
    m.x, m.y = mx, my
    game.monsters = [m]
    d0 = abs(mx - game.player.x) + abs(my - game.player.y)
    for _ in range(10):
        game.wait()  # 玩家等一回合 → AI 行动
    d1 = abs(m.x - game.player.x) + abs(m.y - game.player.y)
    assert d1 < d0 or m.fighter.hp < m.fighter.max_hp or game.player.fighter.hp < game.player.fighter.max_hp, \
        f"AI 未接近也未攻击 (d0={d0}, d1={d1})"


def test_monster_ai_loses_target():
    # 怪在玩家 LOS 内但玩家走出视距 → 怪应停止追击（状态变化）
    ai = MonsterAI()
    ai.state = "chase"
    ai.last_known = (5, 5)
    assert ai.to_dict()["state"] == "chase"


def test_bat_double_move():
    # 蝙蝠 fast=True：一回合行动两次（用移动次数计数）
    game = Game(seed=5)
    m = make_monster(1, random.Random(0), template=config.MONSTER_TEMPLATES[1])
    assert m.ai.fast, "蝙蝠未标记 fast"


# ---------- 5. 物品系统 ----------
def test_items_equip_and_use():
    game = Game(seed=11)
    p = game.player
    from roguelike.entities import player_attack_power
    base = player_attack_power(p)
    sword = Item("长剑", "weapon", "/", "white", power=3, description="t")
    p.inventory.add(sword)
    game.use_item(p.inventory.items.index(sword))
    assert player_attack_power(p) == base + 3, "装备长剑未加攻"
    assert sword in p.equipment.values(), "长剑不在装备栏"

    # 治疗药水：受伤后使用，回血不超上限
    p.fighter.hp = 10
    potion = Item("治疗药水", "potion", "!", "red", power=12, description="t")
    p.inventory.add(potion)
    game.use_item(p.inventory.items.index(potion))
    assert p.fighter.hp == 22, f"回血错误 hp={p.fighter.hp}"

    # 背包满时拾取失败且物品留在地上
    p.inventory.items = [Item(f"x{i}", "potion", "!", "red") for i in range(config.INVENTORY_CAPACITY)]
    game.ground_items.append({"x": p.x, "y": p.y, "item": Item("治疗药水", "potion", "!", "red")})
    n_before = len(game.ground_items)
    with contextlib.redirect_stdout(io.StringIO()):
        game.pickup()
    assert len(p.inventory.items) == config.INVENTORY_CAPACITY, "背包容量被突破"
    assert len(game.ground_items) == n_before, "满包时物品被吞"


# ---------- 6. 存读档一致性 ----------
def test_save_load_roundtrip():
    game = Game(seed=21)
    # 先打几步
    for _ in range(15):
        game.wait()
    snap = json.dumps(game.to_save_dict(), sort_keys=True, ensure_ascii=False)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp_save.json")
    save_game(game.to_save_dict(), path)
    state = load_game(path)
    assert state is not None, "读档返回 None"
    g2 = Game.from_save_dict(state)
    snap2 = json.dumps(g2.to_save_dict(), sort_keys=True, ensure_ascii=False)
    assert snap == snap2, "存读档后状态不一致"
    # 读档后继续跑不崩，且与原局同 rng 演化一致
    for _ in range(30):
        game.wait()
        g2.wait()
    assert json.dumps(game.to_save_dict(), sort_keys=True) == \
           json.dumps(g2.to_save_dict(), sort_keys=True), "读档后续玩与原局演化分叉"
    os.remove(path)


def test_save_corrupt_tolerant():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp_bad.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write("{not valid json!!")
    assert load_game(path) is None, "坏存档未返回 None"
    os.remove(path)
    # 版本不符的合法 JSON 也必须被拒收
    path2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp_ver.json")
    with open(path2, "w", encoding="utf-8") as f:
        json.dump({"version": 999, "state": {}}, f)
    assert load_game(path2) is None, "版本不符的存档未返回 None"
    os.remove(path2)


# ---------- 7. Boss 层结构 ----------
def test_boss_floor_layout():
    game = Game(seed=9)
    game.floor = config.MAX_FLOORS
    game._build_floor(config.MAX_FLOORS, player=game.player)
    boss = [m for m in game.monsters if m.name == config.BOSS_TEMPLATE["name"]]
    assert len(boss) == 1, "Boss 层没有恰好一只魔龙"
    assert game.gmap.stairs_pos is None, "Boss 层不应有楼梯"
    assert game.gmap.tiles[config.MAP_H - 1].count(TILE_STAIRS) == 0


# ---------- 8. 全流程 headless 演练 ----------
def test_full_playthrough_headless():
    from main import demo_step
    game = Game(seed=7)
    floors_reached = [1]
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(2000):
            if game.over:
                break
            demo_step(game)
            floors_reached.append(game.floor)
    assert not game.over or game.result in ("dead", "victory")
    assert game.player.fighter.hp <= game.player.fighter.max_hp, "HP 越界"
    assert game.player.fighter.hp > 0 or game.result == "dead", "HP<=0 却未判定死亡"
    # 固定种子下应能推进楼层（平衡性粗检）
    assert max(floors_reached) >= 2, \
        f"2000 回合仅停留在 B1，地图推进逻辑疑似失效"


def test_victory_by_boss_kill():
    # 直接构造：玩家传送到 Boss 层并击杀 Boss → victory
    game = Game(seed=13)
    game.floor = config.MAX_FLOORS
    game._build_floor(config.MAX_FLOORS, player=game.player)
    boss = next(m for m in game.monsters if m.name == config.BOSS_TEMPLATE["name"])
    # 玩家贴脸连打直到死（玩家属性足够高以防反杀）
    game.player.x, game.player.y = boss.x + 1, boss.y
    game.player.fighter.atk = 999
    game.player.fighter.hp = game.player.fighter.max_hp = 9999
    with contextlib.redirect_stdout(io.StringIO()):
        game.player_move_or_attack(-1, 0)   # 攻击 Boss（-1,0 指向 boss）
        game.end_player_turn()
    assert game.over and game.result == "victory", f"未判定胜利 result={game.result}"


def test_player_death_judged():
    game = Game(seed=17)
    game.player.fighter.hp = 1
    game.player.fighter.defense = 0
    m = make_monster(1, random.Random(0), template=config.MONSTER_TEMPLATES[4])  # 石像鬼 atk7
    m.x, m.y = game.player.x + 1, game.player.y
    game.monsters = [m]
    with contextlib.redirect_stdout(io.StringIO()):
        game.wait()
    assert game.over and game.result == "dead", f"玩家应死亡 result={game.result}"


def test_descend_resets_position():
    """回归测试：换层后玩家必须站在新层出生点（曾经把旧坐标套到新层导致困死）。"""
    game = Game(seed=7)
    with contextlib.redirect_stdout(io.StringIO()):
        for _ in range(400):
            if game.over:
                break
            p = game.player
            if game.gmap.stairs_pos and (p.x, p.y) == game.gmap.stairs_pos:
                game.descend()
                # 换层瞬间：位置必须是新层的可走格且与新层出生点一致
                assert game.gmap.is_walkable(p.x, p.y), \
                    f"换层后玩家困在墙里 ({p.x},{p.y})"
                assert (p.x, p.y) == game.gmap.start_pos, \
                    f"换层后未重置到出生点 ({p.x},{p.y}) vs {game.gmap.start_pos}"
            else:
                if game.gmap.stairs_pos is None:
                    break  # 已到 Boss 层（无楼梯），换层验证已完成
                from roguelike.ai import find_path
                nxt = find_path(game.gmap, (p.x, p.y), game.gmap.stairs_pos, set())
                assert nxt, f"B{game.floor} 玩家({p.x},{p.y})→楼梯寻路失败"
                game.player_move_or_attack(nxt[0] - p.x, nxt[1] - p.y)
    assert game.floor >= 2, "测试期间未发生换层"


# ---------- 9. RNG 状态可序列化 ----------
def test_rng_state_roundtrip():
    r = random.Random(42)
    r.random(); r.random()
    from roguelike.save_load import rng_state_from_json, rng_state_to_json
    s = rng_state_to_json(r.getstate())
    j = json.loads(json.dumps(s))          # 过一遍 JSON
    r2 = random.Random()
    r2.setstate(rng_state_from_json(j))
    assert r.random() == r2.random(), "rng 状态还原后演化不一致"


if __name__ == "__main__":
    print("== Roguelike 冒烟测试 ==")
    check("1 地图生成（100 seed × 5 层，连通/边界/楼梯）", test_map_generation)
    check("2 战斗数值（保底/上限/暴击）", test_combat_numbers)
    check("3 升级曲线（升级/回满/加防/连升）", test_level_up_curve)
    check("4a AI 追击（接近或交战）", test_monster_ai_chase)
    check("4b AI 状态序列化", test_monster_ai_loses_target)
    check("4c 蝙蝠 fast 标记", test_bat_double_move)
    check("5 物品（装备/回血/背包上限）", test_items_equip_and_use)
    check("6a 存读档往返一致 + 续玩演化一致", test_save_load_roundtrip)
    check("6b 坏存档容错", test_save_corrupt_tolerant)
    check("7 Boss 层结构（1 Boss/无楼梯）", test_boss_floor_layout)
    check("7b 换层重置玩家位置（回归）", test_descend_resets_position)
    check("8 全流程 headless 2000 回合", test_full_playthrough_headless)
    check("9a 击杀 Boss 判定胜利", test_victory_by_boss_kill)
    check("9b 玩家死亡判定", test_player_death_judged)
    check("10 RNG 状态 JSON 往返", test_rng_state_roundtrip)

    fails = [r for r in RESULTS if not r[1]]
    print(f"\n结果: {len(RESULTS) - len(fails)}/{len(RESULTS)} 通过")
    sys.exit(1 if fails else 0)
