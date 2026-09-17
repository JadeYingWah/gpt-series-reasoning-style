import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.*;

/**
 * 保卫萝卜（Java Swing 版塔防）
 * 编译: javac -encoding UTF-8 CarrotFantasy.java
 * 运行: java CarrotFantasy   （或双击 启动保卫萝卜.bat）
 *
 * 玩法：怪物沿小路进攻尽头的萝卜。选中底部炮塔→点击草地建造；
 *       点击已建炮塔升级；右键炮塔出售。守住 10 波进攻即可通关。
 */
public class CarrotFantasy extends JPanel implements ActionListener, MouseListener {

    // ---------------- 常量 ----------------
    static final int CELL = 40, COLS = 24, ROWS = 14;
    static final int W = COLS * CELL, FIELD_H = ROWS * CELL, H = FIELD_H + 84, TOP = 30;
    static final int[][] WPS = {{0,2},{7,2},{7,7},{2,7},{2,11},{12,11},{12,4},{18,4},{18,9},{23,9}};
    static final String[] TNAMES = {"瓶子塔", "火箭塔", "冰星塔"};
    static final int[]    TCOST  = {100, 180, 150};
    static final int[][]  TUP    = {{90,140},{160,220},{130,190}};   // 升级花费
    static final double[] TRANGE = {120, 165, 130};
    static final double[] TRATE  = {0.45, 1.15, 0.55};
    static final double[] TDMG   = {14, 34, 7};
    static final Color[]  TCOL   = {new Color(0x2f7fd8), new Color(0xd8452f), new Color(0xe8b820)};
    static final boolean[][] PATH = new boolean[COLS][ROWS];
    static final Font F(int s, int b){ return new Font("Microsoft YaHei", b, s); }

    static {
        for (int i = 0; i < WPS.length - 1; i++) {
            int c0=WPS[i][0], r0=WPS[i][1], c1=WPS[i+1][0], r1=WPS[i+1][1];
            for (int c=Math.min(c0,c1); c<=Math.max(c0,c1); c++)
                for (int r=Math.min(r0,r1); r<=Math.max(r0,r1); r++)
                    PATH[c][r] = true;
        }
    }

    // ---------------- 实体 ----------------
    static class Tower {
        int c, r, type, level = 1; double cool = 0, invested;
        int cx(){ return c*CELL + CELL/2; }
        int cy(){ return r*CELL + CELL/2; }
    }
    static class Mons {
        double x, y; int wp = 0, kind, hp, maxhp, leak;
        double speed, slowT = 0, flash = 0;
    }
    static class Shot { double x, y; Mons target; double speed, dmg, splash, slow; int type; }
    static class FloatT { double x, y, t; String txt; }

    // ---------------- 状态 ----------------
    double t = 0, interT = 3.0, bannerT = 0, hintT = 0;
    int money = 320, lives = 10, wave = 0, buildSel = -1, speed = 1, spawnLeft = 0;
    double spawnT = 0, spawnGap = 1.4;
    boolean playing = false, over = false, win = false;
    String banner = "", hint = "";
    java.util.List<Integer> queue = new ArrayList<>();
    java.util.List<Tower> towers = new ArrayList<>();
    java.util.List<Mons> mons = new ArrayList<>();
    java.util.List<Shot> shots = new ArrayList<>();
    java.util.List<FloatT> floats = new ArrayList<>();
    Tower selTower = null;
    Rectangle startRect = new Rectangle(W/2-130, 400, 260, 60);
    Rectangle restartRect = new Rectangle(W/2-130, 430, 260, 60);
    Rectangle[] btnRects = new Rectangle[3];
    Rectangle spdRect = new Rectangle(20, FIELD_H + 60, 120, 34);
    javax.swing.Timer timer;

    public CarrotFantasy() {
        setPreferredSize(new Dimension(W, H));
        addMouseListener(this);
        for (int i = 0; i < 3; i++) btnRects[i] = new Rectangle(160 + i*160, FIELD_H + 48, 150, 44);
        reset();
        timer = new javax.swing.Timer(16, this);
        timer.start();
    }

    void reset() {
        money = 320; lives = 10; wave = 0; buildSel = -1; speed = 1;
        playing = false; over = false; win = false; selTower = null;
        towers.clear(); mons.clear(); shots.clear(); floats.clear(); queue.clear();
        t = 0; interT = 3.0; banner = ""; bannerT = 0; spawnLeft = 0;
    }

