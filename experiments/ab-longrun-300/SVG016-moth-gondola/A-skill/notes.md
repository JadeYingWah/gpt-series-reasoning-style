# Notes · SVG016 moth × gondola

## 方向（本次为冒险直选）

**月夜威尼斯运河贡多拉**：深蓝夜空、暖琥珀灯笼、象牙色飞蛾驾黑贡多拉；世界向左滚动 ⇒ 载具相对向右前进。

## 设计 token

| token | hex | 用途 |
|-------|-----|------|
| --night | #0a0e1a | 最深背景 |
| --dusk | #1a2340 | 远景建筑 |
| --stone | #3d4560 | 中景墙面/窗 |
| --ivory | #f2e8d5 | 飞蛾高光/月 |
| --moth-body | #c9a86c | 胸/腹主色 |
| --moth-dark | #6b4a28 | 附肢/纹路 |
| --moth-wing | #e8d5a8 | 翅面 |
| --moth-spot | #8b3a3a | 眼斑 |
| --gondola | #0d0d12 | 船体 |
| --gold | #d4a84b | 船饰/灯框 |
| --amber | #f0b040 | 灯焰 |
| --canal | #0c1828 | 水面 |

字体：系统栈 `Segoe UI / PingFang SC / Microsoft YaHei / system-ui`（无外链字体）。

## 几何与运动自洽

### 前进方向模型

- 场景为无限循环视差：背景/中景/近景向 **左** 平移。
- 物理含义：贡多拉相对世界 **向右** 前进（与需求「朝画面右侧」一致）。
- 船体保持在画面中右区域（x≈600），通过环境相对运动表达前进；船体另有轻微摇摆 bob。
- **船头朝右**：ferro di prua（铁制船首梳）在 x≈810，指向右侧并上扬；艉饰在左侧。

### 桨橹运动 ↔ 前进

- 桨 `.oar-stroke`（周期 3.2s）：桨杆从船右舷 forcola 向 **左后方** 入水。
- 向左后推水 ⇒ 船体受反作用向右前进。方向自洽。
- 桨叶 `.oar-blade` 有独立入水角度变化，非刚体锁死。

### 背景视差（≥2 层，实为 3 层）

| 层 | class | 循环周期 | 相对速度 |
|----|-------|----------|----------|
| 远景宫殿天际线 | `.scroll-far` | 32s | ≈0.25× |
| 中景立面/桥/灯 | `.scroll-mid` | 16s | ≈0.50× |
| 近景系船柱/涟漪 | `.scroll-near` | 8s | 1.0× |

每层 SVG 内双 tile（0 与 1200）平铺，`translateX(-1200px)` 无缝循环。
月亮与水面反光为 **固定** 元素（世界参考系），不随视差滚动。

### 飞蛾相对载具的独立运动（≥4 处）

| 附肢 | class | 周期 | 说明 |
|------|-------|------|------|
| 左翅 | `.wing-l` | 0.72s | 旋转 + scaleY，与船体不同相 |
| 右翅 | `.wing-r` | 0.72s | 相位偏移，近侧更明显 |
| 左触角 | `.antenna-l` | 1.4s | 独立摇摆 |
| 右触角 | `.antenna-r` | 1.7s | 异相摇摆（羽状触角） |
| 前足 | `.leg-front` | 1.9s | 抓握微调 |
| 中足 | `.leg-mid` | 2.3s | 异相 |
| 后足 | `.leg-rear` | 2.05s | 异相 |
| 腹部 | `.abdomen-sway` | 2.8s | 绕腹根旋转，非锁死 |
| 身体微浮 | `.moth-bob` | 2.1s | 与船 bob（2.6s）频率分离 |

船体 `.hull-bob`（2.6s）≠ 全身锁死：翅/触角/足/腹均有独立 transform-origin 与时间曲线。

### 其他环境动效

- 灯笼 `.lantern-flicker`：脉冲闪烁（多灯相位错开）。
- 水面涟漪 `.water-ripple`：opacity + scaleX 微振。
- 月晕 `.moon-halo`：呼吸发光。
- 水面月影 `.reflection-wobble`：波动。
- 尾流（wake）：船左后方涟漪，强化向右前进感。
- `prefers-reduced-motion: reduce` 时关闭全部动画。

## 无外部依赖

- 单文件：CSS/SVG 全内联。
- 无 CDN、无 `@import`、无 `fetch`、无 `img src=http`、无 web font。
- 纯静态打开即可运行。

## 识别性检查（代码级）

- **Moth**：羽状双触角、复眼、卷曲喙、毛绒胸部、分节腹部、带眼斑双翅、三对足。
- **Gondola**：狭长黑色船体、ferro di prua 铁梳（右）、艉饰、trasto 座、forcola 桨架、艉灯、金色饰线。
- **Venice canal**：palazzo 立面、拱桥、系船柱 briccola、运河水面、月影。
