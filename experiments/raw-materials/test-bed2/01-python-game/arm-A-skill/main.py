# -*- coding: utf-8 -*-
"""入口：交互主循环 / --demo 自动演示 / --seed 指定种子。

用法：
    python main.py                # 新游戏（有存档时询问是否继续）
    python main.py --seed 42      # 固定种子新游戏
    python main.py --demo 300     # 无头自动演示 300 回合（自动打怪下楼）
    python main.py --load         # 读档继续

按键：
    移动  w a s d / h j k l / 方向键
    等待  .     拾取  g     背包  i     下楼  >
    存档  S（大写）   退出并存档  q
"""

import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8")

from roguelike.engine import Game
from roguelike.renderer import bold, clear_screen, colored, render
from roguelike.save_load import has_save, load_game, save_game

# ---------- 键盘输入 ----------
if sys.platform == "win32":
    import msvcrt

    def read_key():
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):        # 功能/方向键前缀
            ch2 = msvcrt.getwch()
            return {"H": "up", "P": "down", "K": "left", "M": "right"}.get(ch2, None)
        return ch
else:
    import termios
    import tty

    def read_key():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch


MOVE_DIRS = {
    "w": (0, -1), "k": (0, -1), "up": (0, -1),
    "s": (0, 1), "j": (0, 1), "down": (0, 1),
    "a": (-1, 0), "h": (-1, 0), "left": (-1, 0),
    "d": (1, 0), "l": (1, 0), "right": (1, 0),
}


def save_and_quit(game, msg="已保存进度，再见，冒险者。"):
    save_game(game.to_save_dict())
    print(colored(msg, "cyan"))
    return False


def handle_key(game, key):
    """处理一个按键。返回 False 表示退出游戏循环。"""
    if key in (None, ""):
        return True
    if key == "\x03":                     # Ctrl+C
        return save_and_quit(game)
    if key in ("q", "Q"):
        return save_and_quit(game)
    if key == "S":
        save_game(game.to_save_dict())
        game.add_msg("游戏已存档", "cyan")
        return True
    if key == "i":
        inventory_screen(game)
        return True
    if key == ">":
        game.descend()
        return True
    if key == ".":
        game.wait()
        return True
    if key == "g":
        game.pickup()
        return True
    if key in MOVE_DIRS:
        dx, dy = MOVE_DIRS[key]
        game.player_move_or_attack(dx, dy)
    return True


def inventory_screen(game):
    inv = game.player.inventory
    while True:
        clear_screen()
        print(bold("== 背包 ==") + "  （数字=使用/装备，d数字=丢弃，回车/Esc/i 返回）\n")
        if not inv.items:
            print(" （空）")
        for i, item in enumerate(inv.items):
            eq = ""
            if item in game.player.equipment.values():
                eq = colored(" [已装备]", "green")
            print(f" [{i}] {colored(item.char, item.color)} {item.name}{eq} — {item.description}")
        print()
        key = read_key()
        if key in ("\r", "\n", "\x1b", "i"):
            return
        if key.isdigit():
            game.use_item(int(key))
            return
        if key == "d":
            k2 = read_key()
            if k2.isdigit():
                game.drop_item(int(k2))
            return


def draw(game):
    clear_screen()
    print(render(game))


def new_or_continue():
    if has_save():
        print(bold("检测到存档。"))
        print(" [1] 继续上次的冒险   [2] 开始新游戏（覆盖存档）")
        choice = input("选择: ").strip()
        if choice == "1":
            state = load_game()
            if state:
                return Game.from_save_dict(state)
            print(colored("存档损坏，改为新游戏。", "red"))
    return Game()


# ---------- demo 自动策略 ----------
def demo_step(game):
    """简单策略：保命下楼 → 喝药 → 打相邻怪 → 拾取 → 走向楼梯/追击。"""
    p = game.player
    f = p.fighter

    # 1. 站在楼梯上且血量不健康 → 先下楼休整
    if game.gmap.stairs_pos and (p.x, p.y) == game.gmap.stairs_pos \
            and f.hp <= f.max_hp * 0.6:
        game.descend()
        return

    # 2. 低血喝药
    if f.hp <= f.max_hp * 0.4:
        for i, item in enumerate(p.inventory.items):
            if item.name in ("治疗药水", "治疗卷轴"):
                game.use_item(i)
                return

    # 3. 攻击相邻怪
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        if game.monster_at(p.x + dx, p.y + dy):
            game.player_move_or_attack(dx, dy)
            return

    # 4. 拾取脚下
    if any(g["x"] == p.x and g["y"] == p.y for g in game.ground_items):
        game.pickup()
        return

    # 5. 目标点：Boss 层追最近可见怪（无则探索前沿）；常规层走楼梯
    if game.gmap.stairs_pos is None:
        if not _chase_nearest_visible(game):
            _explore_frontier(game)
    else:
        if not _move_toward(game, game.gmap.stairs_pos, on_arrive=game.descend):
            # 寻路失败（怪堵路）→ 主动打最近的可见怪，而非傻等
            if not _chase_nearest_visible(game):
                game.wait()