    // ---------------- 波次 ----------------
    void startWave(int w) {
        wave = w;
        banner = (w == 10 ? "最终波！BOSS 来袭！" : "第 " + w + " 波来袭！");
        bannerT = 2.6;
        queue.clear();
        int normals = 5 + w;
        for (int i = 0; i < normals; i++) queue.add(0);
        if (w % 3 == 0) for (int i = 0; i < w / 3; i++) queue.add(1);
        if (w == 10) for (int i = 0; i < 3; i++) queue.add(2);
        Collections.shuffle(queue);
        spawnLeft = queue.size();
        spawnGap = Math.max(0.85, 1.5 - 0.05 * w);
        spawnT = 0.4;
        interT = 12.0;
    }

    void spawn(int kind) {
        Mons m = new Mons();
        m.kind = kind;
        m.x = -25; m.y = WPS[0][1]*CELL + CELL/2;
        double hpScale = 1 + 0.38 * (wave - 1);
        if (kind == 0) { m.hp = (int)(55 * hpScale); m.speed = 50 + Math.random()*14; m.leak = 1; }
        else if (kind == 1) { m.hp = (int)(55 * hpScale * 2.6); m.speed = 34; m.leak = 2; }
        else { m.hp = 1300; m.speed = 30; m.leak = 3; }
        m.maxhp = m.hp;
        mons.add(m);
    }

    int reward(Mons m) {
        if (m.kind == 0) return 12 + 2*wave;
        if (m.kind == 1) return 30 + 3*wave;
        return 220;
    }

    // ---------------- 主循环 ----------------
    @Override public void actionPerformed(ActionEvent e) {
        double dt = 0.016 * speed;
        if (playing && !over) update(dt);
        repaint();
    }

    void setHint(String s) { hint = s; hintT = 2.2; }

    void update(double dt) {
        t += dt;
        if (bannerT > 0) bannerT -= dt;
        if (hintT > 0) hintT -= dt;

        // 出怪
        if (spawnLeft > 0) {
            spawnT -= dt;
            if (spawnT <= 0) {
                spawnT = spawnGap;
                spawnLeft--;
                spawn(queue.remove(0));
            }
        } else if (mons.isEmpty()) {
            if (wave >= 10) { over = true; win = true; return; }
            interT -= dt;
            if (interT <= 0) startWave(wave + 1);
        }

        // 怪物移动
        Iterator<Mons> it = mons.iterator();
        while (it.hasNext()) {
            Mons m = it.next();
            if (m.slowT > 0) m.slowT -= dt;
            if (m.flash > 0) m.flash -= dt;
            double tx = WPS[m.wp][0]*CELL + CELL/2, ty = WPS[m.wp][1]*CELL + CELL/2;
            double dx = tx - m.x, dy = ty - m.y, d = Math.hypot(dx, dy);
            double step = m.speed * (m.slowT > 0 ? 0.55 : 1) * dt;
            if (d <= step) {
                m.x = tx; m.y = ty; m.wp++;
                if (m.wp >= WPS.length) {
                    lives -= m.leak;
                    it.remove();
                    if (lives <= 0) { lives = 0; over = true; win = false; return; }
                }
            } else { m.x += dx/d*step; m.y += dy/d*step; }
        }

        // 炮塔开火
        for (Tower tw : towers) {
            tw.cool -= dt;
            if (tw.cool > 0) continue;
            double range = TRANGE[tw.type] * (1 + 0.15*(tw.level-1));
            Mons best = null; double bp = -1e18;
            for (Mons m : mons) {
                if (Math.hypot(m.x-tw.cx(), m.y-tw.cy()) > range) continue;
                double dNext = Math.hypot(WPS[m.wp][0]*CELL+CELL/2 - m.x, WPS[m.wp][1]*CELL+CELL/2 - m.y);
                double prog = m.wp * 100000.0 - dNext;
                if (prog > bp) { bp = prog; best = m; }
            }
            if (best != null) {
                tw.cool = TRATE[tw.type] * Math.pow(0.9, tw.level-1);
                Shot s = new Shot();
                s.x = tw.cx(); s.y = tw.cy(); s.target = best; s.type = tw.type;
                s.speed = tw.type == 1 ? 240 : (tw.type == 2 ? 340 : 300);
                s.dmg = TDMG[tw.type] * Math.pow(1.6, tw.level-1);
                if (tw.type == 1) s.splash = 55;
                if (tw.type == 2) s.slow = 1.6;
                shots.add(s);
            }
        }

        // 子弹
        Iterator<Shot> sit = shots.iterator();
        while (sit.hasNext()) {
            Shot s = sit.next();
            Mons m = s.target;
            if (!mons.contains(m)) { sit.remove(); continue; }
            double dx = m.x - s.x, dy = m.y - s.y, d = Math.hypot(dx, dy);
            double step = s.speed * dt;
            if (d <= step || d < 6) {
                m.hp -= s.dmg; m.flash = 0.1;
                if (s.slow > 0) m.slowT = s.slow;
                if (s.splash > 0) {
                    for (Mons o : mons)
                        if (o != m && Math.hypot(o.x-m.x, o.y-m.y) <= s.splash) { o.hp -= s.dmg*0.6; o.flash = 0.1; }
                }
                sit.remove();
            } else { s.x += dx/d*step; s.y += dy/d*step; }
        }

        // 击杀结算
        Iterator<Mons> kit = mons.iterator();
        while (kit.hasNext()) {
            Mons m = kit.next();
            if (m.hp <= 0) {
                money += reward(m);
                FloatT f = new FloatT();
                f.x = m.x; f.y = m.y - 16; f.t = 0; f.txt = "+¥" + reward(m);
                floats.add(f);
                kit.remove();
            }
        }

        // 飘字
        Iterator<FloatT> fit = floats.iterator();
        while (fit.hasNext()) { FloatT f = fit.next(); f.t += dt; f.y -= 24*dt; if (f.t > 1.1) fit.remove(); }
    }

