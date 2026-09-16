"""暗影地穴 —— 程序入口与主循环。

运行：python main.py
"""

from __future__ import annotations

import os
import sys

# Windows 控制台默认 GBK，强制切到 UTF-8 避免中文乱码
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from roguelike import config, engine, render, save  # noqa: E402


def clear() -> None:
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def pause() -> None:
    try:
        input("\n（回车继续）")
    except (EOFError, KeyboardInterrupt):
        pass


def show_help() -> None:
    clear()
    print(render.HELP_TEXT)
    pause()


def inventory_turn(state: engine.GameState) -> None:
    """背包子界面：输入序号使用/装备；操作会消耗一回合。"""
    while True:
        state.recompute_fov()
        clear()
        print(render.render_text(state))
        print()
        print(render.inventory_text(state))
        try:
            cmd = input("背包> ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if cmd in ("0", "", "b", "q"):
            return
        if cmd.isdigit():
            consumed = state.use_inventory(int(cmd) - 1)
            if consumed:
                state.enemies_turn()
                state.turn += 1
                return


def game_loop(state: engine.GameState) -> None:
    while True:
        state.recompute_fov()
        clear()
        print(render.render_text(state))

        if state.over:
            if state.victory:
                print("\n========== 胜 利 ==========")
                print("你击败了暗影魔王，地穴重见光明！")
            else:
                print("\n========== 你死亡了 ==========")
                print("黑暗吞噬了你的身影……")
            print(f"存活回合数：{state.turn}")
            pause()
            return

        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        acted = False

        if cmd in ("w", "a", "s", "d"):
            dx, dy = {"w": (0, -1), "s": (0, 1),
                      "a": (-1, 0), "d": (1, 0)}[cmd]
            acted = state.player_move_or_attack(dx, dy)
        elif cmd in (".", " "):
            state.push("你原地警戒。")
            acted = True
        elif cmd == "g":
            acted = state.pickup()
        elif cmd in ("e", ">"):
            acted = state.descend()
        elif cmd == "i":
            inventory_turn(state)
            continue
        elif cmd == "S":
            try:
                path = save.save_game(state)
                state.push(f"已保存到 {path}。")
            except OSError as exc:
                state.push(f"保存失败：{exc}")
        elif cmd == "?":
            show_help()
        elif cmd == "Q":
            try:
                ans = input("退出前保存进度？(y/N) ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                ans = ""
            if ans == "y":
                save.save_game(state)
                print("已保存。")
            return
        elif cmd == "":
            continue
        else:
            state.push("未知命令，输入 ? 查看帮助。")
            continue

        if acted:
            state.enemies_turn()
            state.turn += 1
            if state.autosave_flag:
                state.autosave_flag = False
                try:
                    save.save_game(state)
                    state.push("（下楼自动存档完成）")
                except OSError:
                    pass


def main() -> None:
    while True:
        clear()
        print(render.TITLE_TEXT)
        print()
        print("   1) 新的冒险")
        print("   2) 继续冒险")
        print("   3) 玩法说明")
        print("   0) 退出")
        try:
            choice = input("选择> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if choice == "1":
            state = engine.GameState()
            state.new_game()
            game_loop(state)
        elif choice == "2":
            if save.has_save():
                try:
                    state = save.load_game()
                except Exception as exc:  # 存档损坏时不崩溃
                    print(f"读档失败：{exc}")
                    pause()
                    continue
                game_loop(state)
            else:
                print("没有找到存档文件。")
                pause()
        elif choice == "3":
            show_help()
        elif choice == "0":
            break


if __name__ == "__main__":
    main()
