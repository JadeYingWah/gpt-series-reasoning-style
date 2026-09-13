# response.md — 实际核对记录

## 验收清单对照

| 项 | 结果 | 证据 |
|----|------|------|
| `art.html` 存在且 ≥8KB | **VERIFIED** | 文件存在，`Length = 28081` 字节（PowerShell `Get-Item`） |
| 含 SVG 或 canvas 主体绘制 | **VERIFIED** | 主体为 `<svg id="scene" viewBox="0 0 1000 600">`，含 cabin、beetle、山脉、缆索等完整矢量场景 |
| 有动画（CSS 或 JS） | **VERIFIED** | CSS：`@keyframes` 覆盖 sheave 旋转、腿部步进、触角、星空闪烁、飘雪、车厢摆动；JS：`requestAnimationFrame` 视差循环 |
| 两层以上背景/视差 | **VERIFIED** | 至少 6 层：stars / clouds / far-peaks / mid ridge+trees / near rocks / snow，速度系数 0.04→0.85；见 `notes.md` 表 |
| 附肢与载具非完全同步锁死 | **VERIFIED** | 前腿 1.1s、中腿 0.7s、后腿 0.85s、触角 1.6s 与车体 advance/sway 周期不同；CSS 类独立于 `#car-rig` transform |
| 无外部资源依赖 | **VERIFIED** | HTML 内无 `http`、`https`、`src=` 外链、`@import`、`fetch`；渐变/滤镜均在 `<defs>` |
| 自洽说明存在 | **VERIFIED** | 本目录 `notes.md` + `art.html` 头部注释 |
| response 有证据或 UNVERIFIED | **VERIFIED** | 本文件 |

## 几何/运动自洽核对

| 项 | 结果 | 说明 |
|----|------|------|
| 车轮/滑轮旋转与前进方向一致 | **UNVERIFIED** | 代码层：`spin-cw` 为顺时针，车朝 +X；**需用户目视**确认轮缘切向与「向右」直觉一致（镜像/透视误读无法在无头环境断言） |
| beetle 可辨认 | **UNVERIFIED** | 绘有鞘翅、前胸背板、触角、六足、大颚；**需用户目视**是否达到「可辨认」门槛 |
| cable-car 可辨认 | **UNVERIFIED** | 悬挂吊臂、主缆、塔架、吊舱形体完整；**需用户目视** |
| 背景视差「感觉」正确 | **UNVERIFIED** | 数值层已设不同速度；**需用户打开页面**确认深度错觉与无跳帧 |
| 白底 + 默认扁平占位图标 | **VERIFIED（排除）** | 深色渐变夜景，非白底；图形为手绘 path/ellipse，非 placeholder 图标 |

## 无法自动化的视觉项 — 用户自验步骤

1. 用浏览器打开 `art.html`（双击或 `start art.html`）。
2. 确认画面非空白，能看到：橙色吊舱、绿色甲虫驾驶者、雪山夜空、缆索塔架。
3. 观察 3–5 秒：
   - 舱底三个圆轮/滑轮在**顺时针**转；
   - 甲虫前腿在抓握/推拉操纵杆，中后腿有交替步态，触角在摆动——与车厢平移**不同步**；
   - 远山几乎不动，近景岩石/飘雪移动更快。
4. 若任一项观感不达标，反馈具体层 ID 或元素 class，便于下一迭代调参。

## 环境与限制

- 未在真实浏览器中截图（当前为无头 CLI 写文件流程）。
- 文件大小、源码结构、依赖扫描、动画定义存在性已用文本/文件系统工具核实。
- 视觉美学与「可辨认」标准依赖人工目视。

## 交付文件

- `art.html`
- `notes.md`
- `response.md`
- （阶段 1 已有）`task.md`、`load-proof.md` — 未改动
