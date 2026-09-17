// -*- coding: utf-8 -*-
// 保卫萝卜 · Swing 简化版（单文件）
// 编译: javac -encoding UTF-8 CarrotDefense.java
// 运行: java CarrotDefense   （或双击同目录 启动游戏.bat / 保卫萝卜.exe）
//
// 玩法：怪物沿 S 形路径进攻终点的萝卜。
//   1. 点击草地空位 -> 选择建塔（箭塔 100 / 冰塔 150）
//   2. 点击已建的塔 -> 升级（伤害翻倍）或卖出（半价返还）
//   3. 冰塔会减速周围怪物；击杀怪物得金币
//   4. 萝卜 10 点血，怪物到终点扣 1；守住 10 波获胜。P 键暂停。

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Random;

public class CarrotDefense extends JPanel {

    // ---------------- 常量 ----------------
    static final int W = 1000, H = 640;
    static final int GRID = 50;
    static final int COLS = W / GRID, ROWS = 560 / GRID;   // 底部 80px 状态栏
    static final double DT = 0.03;

    // 路径折点（像素，S 形）
    static final int[][] WAYPOINTS = {
            {-30, 125}, {775, 125}, {775, 275}, {225, 275}, {225, 475}, {925, 475}
    };
    static final int[] CARROT = {925, 475};

    static final int TOWER_ARROW_COST = 100, TOWER_ICE_COST = 150;
    static final int UPGRADE_BASE = 150;
    static final int CARROT_HP = 10;
    static final int WAVE_TOTAL = 10;

    // ---------------- 内部实体 ----------------
    static class Monster {
        double dist;        // 沿路径已走距离
        int kind;           // 0普通 1快速 2胖子
        int hp, maxHp;
        double speed;
        boolean dead = false;
        double slowT = 0;   // 剩余减速时间

        Monster(int kind, int hp, double speed, double startDist) {
            this.kind = kind; this.hp = hp; this.maxHp = hp;
            this.speed = speed; this.dist = startDist;
        }
        int bounty() { return kind == 0 ? 15 : kind == 1 ? 12 : 30; }
        double r() { return kind == 2 ? 17 : 13; }
    }

    static class Tower {
        int x, y, kind, level = 1;   // kind: 0箭塔 1冰塔
        double cd = 0, angle = -Math.PI / 2;

        Tower(int x, int y, int kind) { this.x = x; this.y = y; this.kind = kind; }
        double range() { return kind == 0 ? 135 : 115; }
        double damage() { return (kind == 0 ? 22 : 8) * level; }
        double rate() { return kind == 0 ? 0.8 : 1.1; }
        int upgradeCost() { return UPGRADE_BASE * level; }
        int sellValue() { return (kind == 0 ? TOWER_ARROW_COST : TOWER_ICE_COST) / 2
                + (level > 1 ? UPGRADE_BASE * (level - 1) / 2 : 0); }
    }

    static class Bullet {
        double x, y, tx, ty, speed = 420, dmg;
        Tower from;
        Monster target;
        boolean ice;
        Bullet(double x, double y, Tower from, Monster t) {
            this.x = x; this.y = y; this.from = from; this.target = t;
            this.dmg = from.damage(); this.ice = from.kind == 1;
        }
    }

    static class Particle {
        double x, y, vx, vy, life;
        Color c;
        Particle(double x, double y, Color c) {
            this.x = x; this.y = y; this.c = c;
            this.vx = (Math.random() - 0.5) * 120;
            this.vy = (Math.random() - 0.5) * 120 - 40;
            this.life = 0.5 + Math.random() * 0.3;
        }
    }

    // 面板按钮（绘制与命中都用）
    static class Btn {
        int x, y, w, h; String label; Runnable action; boolean enabled = true;
        Btn(int x, int y, int w, int h, String l, Runnable a) {
            this.x = x; this.y = y; this.w = w; this.h = h; this.label = l; this.action = a;
        }
        boolean hit(int px, int py) {
            return px >= x && px <= x + w && py >= y && py <= y + h;
        }
    }

    // ---------------- 游戏状态 ----------------
    final List<Monster> monsters = new ArrayList<>();
    final List<Tower> towers = new ArrayList<>();
    final List<Bullet> bullets = new ArrayList<>();
    final List<Particle> particles = new ArrayList<>();
    final List<double[]> pathCache = new ArrayList<>();  // 预采样路径点，用于放塔判定