def _explore_frontier(game):
    """走向最近的未探索可达格（揭开战争迷雾，用于 Boss 层找 Boss）。

    持续沿用同一探索目标直至抵达，避免每回合 goal 跳变导致徘徊。
    """
    from roguelike.map_gen import reachable_tiles
    p = game.player
    reach = reachable_tiles(game.gmap, (p.x, p.y))
    frontier = [c for c in reach if not game.fov.explored[c[1]][c[0]]]
    if not frontier:
        game.wait()
        return
    goal = getattr(game, "_demo_goal", None)
    if goal not in frontier:
        goal = min(frontier, key=lambda c: (c[0] - p.x) ** 2 + (c[1] - p.y) ** 2)
        game._demo_goal = goal
    if not _move_toward(game, goal):
        game._demo_goal = None
        # 去前沿的路被怪堵住 → 先追打可见怪（打完路通常就通了）
        if not _chase_nearest_visible(game):
            game.wait()


def _chase_nearest_visible(game):
    """走向可见怪并攻击。无可视怪返回 False。Boss 层优先直奔魔龙。"""
    from roguelike import config
    p = game.player
    visible = [m for m in game.monsters if not m.fighter.is_dead()
               and game.fov.visible[m.y][m.x]]
    if not visible:
        return False
    target = None
    if game.gmap.stairs_pos is None:
        bosses = [m for m in visible if m.name == config.BOSS_TEMPLATE["name"]]
        if bosses:
            target = bosses[0]
    if target is None:
        target = min(visible, key=lambda m: (m.x - p.x) ** 2 + (m.y - p.y) ** 2)
    return _move_toward(game, (target.x, target.y))


def _move_toward(game, goal, on_arrive=None):
    """朝 goal 走一步。只有已经站在 goal 上时才触发 on_arrive。"""
    from roguelike.ai import find_path
    p = game.player
    if (p.x, p.y) == goal:
        if on_arrive:
            on_arrive()
        return True
    nxt = find_path(game.gmap, (p.x, p.y), goal,
                    {(m.x, m.y) for m in game.monsters
                     if m.blocks and not m.fighter.is_dead()})
    if nxt:
        game.player_move_or_attack(nxt[0] - p.x, nxt[1] - p.y)
        return True
    return False


def run_demo(steps, seed=None):
    game = Game(seed=seed)
    for i in range(steps):
        if game.over:
            break
        demo_step(game)
        if i % 40 == 0:
            clear_screen()
            print(render(game))
    clear_screen()
    print(render(game))
    print()
    print(bold(f"=== 演示结束 ===  回合 {game.turn_count} | 层数 B{game.floor} | "
               f"Lv.{game.player.fighter.level} | HP {game.player.fighter.hp}/"
               f"{game.player.fighter.max_hp} | 结果: {game.result or '进行中'}"))


def run_interactive(args):
    if args.load:
        state = load_game()
        if not state:
            print(colored("没有可用存档，开始新游戏。", "red"))
            game = Game(seed=args.seed)
        else:
            game = Game.from_save_dict(state)
    elif args.seed is not None:
        game = Game(seed=args.seed)
    else:
        game = new_or_continue()

    game.add_msg("欢迎来到地下城。寻找楼梯（>）深入，第 5 层击败魔龙即胜利。", "cyan")
    draw(game)
    while not game.over:
        key = read_key()
        if not handle_key(game, key):
            return
        draw(game)

    # 结束画面
    draw(game)
    print()
    if game.result == "victory":
        print(bold(colored(" ★ 胜利！你击败了远古魔龙，拯救了这片大陆！ ", "yellow")))
    else:
        print(bold(colored(" ✝ 你死亡了……地下城又多了一具白骨。 ", "red")))
    print(f" 回合数: {game.turn_count}  到达: B{game.floor}  等级: Lv.{game.player.fighter.level}")
    print(colored("（死亡不保存进度）", "gray"))


def main():
    ap = argparse.ArgumentParser(description="Roguelike 地下城探险")
    ap.add_argument("--seed", type=int, default=None, help="固定随机种子")
    ap.add_argument("--demo", type=int, default=None, metavar="N",
                    help="无头自动演示 N 回合")
    ap.add_argument("--load", action="store_true", help="从存档继续")
    args = ap.parse_args()

    if args.demo is not None:
        run_demo(args.demo, seed=args.seed)
    else:
        run_interactive(args)


if __name__ == "__main__":
    main()
