# Response · SVG015 seahorse × cableway（A-skill）

## 交付物

| 文件 | 状态 | 大小 |
|------|------|------|
| `art.html` | 已写入 | 24683 bytes (≈24.1 KB) |
| `notes.md` | 已写入 | 几何/运动自洽说明 |
| `response.md` | 本文件 | 证据与核对记录 |

工作目录仅含本任务文件；未读写目录外项目文件（skill 本体只读加载见 load-proof）。

## 验收清单核对

| 项 | 结果 | 证据 |
|----|------|------|
| `art.html` 存在且 ≥8KB | **PASS** | 24683 bytes |
| 含 SVG 或 canvas 主体绘制 | **PASS** | 根元素 `<svg class="scene" viewBox="0 0 1200 700">` |
| 有动画（CSS 或 JS） | **PASS** | 多个 `@keyframes`（`scrollX` / `spinCW` / `finFlap*` / `tailCurl` / `cabinBob` / `rise` / `drift` / `pulseGlow`） |
| 两层以上背景/视差 | **PASS** | `.scroll-far` 28s · `.scroll-mid` 14s · `.scroll-near` 7s，周期不同 ⇒ 相对速度不同 |
| 附肢与载具非完全同步锁死 | **PASS** | 胸鳍 `.fin-r` 0.9s、背鳍 `.fin-l` 1.15s、尾 `.tail-wave` 1.8s、头冠 `.crest-sway` 1.6s；舱体 `.bob` 2.4s，周期/原点均分离 |
| 无外部资源依赖 | **PASS** | 静态扫描无 `http(s)://`、无 `src` 外链、无 CDN/`@import`/`fetch`；全内联 |
| 自洽说明存在 | **PASS** | `notes.md` + HTML 头注释（滑轮 CW ↔ 右移、三层视差、附肢独立） |
| response 有证据或 UNVERIFIED | **PASS** | 本文件；视觉项见下 |

## 已用工具核验（可自动化）

检测方法：PowerShell 读文件字节数 + 正则匹配关键结构（`<svg`、`@keyframes`、`animation:`、`scroll-far|mid|near`、`class="fin-r|fin-l|tail-wave"`、`spinCW`、外链模式）。覆盖面：文件体积、结构存在性、动画类绑定、三层视差、独立附肢类名、无外链。**未**在真实浏览器中渲染截图。

几何/方向自洽（代码级推理，非渲染观察）：

1. 背景层 `translateX(0 → -1200px)` ⇒ 世界左移 ⇒ 载具相对右进。
2. 滑轮 `rotate(360deg)` 顺时针；绳在夹绳器下向左走 ⇒ 车向右，旋转方向一致。
3. 双 tile（`x=0` 与 `x=1200`）与 scroll 距离 1200px 对齐，循环无缝。

## UNVERIFIED（本环境无法自动化的视觉项）

以下项需人工打开浏览器确认，**不得**当作已验收：

1. **主体可辨认度**：远景一眼是否能看出「海马」与「索道/缆车」。
2. **视差是否肉眼可感**：三层速度差是否清晰、近景是否过快闪烁。
3. **附肢动画是否自然**：鳍扇动/尾卷曲是否像游泳而非抽搐；是否明显独立于车厢。
4. **构图与可读性**：车厢是否被近景遮挡；海马在车窗内是否完整可见。
5. **reduce-motion 分支**：系统开启「减弱动态效果」后是否静止且仍可读。
6. **响应式裁切**：窄屏/超宽屏 `preserveAspectRatio="xMidYMid slice"` 是否裁掉主体。

### 用户自验步骤

```text
1. 用 Chrome / Edge / Firefox 直接打开 art.html（无需服务器）。
2. 观察 5 秒：
   - 海马朝右，车厢朝右，背景向左流过（前进感向右）。
   - 两只滑轮顺时针转。
   - 胸鳍/背鳍在扇，尾部在卷，且与车厢摇摆不同步。
3. 切换系统「设置 → 辅助功能 → 视觉效果 → 动画效果」为关，
   刷新页面：应全部静止，场景仍完整。
4. 窗口缩放到 ~375px 宽与全屏 16:9：主体不消失、不裁切到只剩脚。
5. DevTools → Network：刷新后无第三方请求。
```

## 方向说明

本次方向为**冒险直选**（深海生物发光索道峡谷）：创意可逆、本地单文件、无外部副作用；按 skill 创意豁免跳过方向确认，范围与落盘路径按 task.md 锁定。

## 残留风险

- SVG 内 CSS `transform-box: fill-box` 需较新浏览器（2020+）；极旧浏览器滑轮原点可能偏移，不影响静态可读。
- 视差为 CSS 动画，无 JS 备份；若用户强制禁用 CSS 动画，场景静止但仍成立。