    // ---------------- 绘制 ----------------
    @Override protected void paintComponent(Graphics g0) {
        super.paintComponent(g0);
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        drawField(g);
        drawCarrot(g);
        for (Tower tw : towers) drawTower(g, tw);
        for (Mons m : mons) drawMons(g, m);
        for (Shot s : shots) {
            g.setColor(s.type == 1 ? new Color(0xff6a3c) : s.type == 2 ? new Color(0x9fd8ff) : new Color(0xd8f0ff));
            int rr = s.type == 1 ? 6 : 4;
            g.fillOval((int)s.x-rr, (int)s.y-rr, rr*2, rr*2);
        }
        drawHUD(g);
        for (FloatT f : floats) {
            g.setColor(new Color(255, 240, 120, (int)(255*Math.max(0,1-f.t))));
            g.setFont(F(14, Font.BOLD));
            g.drawString(f.txt, (int)f.x - 14, (int)f.y);
        }
        if (bannerT > 0) {
            g.setFont(F(30, Font.BOLD));
            int w = g.getFontMetrics().stringWidth(banner);
            g.setColor(new Color(0,0,0,150)); g.fillRoundRect(W/2-w/2-20, 60, w+40, 52, 14, 14);
            g.setColor(new Color(0xffe08a)); g.drawString(banner, W/2-w/2, 95);
        }
        if (!playing) drawStart(g);
        if (over) drawOver(g);
    }

    void drawField(Graphics2D g) {
        for (int c = 0; c < COLS; c++)
            for (int r = 0; r < ROWS; r++) {
                g.setColor(PATH[c][r] ? new Color(0xd9b38c) : ((c+r)%2==0 ? new Color(0x7ec850) : new Color(0x74bd49)));
                g.fillRect(c*CELL, r*CELL, CELL, CELL);
            }
        // 小路描边
        g.setColor(new Color(0,0,0,25));
        for (int c = 0; c < COLS; c++)
            for (int r = 0; r < ROWS; r++)
                if (PATH[c][r]) g.drawRect(c*CELL, r*CELL, CELL, CELL);
    }

    void drawCarrot(Graphics2D g) {
        double x = WPS[WPS.length-1][0]*CELL + CELL/2, y = WPS[WPS.length-1][1]*CELL + CELL/2;
        g.setColor(new Color(0x8a5a2b)); g.fillRect((int)x-16, (int)y+8, 32, 14);      // 土堆
        g.setColor(new Color(0xff7f2a));                                              // 萝卜身
        int[] xs = {(int)x-13, (int)x+13, (int)x};
        int[] ys = {(int)y-6, (int)y-6, (int)y+26};
        g.fillPolygon(xs, ys, 3);
        g.setColor(new Color(0x2f9e44));                                              // 叶子
        g.fillRect((int)x-8, (int)y-20, 5, 15);
        g.fillRect((int)x-2, (int)y-24, 5, 19);
        g.fillRect((int)x+4, (int)y-20, 5, 15);
        g.setColor(Color.WHITE); g.fillOval((int)x-7, (int)y-2, 5, 5); g.fillOval((int)x+2, (int)y-2, 5, 5);
        g.setColor(Color.BLACK); g.fillOval((int)x-6, (int)y-1, 3, 3); g.fillOval((int)x+3, (int)y-1, 3, 3);
        if (lives <= 4) {                                                              // 受伤表情
            g.setColor(new Color(0x8f1a12)); g.drawLine((int)x-6, (int)y+6, (int)x+6, (int)y+10);
            g.drawLine((int)x+6, (int)y+6, (int)x-6, (int)y+10);
        }
    }

