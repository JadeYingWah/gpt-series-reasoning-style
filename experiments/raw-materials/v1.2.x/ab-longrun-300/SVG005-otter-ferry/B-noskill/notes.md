# SVG005-otter-ferry · 自洽说明（notes）

工作目录：`B-noskill`
主体：一只 otter 驾驶 ferry，朝画面右侧前进。

## 1. 前进方向与滚动一致性

- 画面逻辑：船体在视野中向右前进，因此背景各层做 `translateX(负向)` 的无限循环，模拟水面向后掠过。
- 无车轮/履带；推进器为船尾螺旋桨（`#propeller`）。
- 螺旋桨旋转：CSS `rotate(0deg → 360deg)`，即顺时针（CW）。
  - 螺旋桨位于船尾（画面左侧 `-165`），顺时针旋转将水向后（左）推，船体向右前进 —— 与前进方向自洽。
- 船尾 `#wake` 尾迹在螺旋桨后方（左）扰动，与「右进」一致。
- 烟囱 `#funnel` 烟雾向左上方飘散（相对气流向后），与右进一致。
- 舵轮 `#ships-wheel` 独立慢转（6s/圈），与螺旋桨相位/周期不同，不锁死。

## 2. Otter 相对载具的独立运动（≥2 处）

`#ferry-root` 整体做 4.2s 的 bob + 微倾。以下肢体/附肢周期与相位均不同，**未与船体锁死**：

| 元素 | 运动 | 周期 |
|------|------|------|
| `#otter-arm-wheel` | 肩关节旋转，操舵微调 | 2.8s |
| `#otter-arm-free` | 自由前肢指向前方（右） | 2.6s，相位相反 |
| `#otter-head` | 环视摆头 | 3.4s |
| `#otter-body` | 身体上下 bob | 2.1s（≠ 船体 4.2s） |
| `#otter-tail` | 尾巴摆动 | 1.9s |
| `#otter-ear-l/r` | 耳朵抖动 | 3.1s |
| `#otter-whiskers` | 胡须颤动 | 1.6s |

## 3. 背景视差（≥2 层，实际 5 层独立 + 船体）

由远到近：

1. **远云** `.layer-far-clouds` — 90s 循环，位移 −1200px（最慢）
2. **远岛** `.layer-islands` — 48s，位移 −900px（含灯塔）
3. **海鸟** `.layer-birds` — 36s，自带翅膀扇动
4. **闪点** `.layer-sparkle` — 28s
5. **中景波纹** `.layer-water-mid` — 22s
6. **前景浪** `.layer-water-near` — 14s（最快）

周期单调递减，构成清晰景深。

## 4. 资源与技术

- 单文件 HTML，CSS + SVG 内联。
- **零 CDN / 零框架 / 零网络请求**。
- 动画全部为 CSS `@keyframes` + `animation`，无 JS 依赖（可离线打开）。
- SVG `viewBox="0 0 1200 700"`，`preserveAspectRatio="xMidYMid slice"` 自适应。
