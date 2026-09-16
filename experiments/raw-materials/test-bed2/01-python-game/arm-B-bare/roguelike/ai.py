"""敌人 AI：睡眠 → 发现 → BFS 追击 → 相邻攻击；未发现时徘徊。"""

from __future__ import annotations

from collections import deque

from . import combat
from .fov import has_los

DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def manhattan(ax: int, ay: int, bx: int, by: int) -> int:
    return abs(ax - bx) + abs(ay - by)


def bfs_step(
    game_map, blocked: set[tuple[int, int]],
    sx: int, sy: int, tx: int, ty: int,
) -> tuple[int, int] | None:
    """BFS 寻路：返回从 (sx,sy) 通往 (tx,ty) 的第一步偏移，不可达返回 None。

    blocked 中的格子不可通行，但目标格本身永远允许作为终点。
    """
    if (sx, sy) == (tx, ty):
        return None
    q: deque[tuple[int, int]] = deque([(sx, sy)])
    prev: dict[tuple[int, int], tuple[int, int] | None] = {(sx, sy): None}
    found = False
    while q:
        cx, cy = q.popleft()
        if (cx, cy) == (tx, ty):
            found = True
            break
        for dx, dy in DIRS4:
            nx, ny = cx + dx, cy + dy
            if not game_map.walkable(nx, ny) or (nx, ny) in prev:
                continue
            if (nx, ny) in blocked and (nx, ny) != (tx, ty):
                continue
            prev[(nx, ny)] = (cx, cy)
            q.append((nx, ny))
    if not found:
        return None
    node = (tx, ty)
    while prev[node] != (sx, sy):
        node = prev[node]
    return node[0] - sx, node[1] - sy


def take_enemy_turn(game, enemy) -> None:
    """执行一只敌人的一回合行动。"""
    player = game.player
    fl = game.floor
    dist = manhattan(enemy.x, enemy.y, player.x, player.y)
    sees_player = (
        dist <= enemy.detect
        and has_los(fl.map, enemy.x, enemy.y, player.x, player.y)
    )

    # 状态切换：未追击中的敌人一旦发现玩家就转入追击
    if enemy.state != "chase":
        if sees_player:
            enemy.state = "chase"
            game.push(f"{enemy.name}发现了你！")
        elif enemy.state == "sleep":
            return

    # 相邻直接攻击
    if dist == 1:
        combat.enemy_attack(game, enemy)
        return

    blocked = {
        (e.x, e.y) for e in fl.enemies if e is not enemy and e.hp > 0
    }

    if enemy.state == "chase":
        step = bfs_step(fl.map, blocked, enemy.x, enemy.y, player.x, player.y)
        if step is None:
            # 路径被队友挡死时退化为贪心逼近
            best: tuple[int, int] | None = None
            best_d = dist
            for dx, dy in DIRS4:
                nx, ny = enemy.x + dx, enemy.y + dy
                if fl.map.walkable(nx, ny) and (nx, ny) not in blocked:
                    d = manhattan(nx, ny, player.x, player.y)
                    if d < best_d:
                        best, best_d = (dx, dy), d
            step = best
        if step:
            enemy.x += step[0]
            enemy.y += step[1]
        return

    # 徘徊：一定概率随机走一格（不踩玩家、不踩队友）
    if game.rng.random() < 0.4:
        dx, dy = game.rng.choice(DIRS4)
        nx, ny = enemy.x + dx, enemy.y + dy
        if (
            fl.map.walkable(nx, ny)
            and (nx, ny) not in blocked
            and (nx, ny) != (player.x, player.y)
        ):
            enemy.x, enemy.y = nx, ny