    void drawTower(Graphics2D g, Tower tw) {
        int x = tw.cx(), y = tw.cy();
        if (selTower == tw) {
            double range = TRANGE[tw.type] * (1 + 0.15*(tw.level-1));
            g.setColor(new Color(255,255,255,70));
            g.fillOval((int)(x-range), (int)(y-range), (int)range*2, (int)range*2);
            g.setColor(new Color(255,255,255,160)); g.drawOval((int)(x-range), (int)(y-range), (int)range*2, (int)range*2);
        }
        g.setColor(new Color(0,0,0,40)); g.fillOval(x-14, y+8, 28, 10);
        Color col = TCOL[tw.type];
        if (tw.type == 0) {                                  // 瓶子塔
            g.setColor(col); g.fillRoundRect(x-10, y-14, 20, 28, 10, 10);
            g.setColor(col.brighter()); g.fillOval(x-7, y-20, 14, 12);
        } else if (tw.type == 1) {                           // 火箭塔
            g.setColor(col); g.fillPolygon(new int[]{x-12,x+12,x}, new int[]{y+12,y+12,y-18}, 3);
            g.setColor(Color.WHITE); g.fillRect(x-2, y+2, 4, 8);
        } else {                                             // 冰星塔
            g.setColor(col); fillStar(g, x, y, 16, 7);
            g.setColor(Color.WHITE); fillStar(g, x, y, 7, 5);
        }
        for (int i = 0; i < tw.level; i++) {                 // 等级点
            g.setColor(new Color(0xffe23a));
            g.fillOval(x - 10 + i*8, y + 14, 5, 5);
        }
        if (selTower == tw && tw.level < 3) {
            g.setColor(Color.WHITE); g.setFont(F(12, Font.BOLD));
            g.drawString("升级 ¥" + TUP[tw.type][tw.level-1], x - 34, y - 26);
        }
    }

    void fillStar(Graphics2D g, int cx, int cy, int R, int r) {
        int[] xs = new int[10]; int[] ys = new int[10];
        for (int i = 0; i < 10; i++) {
            double a = -Math.PI/2 + i * Math.PI/5;
            int rad = (i % 2 == 0) ? R : r;
            xs[i] = (int)(cx + Math.cos(a)*rad); ys[i] = (int)(cy + Math.sin(a)*rad);
        }
        g.fillPolygon(xs, ys, 10);
    }

    void drawMons(Graphics2D g, Mons m) {
        int r = m.kind == 0 ? 12 : m.kind == 1 ? 16 : 22;
        Color body = m.kind == 0 ? new Color(0x5cb85c) : m.kind == 1 ? new Color(0x9b59b6) : new Color(0xd8452f);
        if (m.flash > 0) body = Color.WHITE;
        g.setColor(new Color(0,0,0,40)); g.fillOval((int)m.x-r, (int)m.y+r-4, r*2, 8);
        g.setColor(body); g.fillOval((int)m.x-r, (int)m.y-r, r*2, r*2);
        g.setColor(body.darker()); g.drawOval((int)m.x-r, (int)m.y-r, r*2, r*2);
        if (m.slowT > 0) { g.setColor(new Color(0x9fd8ff)); g.drawOval((int)m.x-r-3, (int)m.y-r-3, r*2+6, r*2+6); }
        g.setColor(Color.WHITE); g.fillOval((int)m.x-6, (int)m.y-5, 5, 5); g.fillOval((int)m.x+2, (int)m.y-5, 5, 5);
        g.setColor(Color.BLACK); g.fillOval((int)m.x-5, (int)m.y-4, 3, 3); g.fillOval((int)m.x+3, (int)m.y-4, 3, 3);
        double ratio = Math.max(0, m.hp / (double) m.maxhp);
        g.setColor(new Color(0,0,0,120)); g.fillRect((int)m.x-r, (int)m.y-r-9, r*2, 5);
        g.setColor(ratio > 0.4 ? new Color(0x5ce05c) : new Color(0xff3030));
        g.fillRect((int)m.x-r, (int)m.y-r-9, (int)(r*2*ratio), 5);
    }