    int money = 260, carrotHp = CARROT_HP, wave = 0, kills = 0;
    double waveTimer = 6.0;          // 首波倒计时
    List<int[]> spawnQueue = new ArrayList<>();   // {剩余延迟, kind, 血量系数x100, 速度x100}
    double spawnGap = 0;
    String state = "play";           // play / win / lose
    boolean paused = false;
    Random rnd = new Random();

    Tower selectedTower = null;      // 升级面板目标
    Tower buildSpot = null;          // 建塔面板位置(虚拟塔存坐标)
    List<Btn> panelBtns = new ArrayList<>();
    String toast = ""; double toastT = 0;

    public CarrotDefense() {
        setPreferredSize(new Dimension(W, H));
        setFocusable(true);
        // 预采样路径：每 5px 一个点，用于距离判定
        double total = pathLength();
        for (double d = 0; d <= total; d += 5) pathCache.add(pointAt(d));

        addMouseListener(new MouseAdapter() {
            public void mousePressed(MouseEvent e) {
                if (e.getButton() == MouseEvent.BUTTON3) { closePanels(); return; }
                handleClick(e.getX(), e.getY());
            }
        });
        addKeyListener(new KeyAdapter() {
            public void keyPressed(KeyEvent e) {
                if (e.getKeyCode() == KeyEvent.VK_P) paused = !paused;
            }
        });
    }

    void closePanels() { panelBtns.clear(); selectedTower = null; buildSpot = null; }

    void toast(String s) { toast = s; toastT = 2.2; }

    // ---------------- 路径工具 ----------------
    static double segLen(int[] a, int[] b) {
        return Math.hypot(b[0] - a[0], b[1] - a[1]);
    }
    static double pathLength() {
        double s = 0;
        for (int i = 0; i < WAYPOINTS.length - 1; i++)
            s += segLen(WAYPOINTS[i], WAYPOINTS[i + 1]);
        return s;
    }
    static double[] pointAt(double d) {
        double total = pathLength();
        d = Math.max(0, Math.min(total, d));
        for (int i = 0; i < WAYPOINTS.length - 1; i++) {
            double L = segLen(WAYPOINTS[i], WAYPOINTS[i + 1]);
            if (d <= L) {
                double t = L == 0 ? 0 : d / L;
                return new double[]{
                        WAYPOINTS[i][0] + (WAYPOINTS[i + 1][0] - WAYPOINTS[i][0]) * t,
                        WAYPOINTS[i][1] + (WAYPOINTS[i + 1][1] - WAYPOINTS[i][1]) * t};
            }
            d -= L;
        }
        int[] last = WAYPOINTS[WAYPOINTS.length - 1];
        return new double[]{last[0], last[1]};
    }
    double distToPath(int x, int y) {
        double best = 1e9;
        for (double[] p : pathCache) {
            double dd = Math.hypot(p[0] - x, p[1] - y);
            if (dd < best) best = dd;
        }
        return best;
    }
    Tower towerAt(int x, int y) {
        for (Tower t : towers)
            if (Math.hypot(t.x - x, t.y - y) < 24) return t;
        return null;
    }
    boolean buildable(int x, int y) {
        if (x < GRID / 2 || x > W - GRID / 2 || y < GRID / 2 || y > ROWS * GRID - GRID / 2)
            return false;
        if (Math.hypot(x - CARROT[0], y - CARROT[1]) < 46) return false;
        if (distToPath(x, y) < 42) return false;
        return towerAt(x, y) == null;
    }

    // ---------------- 交互 ----------------
    void handleClick(int x, int y) {
        if (!state.equals("play")) { reset(); return; }
        // 面板按钮优先
        for (Btn b : panelBtns)
            if (b.hit(x, y)) { if (b.enabled) b.action.run(); return; }

        Tower t = towerAt(x, y);
        if (t != null) { openTowerPanel(t); return; }
        if (buildable(x, y)) { openBuildPanel(x, y); return; }
        if (distToPath(x, y) <= 42) toast("离路太近，不能建塔");
        closePanels();
    }

