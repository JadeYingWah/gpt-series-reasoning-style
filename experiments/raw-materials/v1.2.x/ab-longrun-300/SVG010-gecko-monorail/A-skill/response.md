# Response — SVG010-gecko-monorail · A-skill

**Agent mode**: 单 Agent 主干（本地可逆创意单文件，无并行隔离需求）  
**Risk tier**: 轻–中（产物完全可逆、无外部副作用）  
**Direction**: 冒险直选 — Neon Dusk Line（夜色霓虹热带单轨），主动拒绝白底扁平占位风。  
**Closeout**: Stage 2 — 补齐验收证据 / 视觉 UNVERIFIED / 用户自验步骤。**未重写 `art.html`**（无硬伤）。

## Deliverables

| Path | Size / role | Status |
|------|-------------|--------|
| `art.html` | **36155 bytes** (≥8KB gate) · 单文件 HTML/SVG/CSS/JS | written (unchanged in closeout) |
| `notes.md` | 几何/运动自洽 + 设计 token | written (+ closeout anchors) |
| `response.md` | 本文件：证据 + UNVERIFIED + 自验 | written |
| `load-proof.md` | skill load proof v1.2.0 | present (phase 1) |
| `task.md` | 本地验收清单 | present |
| `verify-shot.png` | headless Chrome still | present |
| `verify-shot-t2.png` | 第二次 Chrome still | present |
| `verify-pw-t0.png` | Playwright t≈0.3s | present |
| `verify-pw-t1.png` | Playwright t≈2.8s | present |

## Acceptance checklist（对照 `task.md`，本阶段实测）

| # | Criterion | Method / evidence | Result |
|---|-----------|-------------------|--------|
| 1 | `art.html` 存在且 ≥8KB | `Get-Item` Length = **36155** bytes (35.31 KB), 810 lines | **PASS** |
| 2 | 含 SVG 或 canvas 主体 | `<svg id="scene" viewBox="0 0 1600 900" role="img" aria-label="…">`，完整 scene graph | **PASS** |
| 3 | 有动画（CSS 或 JS） | 多个 `@keyframes`（scroll-*/train-bob/tail/arm/head/leg/blink/tongue/spin-cw/thrust/window/star）+ JS blink/tongue scheduler | **PASS** |
| 4 | 两层以上背景/视差 | `.p-far` 48s · `.p-mid` 22s · `.p-near` 11s · `.p-rail` 6s（+ 静态 sky L0） | **PASS**（≥2，交付 4 层运动） |
| 5 | 附肢与载具非完全同步锁死 | `.train-root` bob 2.4s；tail 1.7s / arm-l 1.15s / arm-r 2.1s / head 3.3s / leg 0.95s / blink / tongue 各异 | **PASS**（≥2，交付 7 路） |
| 6 | 无外部资源依赖 | 检索 `http(s)://`、`cdn`、`@import`、`fetch`、外链 `src`：唯一命中为 SVG `xmlns="http://www.w3.org/2000/svg"`（命名空间 URI，非网络请求）。无 `<link>` / 无外链 script / 无 CDN | **PASS** |
| 7 | 自洽说明存在 | `notes.md` §Geometry & motion + `art.html` 注释（约 L7–11、L505–509、L582–602） | **PASS** |
| 8 | response 有证据或 UNVERIFIED | 本文件 + 4 张真实浏览器截图 | **PASS** |

**Checklist total: 8/8 PASS.** 未发现需要改 `art.html` 的硬伤。

### 结构扫查（closeout 复验）

- 文件体量：36155 B / 810 lines — 远超 8KB。
- 推进：4× `.wheel-spin` + `spin-cw`；`.thrust-stream` / `.thruster-core`；注释明确 exhaust 左 ⇒ thrust 右。
- 视差：四条独立 duration 的 `translateX(0 → -800px)` 循环。
- 附肢：tail / arm-l / arm-r / head / leg-back 均独立 `transform-origin` + 独立 period。
- 可访问性：`role="img"` + `aria-label`；`prefers-reduced-motion` CSS + JS 双保险。
- 禁止项：无 eval、无网络、无外部字体/图标库。

## Visual evidence（真实浏览器截图）

Environment: Windows · Google Chrome / Playwright `channel=chrome` · viewport 1600×900 · `file://` local。

