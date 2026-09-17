# -*- coding: utf-8 -*-
"""
植物大战僵尸（Python tkinter 版）
双击"启动植物大战僵尸.bat"或直接用 Python 运行本文件即可游玩。
玩法：收集阳光 → 种植物 → 挡住一波波僵尸，守住 9x5 的草坪！
"""
import sys, random, math
import tkinter as tk

# ---------------- 常量 ----------------
CELL_W, CELL_H = 90, 95
COLS, ROWS = 9, 5
LAWN_X, LAWN_Y = 45, 112
W = LAWN_X + COLS * CELL_W + 10
H = LAWN_Y + ROWS * CELL_H + 10
HUD_TOP = 104
CARD_X, CARD_W, CARD_H = 120, 82, 88
SHOVEL_X = CARD_X + 4 * CARD_W + 6
TICK = 50  # ms

PLANTS = {
    "sunflower": dict(name="向日葵",  cost=50,  hp=120,  cd=7.5),
    "pea":       dict(name="豌豆射手", cost=100, hp=120,  cd=7.5),
    "wallnut":   dict(name="坚果墙",  cost=50,  hp=450,  cd=20),
    "cherry":    dict(name="樱桃炸弹", cost=150, hp=999,  cd=30),
}
CARD_ORDER = ["sunflower", "pea", "wallnut", "cherry"]

ZOMBIES = {
    "normal": dict(hp=100, speed=11),
    "cone":   dict(hp=200, speed=11),
    "bucket": dict(hp=380, speed=9),
}

# (时间, 普通组, 大波组)  大波组出现时打横幅
WAVE_PLAN = [
    (12,  ["normal"], None),
    (35,  ["normal", "normal"], None),
    (55,  ["normal", "cone"], None),
    (75,  ["normal", "normal", "cone"], None),
    (95,  [], ["normal", "normal", "cone", "normal", "cone"]),
    (115, ["bucket", "normal"], None),
    (135, ["cone", "cone", "normal"], None),
    (155, ["normal", "cone", "bucket"], None),
    (180, [], ["normal", "cone", "normal", "bucket", "cone", "normal", "bucket"]),
]
TOTAL_ZOMBIES = sum(len(a) + len(b or []) for _, a, b in WAVE_PLAN)


