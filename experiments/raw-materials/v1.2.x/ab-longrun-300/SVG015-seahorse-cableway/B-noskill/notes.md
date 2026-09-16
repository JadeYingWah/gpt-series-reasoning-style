# SVG015-seahorse-cableway · 几何/运动自洽说明

## 主体与朝向

- **主体**：海马（seahorse）驾驶索道吊厢（cableway cabin）。
- **朝向**：整体朝画面右侧前进。
  - 吊厢前脸在 +x（右），装有朝右的头灯 `translate(90,70)` 与朝右的船首饰件 `M85,-8 Q120,-22 138,-4`。
  - 海马吻部/口鼻朝右（`snout` 路径向 +x 延伸，眼在吻部后上方），符合“驾驶员面向前进方向”。
  - 世界位移速度为正（`SPEED = 42`，`world` 递增，cabin x 递增）→ **前进方向 = 右**。

## 载具与滚动动画（与前进方向一致）

索道本身没有地面车轮，采用 **索夹滚轮 + 底部导向轮** 的旋转来表达“沿缆前进”：

| 部件 | class | 旋转 | 与前进关系 |
|------|-------|------|------------|
| 索夹滚轮 ×2 | `grip-roller` | `wheelSpin` 0.55s linear | 贴在缆上滚动，随厢体向右 → 视觉上持续正转 |
| 底部导向轮 ×3 | `guide-wheel` | `wheelSpin` 0.4s linear | 同上，线速度略慢于索夹 |

旋转用 CSS `@keyframes wheelSpin { to { transform: rotate(360deg); } }`，`linear` 保证角速度恒定，与匀速平移一致。

## 海马相对车厢的肢体运动（≥2 处，非锁死）

车厢整体由 JS 做 **平移 + 吊挂摆动（sway）+ 垂向 bob**；以下附肢用独立 CSS 动画，周期/相位各不相同，**不跟随车厢刚体变换锁死**：

1. **右胸鳍** `.fin-right` — `finL`/`finR` 异相，0.95s，绕鳍根旋转（去够操纵杆）。
2. **左胸鳍** `.fin-left` — 1.1s，另一套相位，远侧鳍。
3. **尾巴** `.tail` — `tailWave` 1.6s，带 translateX 的左右摆动（S 形海马特征）。
4. **头冠/背鳍** `.crown` — `crownBob` 1.3s。
5. **口鼻** `.snout` — `snoutPulse` 0.7s（呼吸/吐泡）。
6. **操纵杆** `.lever` — `leverRock` 0.85s，独立于车体旋转。

> 判分点：至少 fin-left / fin-right / tail 三处与车体“平移+摆动”不同步。

## 背景视差（4 层 + 水面）

| 层 id | 内容 | 视差系数 `P` | 效果 |
|-------|------|--------------|------|
| `layer-far` | 远山脊、高空云、远缆虚线 | 0.12 | 极慢 |
| `layer-mid` | 近丘、中云带 | 0.28 | 慢 |
| `layer-towers` + `layer-cable` | 索塔、主缆、回空缆 | 0.55 | 中（与吊厢同深度系） |
| `layer-fg` | 前景海草/珊瑚/底缘 | 0.95 | 快，略超前 |

JS 中 `world += SPEED * dt`，各层 `translate(-world*P % tile)`，形成无限循环滚动。吊厢以 `world * 1.0` 在 1600 画布上 wrap，相对背景表现为“自己在前进”。

另：水面 sparkle 用 `P=0.4` 再加一层微动。

## 技术约束

- 单文件 `art.html`，CSS/JS 内联。
- 无 CDN、无外链、无网络请求。
- 主体为 **SVG**（非 canvas），动画 = CSS keyframes + requestAnimationFrame 驱动的 transform。
