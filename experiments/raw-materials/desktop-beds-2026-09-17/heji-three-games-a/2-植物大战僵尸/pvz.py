# -*- coding: utf-8 -*-
"""
植物大战僵尸 · tkinter 简化版
运行方式：双击同目录"启动游戏.bat"，或 python pvz.py
玩法：阳光经济 + 种植物防御 8 波僵尸
  向日葵 50 阳光 —— 定期产出阳光
  豌豆射手 100 阳光 —— 同行有僵尸时发射豌豆
  坚果墙 50 阳光 —— 高血量肉盾
  铲子 —— 移除植物（免费）
僵尸到达最左侧房屋则失败；守住全部 8 波获胜。
"""
import math
import random
import tkinter as tk

# ---------------- 常量 ----------------
W, H = 1000, 640
COLS, ROWS = 9, 5
CELL_W, CELL_H = 92, 96
X0, Y0 = 130, 100              # 草坪左上角
BOARD_R = X0 + COLS * CELL_W   # 草坪右缘

SUN_NATURAL_EVERY = 7.0        # 天降阳光间隔（秒）
WAVE_TOTAL = 8

CARD_INFO = [
    # key, 名称, 价格, 冷却(秒)
    ("sunflower", "向日葵", 50, 6.0),
    ("pea",       "豌豆射手", 100, 6.0),
    ("wallnut",   "坚果墙", 50, 14.0),
]

PLANT_HP = {"sunflower": 60, "pea": 120, "wallnut": 400}
ZOMBIE_BASE_HP = 100
ZOMBIE_CONE_HP = 200
ZOMBIE_SPEED = 17.0            # 像素/秒
ZOMBIE_BITE_DPS = 28
PEA_DAMAGE = 20
PEA_SPEED = 260.0
PEA_INTERVAL = 1.4
SUN_VALUE = 25


