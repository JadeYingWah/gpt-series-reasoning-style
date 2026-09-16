# SVG005-otter-ferry · 核对记录 response.md

## 交付物

| 文件 | 状态 |
|------|------|
| `art.html` | 已创建，27 101 bytes |
| `notes.md` | 已创建（几何/运动自洽说明） |
| `response.md` | 本文件 |

## 验收清单逐项核对

### 1. `art.html` 存在且 ≥ 8KB — **PASS**

- 路径：`<实验根目录>\ab-longrun-300\SVG005-otter-ferry\A-skill\art.html`
- 实测大小：**27 101 bytes**（阈值 8 192）

### 2. 含 SVG 或 canvas 主体绘制 — **PASS**

- 存在 `<svg id="ferry-scene" viewBox="0 0 800 500" …>`
- 全场景由内联 SVG path / rect / circle / ellipse / line 绘制
- 无 `<canvas>`

### 3. 有动画（CSS 或 JS）— **PASS**

- 15 组 `@keyframes`：`drift-far/mid/near`、`shimmer`、`ferry-bob`、`spin-paddle`、`puff`、`otter-torso`、`steer-arm`、`wave-arm`、`tail-sway`、`head-look`、`ear-twitch`、`flag-flap`、`lantern-pulse`、`wake-slide`、`bird-glide`、`caption-in`
- 全部为 CSS 动画，无 JS

### 4. 两层以上背景/视差 — **PASS**

- `.layer-far` 80s（云 + 远山）
- `.layer-mid` 36s（岛屿 + 灯塔）
- `.layer-near` 14s（水面波纹）
- 三层均以 800px 无缝复制条带平移

### 5. 附肢与载具非完全同步锁死 — **PASS**

载具周期 6s；附肢独立：

| 附肢 | 周期 | 证据 class |
|------|------|-----------|
| 挥手手臂 | 1.4s | `.arm-wave` |
| 舵轮手臂 | 2.4s | `.arm-steer` |
| 尾巴 | 2.6s | `.otter-tail` |
| 躯干 | 1.8s | `.otter-torso` |
| 头 | 3.8s | `.otter-head` |
| 双耳 | 4.5s（右耳 +0.3s） | `.ear-l` / `.ear-r` |

满足「至少 2 处肢体/附肢与载具有相对运动」。

### 6. 无外部资源依赖 — **PASS**

自动化扫描结果：

| 检查 | 结果 |
|------|------|
| `src`/`href` 指向 `http(s)://` | 无 |
| `<link>` | 无 |
| `@import` | 无 |
| `<script src>` | 无 |
| `<img>` | 无 |
| `http(s)://` 出现次数 | **1**（`xmlns="http://www.w3.org/2000/svg"`，SVG 命名空间标识，非请求） |

### 7. 自洽说明存在 — **PASS**

见 `notes.md`：调色板、推进方向与明轮/尾迹/烟/旗一致性、附肢相位表、三层视差速比、reduced-motion 分支。

### 8. response 有证据或 UNVERIFIED — **PASS**

本文件即证据文档；无法自动化的视觉项见下方 UNVERIFIED。

## 自动化无法覆盖 → UNVERIFIED

以下项需用户在浏览器中打开 `art.html` 目视确认：

| ID | 项目 | 用户自验步骤 |
|----|------|-------------|
| V1 | 水獭与渡船**可辨认**（非抽象色块） | 打开 `art.html`，确认能一眼认出「有毛的四足动物 + 带舱/桨轮的船体」 |
| V2 | 明轮旋转视觉上推动向右（非看起来倒转） | 盯住桨轮 3 秒，确认桨叶从上方转向后方再入水，整体像向右推进 |
| V3 | 视差层次感自然（远慢近快不晕） | 浏览器窗口 ≥1000px 宽，观察远山几乎不动、波纹明显左移 |
| V4 | 挥手与操舵动作读得出来 | 观察左臂大幅上下挥、右臂扶舵小幅摆，二者不同步 |
| V5 | 无布局溢出 / 变形 | 375px 与 1440px 宽各看一眼，SVG 应铺满且不变形 |
| V6 | `prefers-reduced-motion` 下动画收敛 | 系统开启「减弱动态效果」后刷新，视差/烟应静止 |
| V7 | 整体审美不落「白底默认图标」 | 调色为黄昏青陶土色，非白底扁平 |

## 技术备注

- 单文件，无构建步骤，双击即开
- SVG `preserveAspectRatio="xMidYMid slice"`：任意视口比例下铺满并居中裁切
- 所有动画 CSS-only；`prefers-reduced-motion` 有完整分支
