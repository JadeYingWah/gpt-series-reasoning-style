"""视野计算：基于 Bresenham 直线的射线视野（FOV / LOS）。"""

from __future__ import annotations


def bresenham(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    """返回从 (x0,y0) 到 (x1,y1) 的直线经过的所有格点（含两端）。"""
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        points.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    return points


def has_los(game_map, x0: int, y0: int, x1: int, y1: int) -> bool:
    """两点之间是否通视（终点本身允许是不透明的墙，墙面可见）。"""
    pts = bresenham(x0, y0, x1, y1)
    for (x, y) in pts[1:-1]:
        if not game_map.transparent(x, y):
            return False
    return True


def compute_fov(game_map, px: int, py: int, radius: int) -> set[tuple[int, int]]:
    """以 (px,py) 为中心、radius 为半径计算可见格点集合。"""
    visible: set[tuple[int, int]] = set()
    r2 = radius * radius
    for y in range(max(0, py - radius), min(game_map.h, py + radius + 1)):
        for x in range(max(0, px - radius), min(game_map.w, px + radius + 1)):
            if (x - px) ** 2 + (y - py) ** 2 > r2:
                continue
            if has_los(game_map, px, py, x, y):
                visible.add((x, y))
    return visible