class Game:
    def __init__(self, root):
        self.root = root
        root.title("植物大战僵尸 · 简化版")
        root.resizable(False, False)
        self.cv = tk.Canvas(root, width=W, height=H, bg="#0d2b17",
                            highlightthickness=0)
        self.cv.pack()
        self.cv.bind("<Button-1>", self.on_click)
        self.cv.bind("<Motion>", self.on_move)

        self.reset()
        self.last = self.now()
        self.loop()
        self.center_window()

    # ---------- 工具 ----------
    @staticmethod
    def now():
        import time
        return time.perf_counter()

    def center_window(self):
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw - W) // 2}+{max(20, (sh - H) // 2 - 30)}")

    def reset(self):
        self.sun = 150
        self.plants = {}          # (row, col) -> plant dict
        self.zombies = []
        self.bullets = []
        self.suns = []            # 掉落的阳光
        self.particles = []
        self.card_cd = {k: 0.0 for k, *_ in CARD_INFO}
        self.selected = None      # 待种植物 key
        self.shovel = False
        self.sun_timer = 3.0
        self.wave = 0
        self.wave_timer = 12.0    # 首波倒计时
        self.spawn_queue = []     # 待出场僵尸 (delay, kind, row)
        self.state = "play"       # play / win / lose
        self.msg = ""
        self.mouse = (-99, -99)
        self.kills = 0

    # ---------- 坐标换算 ----------
    def cell_at(self, x, y):
        c = (x - X0) // CELL_W
        r = (y - Y0) // CELL_H
        if 0 <= c < COLS and 0 <= r < ROWS:
            return int(r), int(c)
        return None

    def cell_center(self, r, c):
        return (X0 + c * CELL_W + CELL_W / 2,
                Y0 + r * CELL_H + CELL_H / 2)

    # ---------- 输入 ----------
    def card_rects(self):
        rects = []
        x = 20
        for key, name, price, cd in CARD_INFO:
            rects.append((key, x, 12, x + 92, 78))
            x += 100
        rects.append(("shovel", x, 12, x + 70, 78))
        return rects

    def on_move(self, e):
        self.mouse = (e.x, e.y)

    def on_click(self, e):
        if self.state != "play":
            self.reset()
            return
        x, y = e.x, e.y
        # 1) 点卡片
        for key, rx0, ry0, rx1, ry1 in self.card_rects():
            if rx0 <= x <= rx1 and ry0 <= y <= ry1:
                if key == "shovel":
                    self.shovel = not self.shovel
                    self.selected = None
                else:
                    info = next(i for i in CARD_INFO if i[0] == key)
                    if self.sun >= info[2] and self.card_cd[key] <= 0:
                        self.selected = None if self.selected == key else key
                        self.shovel = False
                return
        # 2) 点阳光收集
        for s in self.suns[:]:
            if (s["x"] - x) ** 2 + (s["y"] - y) ** 2 < 26 ** 2:
                self.sun += s["val"]
                self.suns.remove(s)
                self.pop_text(x, y, f"+{s['val']}", "#ffe14a")
                return
        # 3) 草坪操作
        cell = self.cell_at(x, y)
        if not cell:
            self.selected = None
            self.shovel = False
            return
        r, c = cell
        if self.shovel:
            if (r, c) in self.plants:
                del self.plants[(r, c)]
                self.shovel = False
            return
        if self.selected:
            price = next(i[2] for i in CARD_INFO if i[0] == self.selected)
            if (r, c) not in self.plants and self.sun >= price \
                    and self.card_cd[self.selected] <= 0:
                self.plant(r, c, self.selected)
                self.sun -= price
                self.card_cd[self.selected] = next(
                    i[3] for i in CARD_INFO if i[0] == self.selected)
                self.selected = None
            elif (r, c) in self.plants:
                self.pop_text(x, y, "这里已有植物", "#ff9a7a")

    # ---------- 实体 ----------
    def plant(self, r, c, key):
        x, y = self.cell_center(r, c)
        self.plants[(r, c)] = {
            "key": key, "hp": PLANT_HP[key], "max_hp": PLANT_HP[key],
            "r": r, "c": c, "x": x, "y": y,
            "timer": 0.0, "born": self.now(),
        }

    def spawn_zombie(self, kind, row):
        x = BOARD_R + 40 + random.random() * 60
        y = Y0 + row * CELL_H + CELL_H / 2
        hp = ZOMBIE_CONE_HP if kind == "cone" else ZOMBIE_BASE_HP
        self.zombies.append({
            "x": x, "y": y, "row": row, "hp": hp, "max_hp": hp,
            "kind": kind, "eating": None, "ph": random.random() * 6,
        })

    def schedule_wave(self):
        """生成一波僵尸的出场队列"""
        self.wave += 1
        n = 1 + self.wave // 2 + (4 if self.wave == WAVE_TOTAL else 0)
        cone_p = min(0.45, 0.08 * self.wave)
        for _ in range(n):
            kind = "cone" if random.random() < cone_p else "normal"
            delay = random.uniform(1.0, 6.0) if self.wave < WAVE_TOTAL \
                else random.uniform(0.8, 7.0)
            self.spawn_queue.append([delay, kind, random.randrange(ROWS)])
        self.pop_text(W // 2, H // 2 - 60,
                      f"第 {self.wave} 波来袭！", "#ff7a6a")

    # ---------- 特效 ----------
    def pop_text(self, x, y, text, color):
        self.particles.append({"type": "text", "x": x, "y": y,
                               "text": text, "color": color, "life": 1.1})

    # ---------- 主逻辑 ----------
    def update(self, dt):
        if self.state != "play":
            return

        # 天降阳光
        self.sun_timer -= dt
        if self.sun_timer <= 0:
            self.sun_timer = SUN_NATURAL_EVERY
            self.suns.append({"x": random.uniform(X0 + 40, BOARD_R - 40),
                              "y": Y0 - 30, "ty": random.uniform(
                                  Y0 + 60, Y0 + ROWS * CELL_H - 60),
                              "val": SUN_VALUE, "life": 12.0})

        for s in self.suns:
            if s["y"] < s["ty"]:
                s["y"] = min(s["ty"], s["y"] + 45 * dt)
            else:
                s["life"] -= dt
        self.suns = [s for s in self.suns if s["life"] > 0]

        # 卡片冷却
        for k in self.card_cd:
            self.card_cd[k] = max(0.0, self.card_cd[k] - dt)

        # 波次调度
        if not self.spawn_queue and not self.zombies:
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                if self.wave >= WAVE_TOTAL:
                    self.state = "win"
                    return
                self.schedule_wave()
                self.wave_timer = 20.0 if self.wave < WAVE_TOTAL else 0
        else:
            for q in self.spawn_queue:
                q[0] -= dt
            ready = [q for q in self.spawn_queue if q[0] <= 0]
            for q in ready:
                self.spawn_zombie(q[1], q[2])
                self.spawn_queue.remove(q)

        # 植物
        for key in list(self.plants):
            p = self.plants[key]
            if p["key"] == "sunflower":
                p["timer"] += dt
                if p["timer"] >= 9.0:
                    p["timer"] = 0
                    self.suns.append({"x": p["x"] + random.uniform(-16, 16),
                                      "y": p["y"], "ty": p["y"] + 14,
                                      "val": SUN_VALUE, "life": 12.0})
            elif p["key"] == "pea":
                row_has_zombie = any(z["row"] == p["r"] and z["x"] > p["x"]
                                     for z in self.zombies)
                p["timer"] += dt
                if row_has_zombie and p["timer"] >= PEA_INTERVAL:
                    p["timer"] = 0
                    self.bullets.append({"x": p["x"] + 26, "y": p["y"] - 8})

        # 子弹
        for b in self.bullets[:]:
            b["x"] += PEA_SPEED * dt
            hit = None
            # 找同行碰撞
            for z in self.zombies:
                zy = Y0 + z["row"] * CELL_H + CELL_H / 2
                if abs((b["y"] + 8) - zy) < CELL_H * 0.55 and \
                        abs(b["x"] - z["x"]) < 24:
                    hit = z
                    break
            if hit:
                hit["hp"] -= PEA_DAMAGE
                self.pop_text(hit["x"], hit["y"] - 34, "-20", "#9aff6a")
                self.bullets.remove(b)
            elif b["x"] > W + 20:
                self.bullets.remove(b)

        # 僵尸
        for z in self.zombies[:]:
            row_c = int((z["x"] - X0) // CELL_W)
            target = self.plants.get((z["row"], row_c)) \
                if 0 <= row_c < COLS else None
            if target and z["x"] - target["x"] < 34:
                z["eating"] = target
                target["hp"] -= ZOMBIE_BITE_DPS * dt
                if random.random() < dt * 6:
                    self.pop_text(target["x"], target["y"] - 26,
                                  "咔嚓", "#ffd08a")
                if target["hp"] <= 0:
                    self.plants.pop((target["r"], target["c"]), None)
                    z["eating"] = None
            else:
                z["eating"] = None
                z["x"] -= ZOMBIE_SPEED * dt
            if z["x"] < X0 - 46:
                self.state = "lose"
                return
            if z["hp"] <= 0:
                self.kills += 1
                self.pop_text(z["x"], z["y"] - 30, "倒下了!", "#cfcfcf")
                self.zombies.remove(z)

        # 粒子
        for p in self.particles[:]:
            p["life"] -= dt
            if p["type"] == "text":
                p["y"] -= 26 * dt
            if p["life"] <= 0:
                self.particles.remove(p)

    # ---------- 绘制 ----------
    def draw_board(self):
        # 背景天空与草地
        self.cv.create_rectangle(0, 0, W, Y0 - 14, fill="#123a22", outline="")
        for r in range(ROWS):
            for c in range(COLS):
                x0 = X0 + c * CELL_W
                y0 = Y0 + r * CELL_H
                color = "#4f9e3c" if (r + c) % 2 == 0 else "#458f34"
                self.cv.create_rectangle(x0, y0, x0 + CELL_W, y0 + CELL_H,
                                         fill=color, outline="#38682c")
        # 左侧房屋
        self.cv.create_rectangle(0, Y0 - 14, X0 - 6, H, fill="#6b4a2c",
                                 outline="")
        self.cv.create_rectangle(18, Y0 + 60, X0 - 20, H - 60,
                                 fill="#8a6238", outline="#5d3f24",
                                 width=3)
        self.cv.create_text((X0 - 2) // 2 + 8, Y0 + 30, text="🏠",
                            font=("Segoe UI Emoji", 26))
        # 鼠标悬停格
        r_c = self.cell_at(*self.mouse)
        if r_c and (self.selected or self.shovel):
            r, c = r_c
            x0 = X0 + c * CELL_W
            y0 = Y0 + r * CELL_H
            color = "#ffe14a" if self.selected else "#ff8a5a"
            self.cv.create_rectangle(x0 + 2, y0 + 2, x0 + CELL_W - 2,
                                     y0 + CELL_H - 2, outline=color,
                                     width=3)

    def draw_card_bar(self):
        self.cv.create_rectangle(0, 0, W, 84, fill="#28401f", outline="")
        self.cv.create_text(30, 40, text=str(self.sun),
                            font=("Arial", 20, "bold"), fill="#ffe14a")
        self.cv.create_oval(8, 24, 26, 42, fill="#ffe14a", outline="#c9a500")
        for key, name, price, cd in CARD_INFO:
            for k, x0, y0, x1, y1 in self.card_rects():
                if k == key:
                    break
            afford = self.sun >= price and self.card_cd[key] <= 0
            fill = "#e8f5d0" if afford else "#9aa894"
            if self.selected == key:
                fill = "#fff2a8"
            self.cv.create_rectangle(x0, y0, x1, y1, fill=fill,
                                     outline="#5d3f24", width=2)
            self._draw_plant_icon((x0 + x1) / 2, (y0 + y1) / 2 - 6, key, 0.55)
            self.cv.create_text((x0 + x1) / 2, y1 - 22, text=str(price),
                                font=("Arial", 11, "bold"),
                                fill="#7a4a00" if afford else "#555")
            if self.card_cd[key] > 0:
                frac = self.card_cd[key] / next(
                    i[3] for i in CARD_INFO if i[0] == key)
                self.cv.create_rectangle(
                    x0, y1 - (y1 - y0) * min(1, frac), x1, y1,
                    fill="#000", stipple="gray50", outline="")
        for k, x0, y0, x1, y1 in self.card_rects():
            if k == "shovel":
                fill = "#ffe0b0" if self.shovel else "#d9c9a8"
                self.cv.create_rectangle(x0, y0, x1, y1, fill=fill,
                                         outline="#5d3f24", width=2)
                self.cv.create_text((x0 + x1) / 2, (y0 + y1) / 2,
                                    text="铲子", font=("微软雅黑", 12, "bold"),
                                    fill="#5d3f24")

    def _draw_plant_icon(self, x, y, key, scale=1.0, hp_frac=1.0):
        if key == "sunflower":
            for i in range(8):
                a = i * math.pi / 4
                px, py = x + 13 * scale * math.cos(a), \
                    y + 13 * scale * math.sin(a)
                self.cv.create_oval(px - 5 * scale, py - 5 * scale,
                                    px + 5 * scale, py + 5 * scale,
                                    fill="#ffcf33", outline="#e0a800")
            self.cv.create_oval(x - 8 * scale, y - 8 * scale,
                                x + 8 * scale, y + 8 * scale,
                                fill="#8a5a2b", outline="#6d441f")
        elif key == "pea":
            self.cv.create_oval(x - 13 * scale, y - 14 * scale,
                                x + 15 * scale, y + 12 * scale,
                                fill="#4caf50", outline="#2e7d32")
            self.cv.create_oval(x - 2 * scale, y - 8 * scale,
                                x + 4 * scale, y - 2 * scale, fill="#123")
            self.cv.create_oval(x + 2 * scale, y - 9 * scale,
                                x + 8 * scale, y - 3 * scale, fill="#fff")
            self.cv.create_line(x - 12 * scale, y + 8 * scale,
                                x - 18 * scale, y + 14 * scale,
                                fill="#2e7d32", width=2)
        elif key == "wallnut":
            self.cv.create_oval(x - 14 * scale, y - 16 * scale,
                                x + 14 * scale, y + 16 * scale,
                                fill="#b98449", outline="#8a5a2b",
                                width=2 * scale)
            self.cv.create_oval(x - 6 * scale, y - 7 * scale,
                                x - 1 * scale, y - 1 * scale, fill="#4a2f14")
            self.cv.create_oval(x + 2 * scale, y - 7 * scale,
                                x + 7 * scale, y - 1 * scale, fill="#4a2f14")
            self.cv.create_arc(x - 5 * scale, y + 1 * scale,
                               x + 6 * scale, y + 9 * scale, start=200,
                               extent=140, style="arc",
                               outline="#4a2f14", width=2)

    def draw_plants(self):
        for p in self.plants.values():
            sway = math.sin((self.now() - p["born"]) * 2.5) * 2
            self._draw_plant_icon(p["x"] + sway, p["y"], p["key"])
            if p["hp"] < p["max_hp"]:
                frac = p["hp"] / p["max_hp"]
                w = 44
                self.cv.create_rectangle(p["x"] - w / 2, p["y"] - 30,
                                         p["x"] + w / 2, p["y"] - 25,
                                         fill="#333", outline="")
                self.cv.create_rectangle(p["x"] - w / 2, p["y"] - 30,
                                         p["x"] - w / 2 + w * frac,
                                         p["y"] - 25,
                                         fill="#7fe05a", outline="")

    def draw_zombies(self):
        for z in self.zombies:
            x, y = z["x"], z["y"]
            ph = self.now() * 4 + z["ph"]
            step = math.sin(ph) * 3 if not z["eating"] else 0
            # 身体
            self.cv.create_oval(x - 14, y - 40 + step * 0.3, x + 12,
                                y + 14, fill="#7a9e6b", outline="#4e6b43")
            # 头
            self.cv.create_oval(x - 12, y - 62, x + 14, y - 34,
                                fill="#a8c98f", outline="#4e6b43")
            self.cv.create_oval(x - 4, y - 54, x + 2, y - 48, fill="#333")
            self.cv.create_oval(x + 4, y - 54, x + 10, y - 48, fill="#333")
            self.cv.create_line(x - 6, y - 38, x + 10, y - 40,
                                fill="#5d3f24", width=2)
            # 手臂前伸
            self.cv.create_line(x - 8, y - 26 + step * 0.5, x - 30,
                                y - 30 - step * 0.5, fill="#7a9e6b",
                                width=7, capstyle="round")
            # 腿
            self.cv.create_line(x - 6, y + 12, x - 10 - step, y + 30,
                                fill="#4e6b43", width=6, capstyle="round")
            self.cv.create_line(x + 6, y + 12, x + 10 + step, y + 30,
                                fill="#4e6b43", width=6, capstyle="round")
            # 路障帽
            if z["kind"] == "cone":
                self.cv.create_polygon(x - 12, y - 60, x + 14, y - 60,
                                       x + 2, y - 86, fill="#ff8c1a",
                                       outline="#c96a00")
            # 血条
            frac = z["hp"] / z["max_hp"]
            self.cv.create_rectangle(x - 18, y - 72, x + 18, y - 67,
                                     fill="#333", outline="")
            self.cv.create_rectangle(x - 18, y - 72, x - 18 + 36 * frac,
                                     y - 67, fill="#ff5a4a", outline="")

    def draw_bullets_suns(self):
        for b in self.bullets:
            self.cv.create_oval(b["x"] - 7, b["y"] - 7, b["x"] + 7,
                                b["y"] + 7, fill="#6fe04a",
                                outline="#3f9e2a")
        for s in self.suns:
            glow = 1 + 0.08 * math.sin(self.now() * 5)
            r = 14 * glow
            self.cv.create_oval(s["x"] - r, s["y"] - r, s["x"] + r,
                                s["y"] + r, fill="#ffe14a",
                                outline="#e8b400", width=2)
            self.cv.create_oval(s["x"] - r * 0.45, s["y"] - r * 0.45,
                                s["x"] + r * 0.45, s["y"] + r * 0.45,
                                fill="#fff59a", outline="")

    def draw_particles(self):
        for p in self.particles:
            self.cv.create_text(p["x"], p["y"], text=p["text"],
                                fill=p["color"],
                                font=("微软雅黑", 11, "bold"))

    def draw_wave_info(self):
        self.cv.create_text(W - 150, 40, text=f"第 {self.wave}/{WAVE_TOTAL} 波",
                            font=("微软雅黑", 16, "bold"), fill="#eaffe0")
        self.cv.create_text(W - 150, 66, text=f"消灭僵尸 {self.kills}",
                            font=("微软雅黑", 11), fill="#a8d8a0")
        if not self.spawn_queue and not self.zombies and self.wave < WAVE_TOTAL:
            self.cv.create_text(W // 2, 46,
                                text=f"下一波 {max(0, int(self.wave_timer))} 秒",
                                font=("微软雅黑", 13), fill="#ffe14a")
        if self.selected:
            self.cv.create_text(W // 2, 96, text="点击草地种下 ↓",
                                font=("微软雅黑", 12), fill="#fff2a8")
        elif self.shovel:
            self.cv.create_text(W // 2, 96, text="点击植物移除（再点铲子取消）",
                                font=("微软雅黑", 12), fill="#ffc0a0")

    def draw_end(self):
        if self.state == "play":
            return
        self.cv.create_rectangle(0, 0, W, H, fill="#000", stipple="gray50")
        if self.state == "win":
            text, color = "🏆 胜利！守住了一整个花园！", "#ffe14a"
        else:
            text, color = "🧟 僵尸吃掉了你的脑子…", "#ff7a6a"
        self.cv.create_text(W // 2, H // 2 - 40, text=text,
                            font=("微软雅黑", 30, "bold"), fill=color)
        self.cv.create_text(W // 2, H // 2 + 10, text="点击任意位置重新开始",
                            font=("微软雅黑", 15), fill="#e0e0e0")

    def render(self):
        self.cv.delete("all")
        self.draw_board()
        self.draw_plants()
        self.draw_zombies()
        self.draw_bullets_suns()
        self.draw_card_bar()
        self.draw_wave_info()
        self.draw_particles()
        self.draw_end()

    def loop(self):
        now = self.now()
        dt = min(0.05, now - self.last)
        self.last = now
        self.update(dt)
        self.render()
        self.root.after(33, self.loop)


def main():
    root = tk.Tk()
    Game(root)
    root.mainloop()


if __name__ == "__main__":
    main()