    void openBuildPanel(int x, int y) {
        closePanels();
        buildSpot = new Tower(x, y, 0);
        panelBtns.add(new Btn(x - 60, y - 76, 118, 30, "箭塔 ¥" + TOWER_ARROW_COST, () -> {
            if (money >= TOWER_ARROW_COST) {
                money -= TOWER_ARROW_COST;
                towers.add(new Tower(x, y, 0));
                beepPlace(); closePanels();
            } else toast("金币不足");
        }));
        panelBtns.add(new Btn(x - 60, y - 40, 118, 30, "冰塔 ¥" + TOWER_ICE_COST, () -> {
            if (money >= TOWER_ICE_COST) {
                money -= TOWER_ICE_COST;
                towers.add(new Tower(x, y, 1));
                beepPlace(); closePanels();
            } else toast("金币不足");
        }));
    }

    void openTowerPanel(Tower t) {
        closePanels();
        selectedTower = t;
        final Tower ft = t;
        if (t.level < 3)
            panelBtns.add(new Btn(t.x - 60, t.y - 76, 118, 30,
                    "升级 ¥" + t.upgradeCost(), () -> {
                if (money >= ft.upgradeCost()) {
                    money -= ft.upgradeCost(); ft.level++;
                    beepPlace(); closePanels();
                } else toast("金币不足");
            }));
        panelBtns.add(new Btn(t.x - 60, t.y - 40, 118, 30,
                "卖出 ¥" + t.sellValue(), () -> {
            money += ft.sellValue();
            towers.remove(ft); closePanels();
        }));
    }

    // ---------------- 波次 ----------------
    void scheduleWave() {
        wave++;
        int n = 4 + wave + (wave == WAVE_TOTAL ? 3 : 0);
        spawnQueue.clear();
        for (int i = 0; i < n; i++) {
            double roll = rnd.nextDouble();
            int kind = wave >= 3 && roll < 0.25 ? 1 : (wave >= 5 && roll > 0.78 ? 2 : 0);
            int hp = kind == 0 ? 55 + wave * 14 : kind == 1 ? 30 + wave * 8 : 130 + wave * 22;
            int spd = (int) ((kind == 1 ? 62 : kind == 2 ? 30 : 44) * 100);
            spawnQueue.add(new int[]{(int) (i * 1.3 * 100), kind, hp, spd});
        }
        spawnGap = 0;
        toast("第 " + wave + " 波来袭！");
    }

    void reset() {
        monsters.clear(); towers.clear(); bullets.clear();
        particles.clear(); spawnQueue.clear(); panelBtns.clear();
        money = 260; carrotHp = CARROT_HP; wave = 0; kills = 0;
        waveTimer = 6.0; state = "play"; paused = false;
        selectedTower = null; buildSpot = null;
    }

    // ---------------- 音效（仅系统提示音，避免依赖） ----------------
    void beepPlace() { Toolkit.getDefaultToolkit().beep(); }

