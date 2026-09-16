# Response · SVG016 moth × gondola（A-skill）

## 交付物

| 文件 | 状态 | 说明 |
|------|------|------|
| `art.html` | 已写入并修复 1 处硬伤 | 43559 bytes |
| `notes.md` | 已写入 | 设计 token、几何/运动自洽、识别性检查 |
| `load-proof.md` | 阶段1产物 | skill 1.2.0 加载证明 |
| `response.md` | 本文件 | 验收证据 + 视觉 UNVERIFIED + 自验步骤 |

工作目录仅含本任务 4 个文件；未读写目录外项目文件（skill 本体只读加载见 load-proof）。

## 硬伤修复记录

| 问题 | 位置 | 修复 |
|------|------|------|
| `.oar-blade` 绑定 `animation: oarBlade`，但 `@keyframes` 名写成 `oar-blade`（连字符），名称不匹配 ⇒ 桨叶独立入水角度动画**不会生效** | art.html L213 / L215 | 将 `@keyframes oar-blade` 改为 `@keyframes oarBlade`，与 animation 属性一致 |

其余结构未改动。修复后文件 43559 bytes。

## 验收清单核对

| 项 | 结果 | 证据 |
|----|------|------|
| `art.html` 存在且 ≥8KB | **PASS** | 43559 bytes |
| 含 SVG 或 canvas 主体绘制 | **PASS** | 根元素 `<svg class="scene" viewBox="0 0 1200 700" preserveAspectRatio="xMidYMid slice">` |
| 有动画（CSS 或 JS） | **PASS** | 17 组 `@keyframes`：`scrollX` / `hullBob` / `mothBob` / `wingFlapL` / `wingFlapR` / `antTwitchL` / `antTwitchR` / `legFront` / `legMid` / `legRear` / `abdomenSway` / `oarStroke` / `oarBlade` / `ripple` / `flicker` / `halo` / `reflWob`；全部有对应 `animation:` 绑定（已交叉核对无 missing/orphan） |
| 两层以上背景/视差 | **PASS** | `.scroll-far` 32s · `.scroll-mid` 16s · `.scroll-near` 8s；每层 SVG 内双 tile（0 与 +1200）对齐 `translateX(-1200px)` |
| 附肢与载具非完全同步锁死 | **PASS** | 翅 0.72s、触角 1.4s/1.7s、足 1.9/2.3/2.05s、腹 2.8s、moth-bob 2.1s；船体 hull-bob 2.6s；周期与 transform-origin 均分离 |
| 无外部资源依赖 | **PASS** | 唯一 `http://` 为 SVG 命名空间 `xmlns="http://www.w3.org/2000/svg"`（非网络请求）；无 `src=` / `href=` / CDN / `@import` / `fetch`；CSS/SVG 全内联 |
| 自洽说明存在 | **PASS** | `notes.md` 全文 + art.html 头注释（桨橹左后推水↔右进、三层视差、附肢独立） |
| response 有证据或 UNVERIFIED | **PASS** | 本文件；视觉项见下 |

## 已用工具核验（可自动化）

检测方法：文件字节数 + 正则交叉核对 `animation:` 与 `@keyframes` 名称、关键 class 存在性、外链模式扫描。覆盖面：体积、结构、动画绑定完整性、三层视差、独立附肢类名、无外链。**未**在真实浏览器中渲染截图。

几何/方向自洽（代码级推理，非渲染观察）：

1. 背景层 `translateX(0 → -1200px)` ⇒ 世界左移 ⇒ 载具相对右进。
2. ferro di prua 在 x≈810 指向右侧 ⇒ 船头朝右。
3. 桨杆从 forcola（x≈670）向左后方（x≈480）入水 ⇒ 向左推水 ⇒ 船向右。方向一致。
4. 双 tile（`x=0` 与 `x=1200`）与 scroll 距离 1200px 对齐，循环无缝。
5. 尾流涟漪在船左后方，强化前进方向。
6. 月亮与水面反光为固定元素（世界参考系），不随视差滚动。

## UNVERIFIED（本环境无法自动化的视觉项）

以下项需人工打开浏览器确认，**不得**当作已验收：

1. **主体可辨认度**：远景一眼是否能看出「飞蛾」与「贡多拉」。
2. **视差是否肉眼可感**：三层速度差是否清晰、近景是否过快闪烁。
3. **附肢动画是否自然**：翅扇动/触角摇/足抓握/腹摆是否像活物而非抽搐；是否明显独立于船体。
4. **桨橹动画**：桨入水角度是否自然；桨叶 `oarBlade`（已修复 keyframes 名）是否随杆联动。
5. **构图与可读性**：飞蛾是否被船体或近景遮挡；翅展开是否超出画面。
6. **reduce-motion 分支**：系统开启「减弱动态效果」后是否静止且仍可读。
7. **响应式裁切**：窄屏/超宽屏 `preserveAspectRatio="xMidYMid slice"` 是否裁掉主体。
8. **月光氛围**：月亮、灯笼光晕、水面反射是否协调不刺眼。

### 用户自验步骤

```text
1. 用 Chrome / Edge / Firefox 直接打开 art.html（无需服务器）。
2. 观察 5 秒：
   - 飞蛾朝右（头/触角/喙在右），船头 ferro 在右，背景向左流过（前进感向右）。
   - 双翅在扇，触角在摇，三对足有微动，腹部有摆。
   - 以上均与船体摇摆不同步。
   - 桨杆在船左后方划水，桨叶有独立入水角度变化。
3. 切换系统「设置 → 辅助功能 → 视觉效果 → 动画效果」为关，
   刷新页面：应全部静止，场景仍完整可读。
4. 窗口缩放到 ~375px 宽与全屏 16:9：主体不消失、不裁切到只剩船底。
5. DevTools → Network：刷新后无第三方请求。
```

## 方向说明

本次方向为**冒险直选**（月夜威尼斯运河贡多拉）：创意可逆、本地单文件、无外部副作用；按 skill 创意豁免跳过方向确认，范围与落盘路径按任务锁定。

## 残留风险

- SVG 内 CSS `transform-box: fill-box` 需较新浏览器（2020+）；极旧浏览器翅/触角原点可能偏移，不影响静态可读。
- 视差为 CSS 动画，无 JS 备份；若用户强制禁用 CSS 动画，场景静止但仍成立。
- 左右翅使用同一周期 0.72s 但 keyframe 相位不同；若浏览器对 fill-box 原点解析差异大，扇动幅度可能不均。