class Game:
    def __init__(self, root):
        self.root = root
        self.cv = tk.Canvas(root, width=W, height=H, bg="#3a2618", highlightthickness=0)
        self.cv.pack()
        self.cv.bind("<Button-1>", self.on_click)
        self.cv.bind("<Button-3>", self.on_right)
        self.fonts = lambda s, b="normal": ("Microsoft YaHei", s, b)
        self.reset()
        self.root.after(TICK, self.tick)
        if "--selftest" in sys.argv:
            self.root.after(1500, self.selftest_done)

    def selftest_done(self):
        print("SELFTEST OK")
        self.root.destroy()

    # ---------------- 状态重置 ----------------
    def reset(self):
        self.t = 0.0
        self.sun = 175
        self.plants = {}          # (r,c) -> dict
        self.zombies = []
        self.peas = []
        self.suns = []
        self.floats = []
        self.booms = []
        self.selected = None      # 选中的卡片类型
        self.shovel = False
        self.cooldown = {k: 0.0 for k in CARD_ORDER}
        self.sky_timer = 4.0
        self.wave_i = 0
        self.pending = []         # (spawn_time, type)
        self.spawned = 0
        self.banner = None        # (text, until)
        self.state = "play"       # play / win / lose
        self.zomb_head = 0        # 行走动画相位

    # ---------------- 主循环 ----------------
    def tick(self):
        try:
            if self.state == "play":
                self.update(TICK / 1000.0)
            self.draw()
        except tk.TclError:
            return
        self.root.after(TICK, self.tick)

    def update(self, dt):
        self.t += dt
        self.zomb_head += dt
        # 冷却
        for k in self.cooldown:
            self.cooldown[k] = max(0.0, self.cooldown[k] - dt)
        # 天降阳光
        self.sky_timer -= dt
        if self.sky_timer <= 0:
            self.sky_timer = random.uniform(6.5, 9.5)
            x = random.uniform(LAWN_X + 30, LAWN_X + COLS * CELL_W - 30)
            self.suns.append(dict(x=x, y=HUD_TOP - 10, ty=random.uniform(LAWN_Y + 60, H - 40),
                                  v=32, life=10, value=25))
        # 出怪计划
        while self.wave_i < len(WAVE_PLAN) and self.t >= WAVE_PLAN[self.wave_i][0]:
            _, normals, big = WAVE_PLAN[self.wave_i]
            queue = list(normals or [])
            if big:
                self.banner = ("⚠ 一大波僵尸正在接近！", self.t + 4.0)
                queue += list(big)
            for i, zt in enumerate(queue):
                self.pending.append((self.t + i * 2.6, zt))
            self.wave_i += 1
        while self.pending and self.t >= self.pending[0][0]:
            _, zt = self.pending.pop(0)
            row = random.randrange(ROWS)
            st = ZOMBIES[zt]
            self.zombies.append(dict(type=zt, row=row, x=W + 20,
                                     hp=st["hp"], maxhp=st["hp"], speed=st["speed"],
                                     bite=0.0, hit=0.0))
            self.spawned += 1
        if self.banner and self.t > self.banner[1]:
            self.banner = None
        # 阳光
        for s in self.suns:
            if s["y"] < s["ty"]:
                s["y"] = min(s["ty"], s["y"] + s["v"] * dt)
            else:
                s["life"] -= dt
        self.suns = [s for s in self.suns if s["life"] > 0]
        # 植物
        for (r, c), p in list(self.plants.items()):
            px = LAWN_X + c * CELL_W + CELL_W / 2
            py = LAWN_Y + r * CELL_H + CELL_H / 2
            if p["type"] == "sunflower":
                p["timer"] -= dt
                if p["timer"] <= 0:
                    p["timer"] = 9.0
                    self.suns.append(dict(x=px + random.uniform(-16, 16), y=py - 14,
                                          ty=py + random.uniform(8, 22), v=26, life=10, value=25))
            elif p["type"] == "pea":
                has = any(z["row"] == r and z["x"] > px - 10 for z in self.zombies)
                p["timer"] -= dt
                if has and p["timer"] <= 0:
                    p["timer"] = 1.4
                    self.peas.append(dict(x=px + 22, row=r, dmg=20))
            elif p["type"] == "cherry":
                p["fuse"] -= dt
                if p["fuse"] <= 0:
                    self.explode(px, py)
                    del self.plants[(r, c)]
        # 豌豆
        for pe in self.peas:
            pe["x"] += 320 * dt
            for z in self.zombies:
                if z["row"] == pe["row"] and abs(z["x"] - pe["x"]) < 18:
                    z["hp"] -= pe["dmg"]
                    z["hit"] = 0.12
                    pe["dead"] = True
                    break
        self.peas = [pe for pe in self.peas if not pe.get("dead") and pe["x"] < W + 20]
        # 僵尸
        for z in self.zombies:
            if z["hit"] > 0:
                z["hit"] -= dt
            front = z["x"] - 22
            col = int((front - LAWN_X) // CELL_W)
            r = z["row"]
            target = self.plants.get((r, col)) if 0 <= col < COLS else None
            if target:
                z["bite"] -= dt
                if z["bite"] <= 0:
                    z["bite"] = 0.8
                    target["hp"] -= 25
                    if target["hp"] <= 0:
                        del self.plants[(r, col)]
            else:
                z["x"] -= z["speed"] * dt
        self.zombies = [z for z in self.zombies if z["hp"] > 0 and z["x"] > LAWN_X - 28]
        # 特效
        for f in self.floats:
            f["t"] += dt
        self.floats = [f for f in self.floats if f["t"] < 1.1]
        for b in self.booms:
            b["t"] += dt
        self.booms = [b for b in self.booms if b["t"] < 0.5]
        # 胜负
        if any(z["x"] <= LAWN_X - 26 for z in self.zombies):
            self.state = "lose"
        if self.wave_i >= len(WAVE_PLAN) and not self.pending and not self.zombies:
            self.state = "win"

    def explode(self, px, py):
        self.booms.append(dict(x=px, y=py, t=0))
        for z in self.zombies:
            if math.hypot(z["x"] - px, (LAWN_Y + z["row"] * CELL_H + CELL_H / 2) - py) <= CELL_W * 1.6:
                z["hp"] -= 1800
                z["hit"] = 0.2

    # ---------------- 交互 ----------------
    def on_right(self, e):
        self.selected = None
        self.shovel = False

    def on_click(self, e):
        if self.state != "play":
            if self.restart_rect and self.restart_rect[0] <= e.x <= self.restart_rect[0] + 240 \
               and self.restart_rect[1] <= e.y <= self.restart_rect[1] + 56:
                self.reset()
            return
        # 点阳光
        for s in reversed(self.suns):
            if math.hypot(e.x - s["x"], e.y - s["y"]) < 26:
                self.sun += s["value"]
                self.floats.append(dict(x=s["x"], y=s["y"], txt="+25", t=0))
                self.suns.remove(s)
                return
        # 点卡片
        for i, k in enumerate(CARD_ORDER):
            x0 = CARD_X + i * CARD_W
            if x0 <= e.x <= x0 + CARD_W - 8 and 8 <= e.y <= 8 + CARD_H:
                if self.selected == k:
                    self.selected = None
                elif self.cooldown[k] <= 0 and self.sun >= PLANTS[k]["cost"]:
                    self.selected = k
                    self.shovel = False
                return
        # 铲子
        if SHOVEL_X <= e.x <= SHOVEL_X + 52 and 8 <= e.y <= 8 + CARD_H:
            self.shovel = not self.shovel
            self.selected = None
            return
        # 点草坪
        c = int((e.x - LAWN_X) // CELL_W)
        r = int((e.y - LAWN_Y) // CELL_H)
        if 0 <= r < ROWS and 0 <= c < COLS:
            if self.shovel:
                if (r, c) in self.plants:
                    del self.plants[(r, c)]
                    self.shovel = False
                return
            if self.selected:
                st = PLANTS[self.selected]
                if (r, c) not in self.plants and self.sun >= st["cost"]:
                    self.sun -= st["cost"]
                    self.cooldown[self.selected] = st["cd"]
                    p = dict(type=self.selected, hp=st["hp"], maxhp=st["hp"])
                    if self.selected == "sunflower":
                        p["timer"] = 5.0
                    if self.selected == "pea":
                        p["timer"] = 0.5
                    if self.selected == "cherry":
                        p["fuse"] = 0.9
                    self.plants[(r, c)] = p
                    self.selected = None

    # ---------------- 绘制 ----------------
    def draw(self):
        cv = self.cv
        cv.delete("all")
        self.draw_top()
        # 草坪
        for r in range(ROWS):
            for c in range(COLS):
                x0 = LAWN_X + c * CELL_W
                y0 = LAWN_Y + r * CELL_H
                cv.create_rectangle(x0, y0, x0 + CELL_W, y0 + CELL_H,
                                    fill="#4a9c3d" if (r + c) % 2 else "#56ac46", outline="")
        # 种植预览
        if self.selected:
            cv.create_text(W / 2, LAWN_Y - 8, text="点击草地种植：" + PLANTS[self.selected]["name"],
                           font=self.fonts(12), fill="#eaffea", anchor="s")
        for (r, c), p in self.plants.items():
            self.draw_plant(r, c, p)
        for pe in self.peas:
            cv.create_oval(pe["x"] - 7, LAWN_Y + pe["row"] * CELL_H + CELL_H / 2 - 7,
                           pe["x"] + 7, LAWN_Y + pe["row"] * CELL_H + CELL_H / 2 + 7,
                           fill="#4ce04c", outline="#2a8f2a")
        for z in self.zombies:
            self.draw_zombie(z)
        for s in self.suns:
            self.draw_sun(s)
        for b in self.booms:
            rad = 30 + b["t"] * 260
            alpha = max(0, 1 - b["t"] * 2)
            for i, col in enumerate(("#fff3b0", "#ffb347", "#ff5c33")):
                cv.create_oval(b["x"] - rad + i * 18, b["y"] - rad + i * 18,
                               b["x"] + rad - i * 18, b["y"] + rad - i * 18,
                               outline=col, width=6)
        for f in self.floats:
            cv.create_text(f["x"], f["y"] - f["t"] * 34, text=f["txt"],
                           font=self.fonts(13, "bold"), fill="#ffe23a")
        # 横幅
        if self.banner:
            cv.create_rectangle(W / 2 - 190, 150, W / 2 + 190, 200, fill="#7a1010", outline="#ffb0b0", width=2)
            cv.create_text(W / 2, 175, text=self.banner[0], font=self.fonts(19, "bold"), fill="#ffdada")
        self.draw_progress()
        if self.state != "play":
            self.draw_over()

    def draw_top(self):
        cv = self.cv
        cv.create_rectangle(0, 0, W, 104, fill="#3a2618", outline="")
        cv.create_rectangle(0, 104, W, 108, fill="#241407", outline="")
        # 阳光数
        cv.create_oval(12, 14, 56, 58, fill="#ffd447", outline="#c9921b", width=3)
        cv.create_text(34, 36, text="☀", font=self.fonts(20, "bold"), fill="#b07d00")
        cv.create_text(78, 36, text=str(self.sun), font=self.fonts(20, "bold"),
                       fill="#ffe98a", anchor="w")
        # 卡片
        for i, k in enumerate(CARD_ORDER):
            x0 = CARD_X + i * CARD_W
            st = PLANTS[k]
            cool = self.cooldown[k] / st["cd"]
            cv.create_rectangle(x0, 8, x0 + CARD_W - 8, 8 + CARD_H,
                                fill="#cbb27a", outline="#5a3d1c", width=2)
            self.card_icon(k, x0 + (CARD_W - 8) / 2, 8 + CARD_H / 2 - 12)
            cv.create_text(x0 + (CARD_W - 8) / 2, 84, text=str(st["cost"]),
                           font=self.fonts(12, "bold"), fill="#4a2c08")
            if self.selected == k:
                cv.create_rectangle(x0, 8, x0 + CARD_W - 8, 8 + CARD_H,
                                    outline="#ffe23a", width=3)
            if cool > 0:
                cv.create_rectangle(x0, 8, x0 + CARD_W - 8, 8 + CARD_H * cool,
                                    fill="#000000", stipple="gray50", outline="")
            elif self.sun < st["cost"]:
                cv.create_rectangle(x0, 8, x0 + CARD_W - 8, 8 + CARD_H,
                                    fill="#888888", stipple="gray50", outline="")
        # 铲子
        SHOVEL_X = CARD_X + 4 * CARD_W + 6
        cv.create_rectangle(SHOVEL_X, 8, SHOVEL_X + 52, 8 + CARD_H,
                            fill="#8a6a3a" if self.shovel else "#cbb27a",
                            outline="#5a3d1c", width=2)
        cv.create_line(SHOVEL_X + 26, 22, SHOVEL_X + 26, 66, fill="#6b4a22", width=5)
        cv.create_polygon(SHOVEL_X + 12, 66, SHOVEL_X + 40, 66, SHOVEL_X + 26, 88,
                          fill="#b9c4cc", outline="#7a868e")
        cv.create_text(W - 14, 60, text="右键取消选择", font=self.fonts(11),
                       fill="#d8c9a8", anchor="e")

    def card_icon(self, k, cx, cy):
        cv = self.cv
        if k == "sunflower":
            for a in range(8):
                ang = a * math.pi / 4
                cv.create_oval(cx + math.cos(ang) * 13 - 6, cy + math.sin(ang) * 13 - 6,
                               cx + math.cos(ang) * 13 + 6, cy + math.sin(ang) * 13 + 6,
                               fill="#ffb400", outline="")
            cv.create_oval(cx - 9, cy - 9, cx + 9, cy + 9, fill="#ffd447", outline="#c9921b")
        elif k == "pea":
            cv.create_oval(cx - 13, cy - 13, cx + 9, cy + 9, fill="#3fae3f", outline="#256b25")
            cv.create_rectangle(cx + 5, cy - 7, cx + 20, cy + 2, fill="#3fae3f", outline="#256b25")
            cv.create_line(cx - 2, cy + 10, cx - 2, cy + 22, fill="#2f7d2f", width=3)
        elif k == "wallnut":
            cv.create_oval(cx - 12, cy - 16, cx + 12, cy + 16, fill="#a9743f", outline="#6e4520")
            cv.create_text(cx, cy + 2, text="●●", font=self.fonts(8), fill="#4a2c08")
        elif k == "cherry":
            cv.create_oval(cx - 14, cy - 2, cx + 0, cy + 12, fill="#e03a2f", outline="#8f1a12")
            cv.create_oval(cx + 2, cy - 2, cx + 16, cy + 12, fill="#ff5140", outline="#8f1a12")
            cv.create_line(cx + 1, cy - 4, cx + 7, cy - 14, fill="#2f7d2f", width=2)
            cv.create_line(cx + 9, cy - 4, cx + 7, cy - 14, fill="#2f7d2f", width=2)

    def draw_plant(self, r, c, p):
        cv = self.cv
        x = LAWN_X + c * CELL_W + CELL_W / 2
        y = LAWN_Y + r * CELL_H + CELL_H / 2
        t = self.t
        if p["type"] == "sunflower":
            sway = math.sin(t * 2 + c) * 2
            cv.create_line(x, y + 30, x + sway, y, fill="#2f7d2f", width=4)
            cx, cy = x + sway, y - 10
            for a in range(8):
                ang = a * math.pi / 4 + t * 0.4
                cv.create_oval(cx + math.cos(ang) * 16 - 7, cy + math.sin(ang) * 16 - 7,
                               cx + math.cos(ang) * 16 + 7, cy + math.sin(ang) * 16 + 7,
                               fill="#ffb400", outline="")
            cv.create_oval(cx - 11, cy - 11, cx + 11, cy + 11, fill="#ffd447", outline="#c9921b")
            cv.create_text(cx, cy, text="^ ^", font=self.fonts(9, "bold"), fill="#8a5f00")
        elif p["type"] == "pea":
            cv.create_line(x, y + 30, x, y + 4, fill="#2f7d2f", width=4)
            cv.create_oval(x - 15, y - 26, x + 9, y - 2, fill="#3fae3f", outline="#256b25")
            cv.create_rectangle(x + 5, y - 21, x + 24, y - 11, fill="#3fae3f", outline="#256b25")
            cv.create_oval(x + 20, y - 22, x + 26, y - 10, fill="#2f7d2f", outline="")
            cv.create_oval(x - 10, y - 22, x - 4, y - 16, fill="#fff", outline="")
            cv.create_oval(x - 9, y - 21, x - 5, y - 17, fill="#123", outline="")
            cv.create_line(x + 2, y + 4, x + 10, y + 14, fill="#2f7d2f", width=3)
        elif p["type"] == "wallnut":
            hp_ratio = p["hp"] / p["maxhp"]
            cv.create_oval(x - 20, y - 30, x + 20, y + 30, fill="#a9743f", outline="#6e4520", width=3)
            face = "＞ ＜" if hp_ratio < 0.4 else ("• ◡ •" if hp_ratio < 0.75 else "• •")
            cv.create_text(x, y, text=face, font=self.fonts(11, "bold"), fill="#4a2c08")
            if hp_ratio < 0.6:
                cv.create_line(x - 12, y - 24, x - 4, y - 8, x - 14, y + 6, fill="#6e4520", width=2)
        elif p["type"] == "cherry":
            pulse = 1 + (0.9 - p["fuse"]) * 0.5
            rr = 13 * pulse
            cv.create_oval(x - rr - 8, y - rr, x + 8 - rr + 16, y + rr, fill="#e03a2f", outline="#8f1a12")
            cv.create_oval(x + 2, y - rr - 4, x + 2 + rr * 2, y + rr - 4, fill="#ff5140", outline="#8f1a12")
            cv.create_text(x, y - 46, text="爆!", font=self.fonts(13, "bold"),
                           fill="#ff3020")
        # 血条
        if p["hp"] < p["maxhp"]:
            ratio = max(0, p["hp"] / p["maxhp"])
            cv.create_rectangle(x - 20, y + 34, x + 20, y + 39, fill="#333", outline="")
            cv.create_rectangle(x - 19, y + 35, x - 19 + 38 * ratio, y + 38,
                                fill="#5ce05c", outline="")

    def draw_zombie(self, z):
        cv = self.cv
        y = LAWN_Y + z["row"] * CELL_H + CELL_H / 2
        x = z["x"]
        step = math.sin(self.zomb_head * 7 + x * 0.1) * 3
        body = "#9aa8b8" if z["hit"] <= 0 else "#e0e6ec"
        # 腿
        cv.create_line(x - 6, y + 8, x - 10 + step, y + 30, fill="#5a6470", width=6)
        cv.create_line(x + 6, y + 8, x + 10 - step, y + 30, fill="#5a6470", width=6)
        # 身体
        cv.create_rectangle(x - 14, y - 12, x + 14, y + 12, fill=body, outline="#4a5560", width=2)
        # 前伸手臂
        cv.create_line(x + 8, y - 6, x + 30, y - 2 + step * 0.4, fill=body, width=6)
        # 头
        cv.create_oval(x - 12, y - 34, x + 12, y - 10, fill=body, outline="#4a5560", width=2)
        cv.create_oval(x + 2, y - 28, x + 8, y - 22, fill="#c33", outline="")  # 眼
        cv.create_oval(x - 8, y - 28, x - 2, y - 22, fill="#c33", outline="")
        cv.create_line(x - 6, y - 14, x + 8, y - 14, fill="#4a5560", width=2)  # 嘴
        if z["type"] == "cone":
            cv.create_polygon(x - 10, y - 34, x + 10, y - 34, x, y - 58, fill="#e07b1f", outline="#9c5310")
        elif z["type"] == "bucket":
            cv.create_rectangle(x - 11, y - 56, x + 11, y - 34, fill="#8d99a5", outline="#5a6470", width=2)
        ratio = max(0, z["hp"] / z["maxhp"])
        cv.create_rectangle(x - 16, y - 64, x + 16, y - 59, fill="#333", outline="")
        cv.create_rectangle(x - 15, y - 63, x - 15 + 30 * ratio, y - 60,
                            fill="#e05c5c" if ratio > 0.35 else "#ff2020", outline="")

    def draw_sun(self, s):
        cv = self.cv
        r = 16 + math.sin(self.t * 5 + s["x"]) * 2
        for i in range(8):
            a = i * math.pi / 4 + self.t
            cv.create_line(s["x"] + math.cos(a) * (r + 3), s["y"] + math.sin(a) * (r + 3),
                           s["x"] + math.cos(a) * (r + 9), s["y"] + math.sin(a) * (r + 9),
                           fill="#ffcf30", width=3)
        cv.create_oval(s["x"] - r, s["y"] - r, s["x"] + r, s["y"] + r,
                       fill="#ffe23a", outline="#e0a800", width=2)

    def draw_progress(self):
        cv = self.cv
        x0, y0, x1, y1 = W - 210, 122, W - 20, 140
        cv.create_rectangle(x0, y0, x1, y1, fill="#2c1c0e", outline="#8a6a3a", width=2)
        ratio = self.spawned / TOTAL_ZOMBIES
        cv.create_rectangle(x0 + 2, y0 + 2, x0 + 2 + (x1 - x0 - 4) * ratio, y1 - 2,
                            fill="#5cd45c", outline="")
        cv.create_text(x1 - (x1 - x0) / 2, (y0 + y1) / 2, text=f"进度 {int(ratio*100)}%",
                       font=self.fonts(11, "bold"), fill="#fff")
        cv.create_text(x0, y0 - 10, text=f"第 {self.wave_i}/{len(WAVE_PLAN)} 波",
                       font=self.fonts(12, "bold"), fill="#ffe9a8", anchor="w")

    def draw_over(self):
        cv = self.cv
        if self.state == "win":
            cv.create_rectangle(0, 0, W, H, fill="#0a3010", stipple="gray50", outline="")
            cv.create_text(W / 2, H / 2 - 60, text="胜  利  ！",
                           font=self.fonts(44, "bold"), fill="#ffe23a")
            cv.create_text(W / 2, H / 2 - 5, text="你守住了草坪，僵尸灰溜溜地走了。",
                           font=self.fonts(18), fill="#d0ffd0")
        else:
            cv.create_rectangle(0, 0, W, H, fill="#300a0a", stipple="gray50", outline="")
            cv.create_text(W / 2, H / 2 - 60, text="僵尸吃掉了你的脑子！",
                           font=self.fonts(40, "bold"), fill="#ff8080")
            cv.create_text(W / 2, H / 2 - 5, text="坚持了 %.0f 秒，消灭进度 %d%%" %
                           (self.t, 100 * self.spawned / TOTAL_ZOMBIES),
                           font=self.fonts(18), fill="#ffd0d0")
        x0, y0 = W / 2 - 120, H / 2 + 30
        self.restart_rect = (x0, y0)
        cv.create_rectangle(x0, y0, x0 + 240, y0 + 56, fill="#1b6fae", outline="#9fd8ff", width=2)
        cv.create_text(W / 2, y0 + 28, text="再 来 一 局", font=self.fonts(22, "bold"), fill="#fff")


def main():
    root = tk.Tk()
    root.title("植物大战僵尸 · Python 版")
    root.resizable(False, False)
    Game(root)
    root.mainloop()


if __name__ == "__main__":
    main()