    // ---------------- 主更新 ----------------
    void update() {
        if (!state.equals("play") || paused) return;
        double dt = DT;

        toastT -= dt;
        if (toastT < 0) toast = "";

        // 波次调度
        if (spawnQueue.isEmpty() && monsters.isEmpty()) {
            waveTimer -= dt;
            if (waveTimer <= 0) {
                if (wave >= WAVE_TOTAL) { state = "win"; return; }
                scheduleWave();
                waveTimer = 9.0;
            }
        } else {
            // 逐个出怪
            if (!spawnQueue.isEmpty()) {
                spawnQueue.get(0)[0] -= (int) (dt * 100);
                if (spawnQueue.get(0)[0] <= 0) {
                    int[] q = spawnQueue.remove(0);
                    monsters.add(new Monster(q[1], q[2], q[3] / 100.0, 0));
                }
            }
        }

        // 怪物移动
        double total = pathLength();
        Iterator<Monster> mit = monsters.iterator();
        while (mit.hasNext()) {
            Monster m = mit.next();
            if (m.dead) { mit.remove(); continue; }   // 统一清理被击杀的怪
            if (m.slowT > 0) { m.slowT -= dt; }
            double sp = m.speed * (m.slowT > 0 ? 0.55 : 1.0);
            m.dist += sp * dt;
            if (m.dist >= total) {
                mit.remove();
                carrotHp--;
                toast("萝卜被咬了一口！");
                if (carrotHp <= 0) { state = "lose"; return; }
            }
        }

        // 塔攻击
        for (Tower t : towers) {
            t.cd -= dt;
            if (t.kind == 0) {
                // 箭塔：找射程内血最少的怪
                Monster best = null;
                for (Monster m : monsters) {
                    if (m.dead) continue;
                    double[] p = pointAt(m.dist);
                    if (Math.hypot(p[0] - t.x, p[1] - t.y) <= t.range())
                        if (best == null || m.hp < best.hp) best = m;
                }
                if (best != null) {
                    double[] p = pointAt(best.dist);
                    t.angle = Math.atan2(p[1] - t.y, p[0] - t.x);
                    if (t.cd <= 0) {
                        t.cd = t.rate();
                        bullets.add(new Bullet(t.x, t.y - 10, t, best));
                    }
                }
            } else {
                // 冰塔：范围光环
                if (t.cd <= 0) {
                    boolean any = false;
                    for (Monster m : monsters) {
                        double[] p = pointAt(m.dist);
                        if (Math.hypot(p[0] - t.x, p[1] - t.y) <= t.range()) {
                            m.slowT = 1.0; m.hp -= (int) t.damage(); any = true;
                            if (m.hp <= 0) kill(m);   // kill 只标记，不在迭代中移除
                        }
                    }
                    t.cd = t.rate();
                    if (any) particles.add(new Particle(t.x, t.y - 14, new Color(140, 220, 255)));
                }
            }
        }

        // 子弹
        Iterator<Bullet> bit = bullets.iterator();
        while (bit.hasNext()) {
            Bullet b = bit.next();
            double[] tp = b.target.dead ? null : pointAt(b.target.dist);
            if (tp == null) { bit.remove(); continue; }
            double dx = tp[0] - b.x, dy = tp[1] - b.y;
            double d = Math.hypot(dx, dy);
            if (d < 12) {
                b.target.hp -= (int) b.dmg;
                particles.add(new Particle(tp[0], tp[1],
                        b.ice ? new Color(140, 220, 255) : new Color(255, 210, 90)));
                if (b.target.hp <= 0) kill(b.target);
                bit.remove();
            } else {
                b.x += dx / d * b.speed * dt;
                b.y += dy / d * b.speed * dt;
            }
        }

        // 粒子
        Iterator<Particle> pit = particles.iterator();
        while (pit.hasNext()) {
            Particle p = pit.next();
            p.x += p.vx * dt; p.y += p.vy * dt; p.vy += 160 * dt; p.life -= dt;
            if (p.life <= 0) pit.remove();
        }
    }

    void kill(Monster m) {
        if (m.dead) return;
        m.dead = true;                 // 只标记；移除由主循环统一做，避免迭代中修改集合
        money += m.bounty();
        kills++;
        double[] p = pointAt(m.dist);
        for (int i = 0; i < 7; i++) particles.add(new Particle(p[0], p[1], new Color(255, 120, 90)));
    }

