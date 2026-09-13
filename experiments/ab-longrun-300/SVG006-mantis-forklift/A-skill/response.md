# 验收汇报 · SVG006-mantis-forklift（A-skill）

## 交付物

| 文件 | 说明 |
|------|------|
| `art.html` | 单文件 HTML/SVG 创意实现（31852 字节） |
| `notes.md` | 几何/运动自洽说明 |
| `shot-verify.png` | headless Chrome 截图证据（cache-bust 后重拍，约 205 KB） |
| `load-proof.md` | 阶段1 skill 加载证明 |
| `response.md` | 本文件 |

## 验收清单（逐项证据）

- [x] **`art.html` 存在且 ≥ 8KB**  
  实测 31852 字节（`Get-Item Length`）。

- [x] **含 SVG 或 canvas 主体绘制**  
  文内单一 `<svg class="scene" viewBox="0 0 960 540">`，含 defs 渐变、门架/车轮/螳螂分组（约 L297 起）。

- [x] **有动画（CSS 或 JS）**  
  纯 CSS `@keyframes`：轮旋、三层视差、附肢、灯、排气等（约 L89–248）；无外部 JS。

- [x] **两层以上背景/视差**  
  `.layer-far` / `.layer-mid` / `.layer-near` 三层，速度序 far < mid < near（42s / 20s / 8s）。详见 `notes.md` §3。

- [x] **附肢与载具非完全同步锁死**  
  轮 0.5s；触角 1.7s / 2.05s；前肢 0.85s / 1.1s；头 3s；腹 1s 等，周期均独立于车轮与 `rigBob`。详见 `notes.md` §4。

- [x] **无外部资源依赖**  
  全文无 `http(s)://`、无 `src=` 外链、无 `@import`、无 CDN；徽章亦标注 `SVG · CSS ANIM · NO CDN`。

- [x] **自洽说明存在**  
  `art.html` 内注释（L288–296）+ 本目录 `notes.md`。

- [x] **response 有证据或 UNVERIFIED**  
  见本文件上表与下节。

## 视觉项 · UNVERIFIED（需用户在浏览器自验）

以下**不能**仅靠源码或单张静态截图完全证明；本环境未做实时动画测量。`shot-verify.png` 为夜间巷道场景，螳螂 + 黄色叉车 + 货箱可辨认、朝向右、FRAGILE 标签完整、高对比轮毂可见；但 headless `--virtual-time-budget` 对连续 CSS 动画推进有限，**不作为动画流畅度的充分证据**。

本环境 Playwright CLI 启动失败（`ChildProcess.kill`），已改用 Chrome headless 截图，**不以 Playwright 结果冒充**。

### 用户自验步骤

1. 用 Chrome / Edge / Firefox **直接打开** `art.html`（双击或拖入窗口），勿用“禁用 CSS”的阅读模式。
2. **车轮**：盯住前/后轮辐条，确认**顺时针**旋转；与车头朝右、背景左移一致。
3. **附肢**：观察触角两根**不同步**摆动；前肢相对门架/车体有抓握或调整动作；头部有缓慢环顾、腹部有轻微弹跳——确认不是整车刚体平移。
4. **视差**：对比远楼、中景货架/吊灯、近地色带的滑动速度，应为**远慢近快**。
5. **载荷**：货箱在叉上有轻微 jiggle，门架轻微 sway，不穿模、不脱离货叉。
6. **系统减动效**（可选）：系统开启“减少动态效果”后刷新，动画应停，构图仍可读。
7. **窄窗/缩放**（可选）：改窗口比例，`slice` 裁切下主体仍大致居中可读。

若 2–5 任一明显违和（轮倒转、附肢锁死、只有一层背景、白底占位感），请反馈；当前包按静态源码与截图判定结构项通过，动画感官以你的浏览器为准。

## 本环境实测命令摘要

```text
html_bytes=31852
external_hits=0   # Select-String 模式 https?://|cdn\.|unpkg|jsdelivr|googleapis|@import|fetch\(
svg_tags=1
keyframes=23
shot-verify.png ≈ 209872 bytes
Chrome: --headless=new --disable-gpu --window-size=1280,720 --screenshot=... --virtual-time-budget=600
```

视觉已用 `shot-verify.png` 肉眼核对：叉车（黄体/M-07/门架/货叉/木箱/警灯）与螳螂（三角头/红复眼/触角/镰刀前足/分节腹）均可辨认；非白底扁平占位。

## 已知边界

- 未在此会话做 headless 录屏帧差 / 性能 profiling。
- 未验证 IE/极旧浏览器；目标为现代 Chromium / Firefox / WebKit。
- `load-proof.md` 为流程阶段文档，与画面验收无关。
- 本地方向为**冒险直选**（夜间霓虹工业插画）；若审美不合可要求换向重做。