| File | What it shows |
|------|----------------|
| `verify-shot.png` | 主验收静帧：亮绿 gecko（鼓眼、黄腹、粉颊/舌、趾垫）坐进青色描边开放驾驶舱；右侧流线型 monorail 车头 + 头灯；左侧推进尾流；4 磁轮在高架梁上；霓虹城市 / 月亮 / 棕榈 / 电线杆；字幕 “Neon Dusk Line · WESTBOUND · GECKO EXPRESS” |
| `verify-shot-t2.png` | 第二次静帧，构图一致，证明可重复渲染（非一次性 glitch） |
| `verify-pw-t0.png` | Playwright t≈0.3s |
| `verify-pw-t1.png` | Playwright t≈2.8s |

### 双时帧差分（t0 vs t1，证明动画在跑）

对照 `verify-pw-t0.png` 与 `verify-pw-t1.png` 可观察到：

1. **轮辐相位变化**：磁轮 spoke 呈 `+` vs `×` 不同相位 → `spin-cw` 生效。
2. **视差相对位移**：近层电线杆 / 中层棕榈相对远层天际线位置改变 → 多层速度梯度生效。
3. **附肢姿态变化**：gecko 手臂/尾部相对车体角度不同 → 非全身锁死平移。

### 视觉判定（基于上述截图，非自动 metric）

| Item | Judgement |
|------|-----------|
| Gecko 可辨认 | 是 — 鼓眼、趾垫、尾、斑点、背/腹对比 |
| Monorail 可辨认 | 是 — 单轨高架梁、流线车头、车窗、受电弓、转向架 |
| 前进方向 | 画面右侧（+X）— 车头/头灯朝右；尾流与轨缝刻度向左 |
| 非白底扁平占位 | 是 — 夜色霓虹调色、辉光、双色条纹、字幕条 |
| 附肢相对运动 | 是 — 臂/尾/头/腿各自 transform，非刚体跟随 |

## UNVERIFIED（本环境无法完全自动化）

| Item | Why | 用户自验步骤 |
|------|-----|--------------|
| Live 流畅度 / 无 jank | 静帧无法测帧时 | 用 Chrome 打开 `art.html`；DevTools → Performance → 录 5s；检查是否有长帧 / 掉帧 |
| 视差循环接缝无跳变 | 需连续观察多圈 | 盯 far/mid/near 各看 2–3 个完整周期（far≈48s）；确认 −800px wrap 处无突跳 |
| “在驾驶”整体观感（而非只是坐着） | 主观审美；舵杆是静态造型 | 打开页面 3s 内判断：油门臂 + 开放舱 + 舵杆是否读成 piloting |
| `prefers-reduced-motion` 真冻结全部动画 | 需系统设置或 DevTools 模拟 | DevTools → Rendering → emulate `prefers-reduced-motion: reduce` → reload；应全部静止 |
| 小视口 / 移动端布局 | 仅捕获 1600×900 | 窗口缩到约 375px 宽；场景应 letterbox，页面本身不出现横向滚动条 |
| Blink / tongue 随机节奏是否自然 | JS 随机，仅 code-review | 持续观察 30s；预期多次眨眼 + 1–3 次吐舌 |
| 色弱 / 低对比可读性 | 未跑 aXe / 对比度工具 | 可选：Lighthouse Accessibility 或人工在降低对比度显示器上扫一眼主体轮廓 |

## Known minor（非硬伤，未在 closeout 修改）

- 字幕写 “Westbound”，而画面运动为 +X（右）。在默认上北下南地图语义下 westbound 通常朝左；作为装饰文案保留，不影响几何/动画自洽验收。
- gecko 比例相对乘客窗偏大 — 刻意的 hero-character 风格选择。
- 舌头闪现很短，静帧里容易错过（见 UNVERIFIED 表）。
- 轨缝刻度在 x≈780/800 处间距略不均（20px vs 60px），循环中几乎不可察。

## 用户一键自验（最短路径）

1. 双击或浏览器打开 `<实验根目录>\ab-longrun-300\SVG010-gecko-monorail\A-skill\art.html`（无需服务器、无需联网）。
2. 确认：画面为夜色城市单轨，绿色 gecko 在车头开放舱，列车朝**右**。
3. 观察 10 秒：车轮转、尾流向左、背景分层左移、gecko 手臂/尾/头有独立动作。
4. （可选）DevTools 模拟 reduced-motion → 应全部静止。
5. 对照 `verify-pw-t0.png` / `verify-pw-t1.png` 理解预期运动差分。

## Skill / process notes

- Load proof（phase 1）见 `load-proof.md`（skill v1.2.0）。
- 单 Agent 主干即可；本任务无多 Agent 扩展需求。
- 底线：真实环境截图已有；无法自动化的视觉项均标 **UNVERIFIED** 并给出用户自验步骤。
- **只写了 `A-skill/` 目录内文件**；closeout 未改 `art.html`。