    // ---------------- 绘制 ----------------
    @Override protected void paintComponent(Graphics g0) {
        super.paintComponent(g0);
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        // 草地
        for (int r = 0; r < ROWS; r++)
            for (int c = 0; c < COLS; c++) {
                g.setColor((r + c) % 2 == 0 ? new Color(0x8fbf6a) : new Color(0x84b561));
                g.fillRect(c * GRID, r * GRID, GRID, GRID);
            }

        // 路径（宽条）
        g.setColor(new Color(0xc9a86a));
        g.setStroke(new BasicStroke(44, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
        g.drawPolyline(xs(WAYPOINTS), ys(WAYPOINTS), WAYPOINTS.length);
        g.setColor(new Color(0xb5934f));
        g.setStroke(new BasicStroke(2));
        g.drawPolyline(xs(WAYPOINTS), ys(WAYPOINTS), WAYPOINTS.length);

        // 出怪口
        g.setColor(new Color(0x6a4a2c));
        g.fillOval(-18, 125 - 22, 44, 44);

        // 萝卜
        drawCarrot(g);

        // 塔
        for (Tower t : towers) drawTower(g, t);

        // 怪
        for (Monster m : monsters) drawMonster(g, m);

        // 子弹
        for (Bullet b : bullets) {
            g.setColor(b.ice ? new Color(0x8cdcff) : new Color(0x3c3c3c));
            g.fillOval((int) b.x - 5, (int) b.y - 5, 10, 10);
        }

        // 粒子
        for (Particle p : particles) {
            g.setColor(p.c);
            g.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER,
                    (float) Math.max(0, p.life * 2)));
            g.fillOval((int) p.x - 3, (int) p.y - 3, 6, 6);
        }
        g.setComposite(AlphaComposite.SrcOver);

        // 范围指示
        if (selectedTower != null || buildSpot != null) {
            Tower t = selectedTower != null ? selectedTower : buildSpot;
            g.setColor(new Color(255, 255, 255, 60));
            g.fillOval(t.x - (int) t.range(), t.y - (int) t.range(),
                    (int) t.range() * 2, (int) t.range() * 2);
            g.setColor(Color.WHITE);
            g.setStroke(new BasicStroke(1.5f));
            g.drawOval(t.x - (int) t.range(), t.y - (int) t.range(),
                    (int) t.range() * 2, (int) t.range() * 2);
        }

        // 面板按钮
        for (Btn b : panelBtns) {
            g.setColor(b.enabled ? new Color(0x2c3e50) : new Color(0x555555));
            g.fillRoundRect(b.x, b.y, b.w, b.h, 10, 10);
            g.setColor(Color.WHITE);
            g.setFont(new Font("微软雅黑", Font.BOLD, 14));
            g.drawString(b.label, b.x + 10, b.y + 20);
        }

        // 底部状态栏
        g.setColor(new Color(0x2c3e50));
        g.fillRect(0, ROWS * GRID, W, H - ROWS * GRID);
        g.setColor(Color.WHITE);
        g.setFont(new Font("微软雅黑", Font.BOLD, 17));
        g.drawString("金币: " + money, 16, ROWS * GRID + 30);
        g.setColor(new Color(0xff9a7a));
        g.drawString("萝卜血量: " + carrotHp, 150, ROWS * GRID + 30);
        g.setColor(new Color(0xffe14a));
        g.drawString("第 " + wave + "/" + WAVE_TOTAL + " 波", 300, ROWS * GRID + 30);
        g.setColor(Color.WHITE);
        g.drawString("消灭: " + kills, 440, ROWS * GRID + 30);
        if (spawnQueue.isEmpty() && monsters.isEmpty() && state.equals("play"))
            g.drawString("下一波 " + Math.max(0, (int) Math.ceil(waveTimer)) + " 秒", 560, ROWS * GRID + 30);
        g.setColor(new Color(0xa8c8e0));
        g.setFont(new Font("微软雅黑", Font.PLAIN, 13));
        g.drawString("点空地建塔 · 点塔升级/卖 · P 暂停", 760, ROWS * GRID + 30);

        // 提示条
        if (!toast.isEmpty()) {
            g.setColor(new Color(0, 0, 0, 160));
            g.setFont(new Font("微软雅黑", Font.BOLD, 22));
            int tw = g.getFontMetrics().stringWidth(toast);
            g.fillRoundRect(W / 2 - tw / 2 - 18, 84, tw + 36, 42, 12, 12);
            g.setColor(Color.YELLOW);
            g.drawString(toast, W / 2 - tw / 2, 113);
        }

        // 胜负
        if (!state.equals("play")) {
            g.setColor(new Color(0, 0, 0, 150));
            g.fillRect(0, 0, W, H);
            g.setFont(new Font("微软雅黑", Font.BOLD, 44));
            if (state.equals("win")) {
                g.setColor(new Color(0xffe14a));
                g.drawString("胜利！萝卜守住了！", 300, 280);
            } else {
                g.setColor(new Color(0xff7a6a));
                g.drawString("失败……萝卜被吃光了", 270, 280);
            }
            g.setFont(new Font("微软雅黑", Font.PLAIN, 18));
            g.setColor(Color.WHITE);
            g.drawString("点击任意位置重新开始", 400, 340);
        }

        if (paused && state.equals("play")) {
            g.setColor(new Color(0, 0, 0, 110));
            g.fillRect(0, 0, W, H);
            g.setColor(Color.WHITE);
            g.setFont(new Font("微软雅黑", Font.BOLD, 36));
            g.drawString("已暂停 (P 继续)", 380, 300);
        }
    }

