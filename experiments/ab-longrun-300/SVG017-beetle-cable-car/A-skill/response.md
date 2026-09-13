# response.md — SVG017 实际核对记录

## 交付物

| 文件 | 状态 | 大小 |
|------|------|------|
| `art.html` | 已写入 | **31850 bytes** (≈31.1 KB) |
| `notes.md` | 已写入 | 几何/运动自洽说明 |
| `response.md` | 本文件 | 证据与核对记录 |
| `task.md` | 已自建 | 阶段 1 无外部 task.md，按臂协议自建 brief |

工作目录仅含本任务文件；未读写目录外项目文件（skill 本体只读加载见 load-proof）。

## 验收清单核对

| 项 | 结果 | 证据 |
|----|------|------|
| `art.html` 存在且 ≥8KB | **VERIFIED** | 31850 bytes（PowerShell `Get-Item`） |
| 含 SVG 或 canvas 主体绘制 | **VERIFIED** | `<svg class="scene" id="scene" viewBox="0 0 1200 700">`，完整矢量场景 |
| 有动画（CSS 或 JS） | **VERIFIED** | 15 个 `@keyframes`：`scrollX` / `cabinSway` / `cabinBob` / `spinCW` / `foreGrab` / `midStep` / `hindStep` / `antWave` / `mandible` / `elytraPulse` / `headBob` / `sunPulse` / `leafDrift` / `headlampFlicker` / `towerLamp` |
| 两层以上背景/视差 | **VERIFIED** | 5 层滚动：sky 60s / far 32s / mid 16s / cable 12s / near 8s；周期不同 ⇒ 速度不同 |
| 附肢与载具非完全同步锁死 | **VERIFIED** | 前腿 1.05s、中腿 0.72s、后腿 0.88s、触角 1.55s、大颚 1.35s、头 1.9s；舱体 sway 3.2s + bob 2.4s；transform-origin 均分离 |
| 无外部资源依赖 | **VERIFIED** | 扫描 `https?://`、`@import`、`fetch(`、`<script src`、`<link ` → **NONE** |
| 自洽说明存在 | **VERIFIED** | 本目录 `notes.md` + `art.html` 头部注释 |
| response 有证据或 UNVERIFIED | **VERIFIED** | 本文件 |

## 已用工具核验（可自动化）

检测方法：PowerShell 读文件字节数 + `Select-String` 正则匹配关键结构。

覆盖面：

1. 文件体积 31850 ≥ 8192。
2. 根元素 `<svg` 存在。
3. `@keyframes` 计数 15。
4. 五层视差 class 定义与绑定均存在（`.scroll-sky/far/mid/near/cable`）。
5. `class="sheave` 出现 15 次（吊臂双滑轮 + 底盘三轮，含子线段）。
6. 附肢 class 绑定 12 处（leg-fore/mid/hind、antenna、mandible、elytra、beetle-head）。
7. `prefers-reduced-motion` 分支存在。
8. 外部资源模式匹配为空。

**未**在真实浏览器中渲染截图。

## 几何/方向自洽（代码级推理，非渲染观察）

1. 背景层 `translateX(0 → -1200px)` ⇒ 世界左移 ⇒ 载具相对右进。
2. 滑轮 `rotate(360deg)` 顺时针；车朝 +X ⇒ 旋转方向一致。
3. 双 tile（`x=0` 与 `x=1200`）与 scroll 距离 1200px 对齐，循环无缝。
4. 车头导流鼻、前灯光锥、朝右眼位/触角指向均在 +X 侧。
5. 尾旗向 −X 弯折，符合相对风阻。

## UNVERIFIED（本环境无法自动化的视觉项）

以下项需人工打开浏览器确认，**不得**当作已验收：

1. **主体可辨认度**：远景一眼是否能看出「甲虫」与「缆车」。
2. **视差是否肉眼可感**：五层速度差是否清晰、近景是否过快。
3. **附肢动画是否自然**：腿部步态/触角摆动是否像驾驶而非抽搐；是否明显独立于车厢。
4. **滑轮转向直觉**：顺时针是否与「向右」的肉眼直觉一致（镜像/透视误读无法在无头环境断言）。
5. **构图与可读性**：甲虫是否被窗棂/舱体遮挡；前灯光锥是否过曝。
6. **reduce-motion 分支**：系统开启「减弱动态效果」后是否静止且仍可读。
7. **响应式裁切**：窄屏/超宽屏 `preserveAspectRatio="xMidYMid slice"` 是否裁掉主体。

### 用户自验步骤

```text
1. 用 Chrome / Edge / Firefox 直接打开 art.html（无需服务器，双击即可）。
2. 观察 5 秒：
   - 甲虫朝右，吊舱车头朝右，背景向左流过（前进感向右）。
   - 吊臂与舱底滑轮在顺时针转。
   - 前腿在抓握操纵杆，中后腿有交替步态，触角在摆动——与车厢摇摆不同步。
   - 远山几乎不动，近景岩坡/灌木移动更快。
3. 切换系统「设置 → 辅助功能 → 视觉效果 → 动画效果」为关，
   刷新页面：应全部静止，场景仍完整可读。
4. 窗口缩放到 ~375px 宽与全屏 16:9：主体不消失、不裁切到只剩脚。
5. DevTools → Network：刷新后无第三方请求。
```

## 方向说明

阶段 1 无 `task.md`，按臂协议自建 brief：「甲虫驾驶缆车朝右」。创意方向直选 **暮光金秋峡谷索道**，与同题 SVG008（夜雪）在时段、色板、视差实现上均区分。创意可逆、本地单文件、无外部副作用；范围与落盘路径锁定在 `A-skill/`。

## 残留风险

- SVG 内 CSS `transform-box: fill-box` 需较新浏览器（2020+）；极旧浏览器滑轮/附肢原点可能偏移，不影响静态可读。
- 视差为纯 CSS 动画，无 JS 备份；若用户强制禁用 CSS 动画，场景静止但仍成立。
- 甲虫绘制在窗玻璃之上（卡通可读性优先）；若要求严格遮挡关系，可在窗上再叠一层半透明玻璃层。
- 未做真实浏览器视觉回归；美学与「可辨认」标准依赖人工目视。

## 交付文件

- `art.html`
- `notes.md`
- `response.md`
- `task.md`（自建 brief）
- （阶段 1 已有）`load-proof.md` — 未改动
