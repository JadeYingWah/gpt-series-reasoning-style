# response.md — SVG003-crab-snowplow · 核对记录

工作目录：`<实验根目录>\ab-longrun-300\SVG003-crab-snowplow\B-noskill`  
臂：B（noskill）  
核对方式：本地文件读取 + PowerShell/Grep 静态检查（未启动浏览器）

## 验收清单

| # | 项 | 结果 | 证据 |
|---|-----|------|------|
| 1 | `art.html` 存在且 ≥ 8KB | **PASS** | 文件长度 **43356 bytes**（约 42 KB） |
| 2 | 含 SVG 或 canvas 主体绘制 | **PASS** | `<svg class="scene" viewBox="0 0 1200 700" ...>` 内联完整场景 |
| 3 | 有动画（CSS 或 JS） | **PASS** | 大量 `@keyframes`：`spinCW` / `bodyBob` / `plowJitter` / `eyeWobble*` / `clawGrip*` / `legSwing*` / `snowFall` / `midScroll` / `farScroll` / `groundDrift` / `beaconPulse` 等 |
| 4 | 两层以上背景/视差 | **PASS** | `layer-stars`、`layer-far`（36s）、`layer-mid`（14s）、`layer-ground`（3.2s）、`layer-fore`（2.0s）共 5 层位移/闪变 |
| 5 | 附肢与载具非完全同步锁死 | **PASS** | 车身 `bodyBob` 0.55s；眼柄 0.85/1.1s；螯 0.62/0.72s；步足 0.75–1.05s；触角 1.25–1.4s — 周期与相位均独立 |
| 6 | 无外部资源依赖 | **PASS** | Grep `https?://` 仅命中 SVG namespace（`http://www.w3.org/2000/svg`）两处，**非网络资源**；无 link/script src/font/fetch |
| 7 | 自洽说明存在 | **PASS** | 本目录 `notes.md` + `art.html` 顶部 HTML 注释同步说明 |
| 8 | response 有证据或 UNVERIFIED | **PASS** | 本文件；纯视觉项见下表 |

## 无法自动化的视觉项

| 项 | 状态 | 用户自验步骤 |
|----|------|--------------|
| crab 与 snowplow 是否“可辨认”（造型识别度） | **UNVERIFIED** | 用浏览器打开 `art.html`：应看到橙红色螃蟹坐在青蓝色卡车驾驶室，右前方黄色雪铲；车轮在转 |
| 前进方向是否“感觉正确”（轮转 vs 地面纹理 vs 车头朝向） | **UNVERIFIED** | 打开后观察：车头/铲在右；车轮顺时针；地面雪纹与轮胎痕迹向左移；排气与抛雪向左后 |
| 附肢相对运动是否肉眼明显、非全局锁死 | **UNVERIFIED** | 盯住驾驶室：眼柄左右异相摆动；螯夹方向盘微动；露在车外的步足相位错开摆动；车身另有轻微颠簸 |
| 视差景深是否成立 | **UNVERIFIED** | 对比远山（极慢）、中景树（中速）、前景雪丘（较快）的相对滑动速度 |
| 风格是否避免“白底 + 默认扁平占位” | **UNVERIFIED** | 夜色极光天空、渐变雪原、工业质感车体、着色螃蟹；无纯白底占位图标 |
| 动画是否流畅、无错位/穿模 | **UNVERIFIED** | 全屏打开至少 5 秒；观察轮辐条旋转连续、雪喷粒子不卡死、螃蟹不穿出车壳外轮廓 |

## 建议自验命令（用户侧）

```text
start "" "<实验根目录>\ab-longrun-300\SVG003-crab-snowplow\B-noskill\art.html"
```

或任意现代浏览器直接打开该路径。

## 文件清单

- `art.html` — 主交付（单文件场景）
- `notes.md` — 几何/运动自洽说明
- `response.md` — 本核对记录
- `task.md` — 任务原文（未修改）