    void drawHUD(Graphics2D g) {
        g.setColor(new Color(0x2c1c0e)); g.fillRect(0, 0, W, TOP);
        g.setFont(F(16, Font.BOLD));
        g.setColor(new Color(0xffd447)); g.drawString("¥ " + money, 14, 21);
        g.setColor(new Color(0xffe9a8));
        g.drawString("第 " + Math.max(wave,0) + "/10 波", 150, 21);
        String hearts = "";
        for (int i = 0; i < lives; i++) hearts += "♥";
        g.setColor(new Color(0xff5c5c)); g.drawString(hearts, 290, 21);
        if (playing && !over && spawnLeft == 0 && mons.isEmpty() && wave < 10 && wave > 0) {
            g.setColor(new Color(0x9fd8ff));
            g.drawString("下一波：" + Math.ceil(interT) + "s", 430, 21);
        }
        // 底栏
        g.setColor(new Color(0x2c1c0e)); g.fillRect(0, FIELD_H, W, H - FIELD_H);
        g.setColor(new Color(0x8a6a3a)); g.fillRect(0, FIELD_H, W, 3);
        for (int i = 0; i < 3; i++) {
            Rectangle b = btnRects[i];
            boolean ok = money >= TCOST[i];
            g.setColor(buildSel == i ? new Color(0x1b8f4d) : ok ? new Color(0x1b6fae) : new Color(0x555f66));
            g.fillRoundRect(b.x, b.y, b.width, b.height, 12, 12);
            g.setColor(TCOL[i]); g.fillOval(b.x+10, b.y+12, 20, 20);
            g.setColor(Color.WHITE); g.setFont(F(14, Font.BOLD));
            g.drawString(TNAMES[i], b.x+38, b.y+19);
            g.setColor(new Color(0xffd447)); g.setFont(F(12, Font.PLAIN));
            g.drawString("¥" + TCOST[i] + (i==1?" · 溅射":i==2?" · 减速":" · 速攻"), b.x+38, b.y+36);
        }
        g.setColor(speed == 2 ? new Color(0x1b8f4d) : new Color(0x555f66));
        g.fillRoundRect(spdRect.x, spdRect.y, spdRect.width, spdRect.height, 10, 10);
        g.setColor(Color.WHITE); g.setFont(F(14, Font.BOLD));
        g.drawString(speed == 2 ? "×2 速度" : "×1 速度", spdRect.x + 26, spdRect.y + 22);
        g.setFont(F(12, Font.PLAIN)); g.setColor(new Color(0xd8c9a8));
        g.drawString("左键：选中炮塔建造型 → 点草地建造 / 点炮塔升级 · 右键：出售炮塔或取消", 160, FIELD_H + 76);
        if (hintT > 0) {
            g.setFont(F(14, Font.BOLD)); g.setColor(new Color(0xff9c6b));
            g.drawString(hint, 160, FIELD_H + 20);
        }
    }

    void drawStart(Graphics2D g) {
        g.setColor(new Color(0, 20, 10, 190)); g.fillRect(0, 0, W, H);
        g.setFont(F(52, Font.BOLD)); g.setColor(new Color(0xffb84d));
        g.drawString("保 卫 萝 卜", W/2 - 160, 220);
        g.setFont(F(18, Font.PLAIN)); g.setColor(new Color(0xdff2ff));
        g.drawString("怪物沿小路进攻尽头的萝卜，建炮塔守住 10 波进攻！", W/2 - 250, 290);
        g.drawString("瓶子塔速攻 · 火箭塔溅射 · 冰星塔减速 · 点击炮塔可升级", W/2 - 235, 325);
        g.setColor(new Color(0x1b8f4d)); g.fillRoundRect(startRect.x, startRect.y, startRect.width, startRect.height, 16, 16);
        g.setColor(Color.WHITE); g.setFont(F(26, Font.BOLD));
        g.drawString("开 始 游 戏", startRect.x + 56, startRect.y + 39);
    }