    void drawCarrot(Graphics2D g) {
        int x = CARROT[0], y = CARROT[1];
        double pulse = 1 + 0.04 * Math.sin(System.currentTimeMillis() / 300.0);
        int r = (int) (20 * pulse);
        g.setColor(new Color(0xff8c1a));
        g.fillPolygon(new int[]{x - r, x + r, x}, new int[]{y + r / 2, y + r / 2, y + r * 2}, 3);
        g.setColor(new Color(0xffa53e));
        g.fillOval(x - r, y - r / 2, r * 2, r);
        // 叶子
        g.setColor(new Color(0x3f9e2a));
        for (int i = -1; i <= 1; i++) {
            g.setStroke(new BasicStroke(4, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
            g.drawLine(x, y - r / 2, x + i * 12, y - r / 2 - 26 + Math.abs(i) * 8);
        }
        // 脸
        g.setColor(Color.BLACK);
        g.fillOval(x - 8, y - 6, 4, 5);
        g.fillOval(x + 4, y - 6, 4, 5);
        g.setStroke(new BasicStroke(2));
        g.drawArc(x - 5, y + 1, 10, 6, 0, -180);
    }

    void drawTower(Graphics2D g, Tower t) {
        g.setColor(t.kind == 0 ? new Color(0x8a6238) : new Color(0x3a7ca5));
        g.fillRoundRect(t.x - 16, t.y - 10, 32, 26, 8, 8);
        g.setColor(t.kind == 0 ? new Color(0xa87f4e) : new Color(0x5a9cc5));
        g.fillOval(t.x - 13, t.y - 18, 26, 20);
        // 炮管/水晶
        if (t.kind == 0) {
            g.setColor(new Color(0x4a3320));
            g.setStroke(new BasicStroke(6, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
            g.drawLine(t.x, t.y - 8, t.x + (int) (Math.cos(t.angle) * 18),
                    t.y - 8 + (int) (Math.sin(t.angle) * 18));
        } else {
            g.setColor(new Color(0xbfeaff));
            int py = t.y - 24 + (int) (3 * Math.sin(System.currentTimeMillis() / 250.0));
            g.fillPolygon(new int[]{t.x, t.x - 7, t.x + 7},
                    new int[]{py - 9, py + 5, py + 5}, 3);
            g.fillPolygon(new int[]{t.x, t.x - 7, t.x + 7},
                    new int[]{py + 9, py - 5, py - 5}, 3);
        }
        // 等级星
        g.setColor(Color.YELLOW);
        for (int i = 0; i < t.level; i++)
            g.fillOval(t.x - 12 + i * 9, t.y + 12, 6, 6);
    }

    void drawMonster(Graphics2D g, Monster m) {
        double[] p = pointAt(m.dist);
        int x = (int) p[0], y = (int) p[1];
        Color body = m.kind == 0 ? new Color(0xd95f5f)
                : m.kind == 1 ? new Color(0xe0a53e) : new Color(0x8a5fbf);
        int r = (int) m.r();
        g.setColor(body);
        g.fillOval(x - r, y - r, r * 2, r * 2);
        g.setColor(body.darker());
        g.fillOval(x - r, y - r, r * 2, r * 2 / 3);
        // 眼睛
        g.setColor(Color.WHITE);
        g.fillOval(x - r / 2 - 3, y - r / 3, 7, 7);
        g.fillOval(x + r / 2 - 4, y - r / 3, 7, 7);
        g.setColor(Color.BLACK);
        g.fillOval(x - r / 2 - 1, y - r / 3 + 2, 3, 3);
        g.fillOval(x + r / 2 - 2, y - r / 3 + 2, 3, 3);
        // 减速特效
        if (m.slowT > 0) {
            g.setColor(new Color(140, 220, 255, 120));
            g.fillOval(x - r - 3, y - r - 3, r * 2 + 6, r * 2 + 6);
        }
        // 血条
        int bw = r * 2 + 8;
        g.setColor(new Color(50, 50, 50));
        g.fillRect(x - bw / 2, y - r - 12, bw, 5);
        g.setColor(new Color(0x7fe05a));
        g.fillRect(x - bw / 2, y - r - 12, (int) (bw * (double) m.hp / m.maxHp), 5);
    }

    static int[] xs(int[][] pts) { int[] a = new int[pts.length]; for (int i = 0; i < a.length; i++) a[i] = pts[i][0]; return a; }
    static int[] ys(int[][] pts) { int[] a = new int[pts.length]; for (int i = 0; i < a.length; i++) a[i] = pts[i][1]; return a; }

    // ---------------- 主程序 ----------------
    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            JFrame f = new JFrame("保卫萝卜 · 简化版");
            CarrotDefense panel = new CarrotDefense();
            f.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            f.setContentPane(panel);
            f.pack();
            f.setResizable(false);
            f.setLocationRelativeTo(null);
            f.setVisible(true);
            new javax.swing.Timer((int) (DT * 1000), e -> { panel.update(); panel.repaint(); }).start();
        });
    }
}
