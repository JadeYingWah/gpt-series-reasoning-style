# Response · SVG018-owl-subway · 阶段2 实现

工作目录：`<实验根目录>\ab-longrun-300\SVG018-owl-subway\A-skill`  
本臂只写本目录文件。

---

## 实现前门禁摘要（已过）

- 我理解的目标：单文件 HTML/SVG，owl 驾驶 subway 朝右，附肢相对运动 + ≥2 层视差，无外链
- 风险分档：中（全新创意产物，3 个交付文件）——但父代理已下达「阶段2·实现」显式授权，指令已完整指定产物类型/位置/形态
- 形态选择：单 Agent 主干 — 创意 SVG 场景无并行收益
- 已盘点资源：`gpt-series-reasoning-style` skill（阶段1 load-proof 已读）；同题材先例 `SVG004-owl-subway/A-skill`（结构参考，几何/色板/场景已刻意区分）
- 推荐方案：自写高架蓝调场景 + 4 层 CSS 视差 + 6+ 附肢独立通道

---

## 交付清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `task.md` | 已写 | 本任务交付与验收清单（自建） |
| `art.html` | 已写 | 单文件 HTML/SVG，**48,460 bytes** |
| `notes.md` | 已写 | 几何/运动/视差自洽说明 |
| `response.md` | 已写 | 本文件 |

---

## 验收清单核对

| 验收项 | 结果 | 证据 |
|--------|------|------|
| `art.html` 存在且 ≥ 8KB | **PASS** | `Get-Item` Length = **48460** bytes（阈值 8192） |
| 含 SVG 或 canvas 主体绘制 | **PASS** | 根元素 `<svg id="stage" viewBox="0 0 1200 700" preserveAspectRatio="xMidYMid slice">`；全场景为内联 SVG path/rect/circle/g/text |
| 有动画（CSS 或 JS） | **PASS** | CSS `@keyframes` 共 **21** 组：`scroll-far/mid/near/rail`, `train-bob`, `wheel-spin`, `head-scan`, `wing-l`, `wing-r`, `tuft-l`, `tuft-r`, `blink`, `tail-flick`, `crest-puff`, `beam-pulse`, `win-flicker`, `lamp-pulse`, `twinkle`, `speed-dash`, `panto-shake`, `shadow-breathe` |
| 两层以上背景/视差 | **PASS** | 4 层：`.layer-far` 64s / `.layer-mid` 32s / `.layer-near` 16s / `.layer-rail` 10s，均 `translateX(-900px)` 循环；双 tile 无缝；far 层额外 blur |
| 附肢与载具非完全同步锁死 | **PASS** | 独立通道：`#owl-wing-l` 0.78s、`#owl-wing-r` 0.78s（反相）、`#owl-head` 3.6s、`#tuft-l`/`#tuft-r` 1.7s（反相）、`#owl-eyes` 5.1s、`#owl-tail` 1.15s、`#owl-crest` 2.4s；车体仅 `#train-group` 0.62s 竖直 bob |
| 无外部资源依赖 | **PASS** | 扫描 `https?://` 仅命中 SVG 命名空间 `xmlns="http://www.w3.org/2000/svg"`（非网络请求）。`src=`/`href=`/`fetch`/`XMLHttpRequest`/`@import` 全部 0 命中 |
| 自洽说明存在 | **PASS** | `notes.md` 全文 + `art.html` 末尾注释块（约 20 行） |
| response 有证据或 UNVERIFIED | **PASS** | 本文件；无法自动化的视觉项见下 |

---

## 自动化核对命令与结果摘要

```powershell
# 文件大小
art.html  Length = 48460
task.md / notes.md / response.md  已写

# 外部资源扫描
唯一匹配: xmlns="http://www.w3.org/2000/svg"   → 标准命名空间，非资源加载
src= / href= / fetch( / XMLHttpRequest / @import  → 全部 False

# 动画 / 层 / 附肢
@keyframes count = 21
layer-far / mid / near / rail → True
owl-wing-l / owl-wing-r / owl-head / tuft-l / tuft-r / owl-eyes / owl-tail → True
car-cab / wheel-spin / train-bob / scroll-far → True
```

---

## 运动一致性逻辑核对（代码级，非视觉）

1. **前进方向 = 右**
   - 驾驶室（车头）在列车组右端：`#car-cab` path 从 x≈828 拉到鼻端 x≈1082
   - 头灯锥：`1068,355 → 1200,…` 朝右
   - 速度线动画：`translateX(0 → -28px)` 朝左拖尾
   - 全部背景层：`translateX(0 → -900px)` 世界左移

2. **车轮 = 顺时针**
   - `@keyframes wheel-spin { 0→360deg }` 默认顺时针
   - 接触地面在轮缘下方 → 顺时针产生向右的推进
   - 与上述方向一致

3. **视差速度比**
   - far 64s : mid 32s : near 16s : rail 10s = 1 : 2 : 4 : 6.4
   - 同为 900px 循环 → 速度与 1/时长 成正比 → 远慢近快，正确

4. **附肢 vs 车体**
   - 车体：`train-bob` 0.62s，Y 轴平移 −2.8 / +1.4 px
   - 翼：0.78s 旋转（不同周期、不同轴）
   - 头：3.6s 旋转（远长周期）
   - 耳簇 1.7s 反相；眼 5.1s；尾 1.15s
   - 结论：不存在「全身锁死随车平移」

---

## UNVERIFIED（无法自动化的视觉项）

| ID | 项目 | 用户自验步骤 |
|----|------|--------------|
| V1 | owl 与 subway **可辨认**（造型识别度） | 用浏览器打开 `art.html`，应看到：右侧流线型奶油色车头+两节车厢、车轮、受电弓；驾驶窗内有耳簇大眼猫头鹰，翼搭油门/仪表 |
| V2 | 视差观感「至少两层景深」 | 打开后盯住远景楼 vs 近景电杆：远景移动明显更慢；枕木最快 |
| V3 | 车轮滚动方向是否「看起来」向右 | 观察轮辐条：应顺时针转，与车头朝右一致 |
| V4 | 附肢相对运动是否自然、不突兀 | 观察 3–5 秒：双翼交替轻摆、头部缓慢环视、耳簇抖动、尾羽轻扫、偶尔眨眼，均与车体微颠不同步 |
| V5 | 蓝调氛围 / 非「白底扁平占位」 | 应有深蓝夜空、月亮、星空闪烁、橙色色带、窗光、头灯光锥 |
| V6 | 在目标分辨率下无裁切/拉伸错误 | 缩放浏览器窗口；`preserveAspectRatio="xMidYMid slice"` 应填满视口 |
| V7 | owl 面部细节（眉纹/喙/制服领）是否清晰 | 放大驾驶窗：应可见橙色喙朝右、深蓝制服领与金色徽章 |

---

## 禁止项自检

- 未读取本目录以外的**项目**文件（仅读本目录；A 臂 skill `gpt-series-reasoning-style` 按臂协议允许）
- 未修改本目录以外文件
- 未使用外部 CDN / 框架 / 网络请求

---

## 阶段2 结束

实现完成，交付齐备。视觉项按上表 `UNVERIFIED`，待人工打开 `art.html` 验收。