    void drawOver(Graphics2D g) {
        g.setColor(win ? new Color(0, 40, 15, 190) : new Color(60, 5, 5, 190));
        g.fillRect(0, 0, W, H);
        g.setFont(F(44, Font.BOLD));
        if (win) {
            g.setColor(new Color(0xffe23a)); g.drawString("通 关 成 功 ！", W/2 - 150, 300);
            int stars = lives == 10 ? 3 : lives >= 7 ? 2 : 1;
            g.setColor(new Color(0xffd447));
            for (int i = 0; i < 3; i++)
                if (i < stars) fillStar(g, W/2 - 90 + i*90, 370, 34, 15);
                else { g.setColor(new Color(90,90,90)); fillStar(g, W/2 - 90 + i*90, 370, 34, 15); g.setColor(new Color(0xffd447)); }
            g.setFont(F(18, Font.PLAIN)); g.setColor(Color.WHITE);
            g.drawString("剩余生命 " + lives + " / 10", W/2 - 60, 420);
        } else {
            g.setColor(new Color(0xff8080)); g.drawString("萝卜被吃掉了…", W/2 - 165, 330);
            g.setFont(F(18, Font.PLAIN)); g.setColor(Color.WHITE);
            g.drawString("坚持到了第 " + wave + " 波，再试一次吧！", W/2 - 130, 380);
        }
        g.setColor(new Color(0x1b6fae)); g.fillRoundRect(restartRect.x, restartRect.y, restartRect.width, restartRect.height, 14, 14);
        g.setColor(Color.WHITE); g.setFont(F(24, Font.BOLD));
        g.drawString("再 来 一 局", restartRect.x + 62, restartRect.y + 38);
    }

    // ---------------- 交互 ----------------
    Tower towerAt(int px, int py) {
        int c = px / CELL, r = py / CELL;
        for (Tower tw : towers) if (tw.c == c && tw.r == r) return tw;
        return null;
    }

    @Override public void mousePressed(MouseEvent e) {
        int x = e.getX(), y = e.getY();
        if (!playing) {
            if (startRect.contains(x, y)) playing = true;
            return;
        }
        if (over) {
            if (restartRect.contains(x, y)) reset();
            return;
        }
        if (e.getButton() == MouseEvent.BUTTON3) {
            Tower tw = towerAt(x, y);
            if (tw != null && y < FIELD_H) {
                int refund = (int)(tw.invested * 0.6);
                money += refund;
                towers.remove(tw);
                selTower = null;
                setHint("出售炮塔，返还 ¥" + refund);
            } else { selTower = null; buildSel = -1; }
            return;
        }
        // 底栏按钮
        for (int i = 0; i < 3; i++)
            if (btnRects[i].contains(x, y)) { buildSel = (buildSel == i ? -1 : i); selTower = null; return; }
        if (spdRect.contains(x, y)) { speed = speed == 1 ? 2 : 1; return; }
        // 场地
        if (y < FIELD_H) {
            int c = x / CELL, r = y / CELL;
            if (PATH[c][r]) { setHint("小路上不能建塔！"); return; }
            Tower tw = towerAt(x, y);
            if (tw != null) {                                   // 升级
                selTower = tw;
                if (tw.level >= 3) { setHint("该炮塔已满级"); return; }
                int cost = TUP[tw.type][tw.level-1];
                if (money >= cost) {
                    money -= cost; tw.invested += cost; tw.level++;
                    setHint(TNAMES[tw.type] + "升到 " + tw.level + " 级！");
                } else setHint("金钱不足，升级需要 ¥" + cost);
                return;
            }
            if (buildSel < 0) { setHint("先在下方选择一种炮塔"); return; }
            int cost = TCOST[buildSel];
            if (money < cost) { setHint("金钱不足，建造需要 ¥" + cost); return; }
            Tower nt = new Tower();
            nt.c = c; nt.r = r; nt.type = buildSel; nt.invested = cost;
            towers.add(nt);
            money -= cost;
        }
    }

    @Override public void mouseClicked(MouseEvent e) {}
    @Override public void mouseEntered(MouseEvent e) {}
    @Override public void mouseExited(MouseEvent e) {}
    @Override public void mouseReleased(MouseEvent e) {}

    public static void main(String[] args) {
        final boolean selftest = args.length > 0 && "selftest".equals(args[0]);
        SwingUtilities.invokeLater(() -> {
            JFrame f = new JFrame("保卫萝卜 · Java 版");
            CarrotFantasy p = new CarrotFantasy();
            f.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            f.getContentPane().add(p);
            f.pack();
            f.setResizable(false);
            f.setLocationRelativeTo(null);
            f.setVisible(true);
            if (selftest) {
                p.playing = true;   // 自测时直接进入游戏跑几帧
                new javax.swing.Timer(1300, ev -> {
                    System.out.println("SELFTEST OK");
                    f.dispose();
                    System.exit(0);
                }).start();
            }
        });
    }
}
