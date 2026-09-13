# Response · SVG004-owl-subway · 阶段2 实现

工作目录：`<实验根目录>\ab-longrun-300\SVG004-owl-subway\A-skill`  
本臂只写本目录文件。

---

## 交付清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `art.html` | 已写 | 单文件 HTML/SVG，38,557 bytes |
| `notes.md` | 已写 | 几何/运动/视差自洽说明 |
| `response.md` | 已写 | 本文件 |

---

## 验收清单核对

| 验收项 | 结果 | 证据 |
|--------|------|------|
| `art.html` 存在且 ≥ 8KB | **PASS** | `Get-Item` Length = **38557** bytes（阈值 8192） |
| 含 SVG 或 canvas 主体绘制 | **PASS** | 根元素 `<svg id="stage" viewBox="0 0 1200 700">`；全场景为内联 SVG path/rect/circle/g |
| 有动画（CSS 或 JS） | **PASS** | CSS `@keyframes` 共 14 组：`scroll-far/mid/near/rail`, `train-bob`, `lamp-pulse`, `win-flicker`, `wheel-spin`, `wing-flap-l/r`, `head-scan`, `tuft-sway`, `blink`, `tail-flick`, `speed-dash`, `tie-pass`, `twinkle`, `vignette-breathe` |
| 两层以上背景/视差 | **PASS** | 4 层：`.layer-far` 48s / `.layer-mid` 24s / `.layer-near` 12s / `.layer-rail` 8s，均 `translateX(-800px)` 循环；双 tile 无缝 |
| 附肢与载具非完全同步锁死 | **PASS** | 独立通道：`#owl-wing-l` 0.7s、`#owl-wing-r` 0.7s（反相）、`#owl-head` 3.2s、`#tuft-l`/`#tuft-r` 1.6s（反相）、`#owl-eyes` 4.5s、`#owl-tail` 1.1s；车体仅 `#train-group` 0.55s 竖直 bob |
| 无外部资源依赖 | **PASS** | grep `https?://\|cdn\|@import\|fetch\|XMLHttpRequest\|src=\|href=` 仅命中 SVG 命名空间 `xmlns="http://www.w3.org/2000/svg"`（非网络请求）。无外链字体/图/脚本 |
| 自洽说明存在 | **PASS** | `notes.md` 全文 + `art.html` 末尾注释块（约 35 行） |
| response 有证据或 UNVERIFIED | **PASS** | 本文件；无法自动化的视觉项见下 |

---

## 自动化核对命令与结果摘要

```
# 文件大小
art.html  Length = 38557
notes.md  Length = 3829

# 外部资源扫描
唯一匹配: xmlns="http://www.w3.org/2000/svg"   → 标准命名空间，非资源加载

# 动画/层/附肢关键字
@keyframes / animation / class="wheel" / layer-far|mid|rail|near
owl-wing-l / owl-wing-r / owl-head / owl-tail / owl-eyes / tuft-l / tuft-r
→ 共 68 处命中，全部为实现与注释，结构完整
```

---

## 运动一致性逻辑核对（代码级，非视觉）

1. **前进方向 = 右**
   - 驾驶室（车头）在列车组右端：`#car-cab` path 从 x≈492 拉到 x≈840
   - 头灯锥：`848,364 → 980,…` 朝右
   - 速度线动画：`translateX(0 → -40px)` 朝左拖尾
   - 全部背景层：`translateX(0 → -800px)` 世界左移

2. **车轮 = 顺时针**
   - `@keyframes wheel-spin { 0→360deg }` 默认顺时针
   - 接触地面在轮缘下方 → 顺时针产生向右的推进
   - 与上述方向一致

3. **视差速度比**
   - far 48s : mid 24s : near 12s : rail 8s = 1 : 2 : 4 : 6
   - 同为 800px 循环 → 速度与 1/时长 成正比 → 远慢近快，正确

4. **附肢 vs 车体**
   - 车体：`train-bob` 0.55s，Y 轴平移 ±2.5px
   - 翼：0.7s 旋转（不同周期、不同轴）
   - 头：3.2s 旋转（远长周期）
   - 结论：不存在「全身锁死随车平移」

---

## UNVERIFIED（无法自动化的视觉项）

| ID | 项目 | 用户自验步骤 |
|----|------|--------------|
| V1 | owl 与 subway **可辨认**（造型识别度） | 用浏览器打开 `art.html`，应看到：右侧流线型车头+车厢、车轮、受电弓；驾驶窗内有耳簇大眼猫头鹰，手（翼）搭在控制杆上 |
| V2 | 视差观感「至少两层景深」 | 打开后盯住任一远景楼 vs 近景电杆：远景移动明显更慢；枕木最快 |
| V3 | 车轮滚动方向是否「看起来」向右 | 观察轮辐条：应顺时针转，与车头朝右一致 |
| V4 | 附肢相对运动是否自然、不突兀 | 观察 3–5 秒：双翼交替轻摆、头部缓慢环视、耳簇抖动、尾羽轻扫，均与车体微颠不同步 |
| V5 | 夜间氛围 / 非「白底扁平占位」 | 应有深蓝夜空、月光、星空闪烁、窗光、头灯光锥 |
| V6 | 在目标分辨率下无裁切/拉伸错误 | 缩放浏览器窗口；`preserveAspectRatio="xMidYMid slice"` 应填满视口 |

---

## 禁止项自检

- 未读取本目录以外项目文件（仅读本目录 `task.md` / `load-proof.md`）
- 未修改本目录以外文件
- 未使用外部 CDN / 框架 / 网络请求

---

## 阶段2 结束

实现完成，交付齐备。
