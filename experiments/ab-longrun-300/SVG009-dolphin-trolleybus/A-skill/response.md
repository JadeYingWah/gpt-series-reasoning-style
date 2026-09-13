# SVG009-dolphin-trolleybus · A-skill · response.md

阶段2收尾：验收清单证据 + 视觉 UNVERIFIED + 用户自验步骤。本文件为实际核对记录，非计划稿。

## 交付物

| 文件 | 状态 |
|------|------|
| `art.html` | 已存在，**25709 bytes (25.1 KB)**，582 行 |
| `notes.md` | 已存在（设计 token + 几何/运动自洽 + 验收映射） |
| `load-proof.md` | 已存在（skill 加载证明 v1.2.0） |
| `response.md` | 本文件 |
| `_qa/t0.png` … `t4.png`、`final.png` | Playwright 无头截图证据（非正式交付物） |

---

## 验收清单（task.md → 实际核对）

| 项 | 结果 | 证据 |
|----|------|------|
| `art.html` 存在且 ≥ 8KB | ✅ VERIFIED | `Get-Item` → **25709 bytes ≥ 8192** |
| 含 SVG 或 canvas 主体绘制 | ✅ VERIFIED | 唯一画布 `<svg id="scene" viewBox="0 0 1280 720">`（L157）；全文无 `<canvas` |
| 有动画（CSS 或 JS） | ✅ VERIFIED | CSS `@keyframes` ×10：`spin-wheel` / `bob-bus` / `flap-flipper` / `pump-tail` / `nod-head` / `spout` / `pole-sway` / `lamp-pulse` / `speed-line` / `twinkle`（L84–138）；JS `requestAnimationFrame` 视差卷动（L506–579） |
| 两层以上背景/视差 | ✅ VERIFIED（代码层 + 截图层） | L0 天空静止；L1 far `0.15`；L2 mid `0.40`；L3 road `1.00`；L4 fg `1.55`（JS L521–525）。结构 id：`layer-sky` / `layer-far` / `layer-mid` / `layer-road` / `layer-fg`。截图 `t0` vs `t4` 可见楼群与路面虚线相对车体位移 |
| 附肢与载具非完全同步锁死 | ✅ VERIFIED（代码层 + 截图层） | 周期表：胸鳍 `1.1s`、尾鳍 `1.35s`、点头 `2.1s`、水雾 `2.8s`、车身 bob `1.6s`、轮 `2.4s`、集电杆 `1.6s`（第二杆 delay `0.4s`）。截图间海豚姿态/尾鳍/胸鳍可见变化，非整车刚体平移 |
| 无外部资源依赖 | ✅ VERIFIED | 无 `<link>`、无 `<script src>`、无 `@import`、无 `fetch`/`XMLHttpRequest`/`cdn`/`unpkg`/`jsdelivr`/`googleapis`。唯一 `http` 字符串：`http://www.w3.org/2000/svg`（SVG 命名空间，非网络请求） |
| 自洽说明存在 | ✅ VERIFIED | `notes.md` §几何/运动自洽 + `art.html` L148–156 HTML 注释 |
| response 有证据或 UNVERIFIED | ✅ 本文件 | |

---

## 代码/静态核对摘要

```text
# 大小
art.html = 25709 bytes ≥ 8192

# 外链扫描（应仅命中 SVG namespace）
Select-String "http://|https://|cdn\.|unpkg|jsdelivr|googleapis|fetch\(|XMLHttpRequest|@import|<link |<script[^>]+src"
→ 仅 L532: var NS = "http://www.w3.org/2000/svg";

# 主体结构（DOM ids / class）
- svg#scene viewBox 0 0 1280 720                         ✓
- 双集电杆 .pole-sway ×2 + 杆头火花 glow                 ✓ trolleybus 特征
- 架空线 y=208 / 218；杆头 y≈212（车 root y=360 + -148） ✓ 贴线
- 轮 .spin-wheel ×2（正向 rotate 0→360° = 顺时针）       ✓ 右行相位
- 海豚：吻部朝右 / 背鳍 / 双胸鳍 / 尾鳍 / 呼吸孔 / 船长帽 ✓
- 方向盘在近胸鳍下方                                      ✓
- prefers-reduced-motion: CSS 关动画 + JS 直接 return     ✓
- 路牌 “09 HARBOR” / HUD “LINE 09 · HARBOR LOOP”          ✓
```

### 前进方向自洽（摘要，详 `notes.md`）

- 目标：载具相对世界向右。实现：车体近似居中微 bob，世界层向左卷。
- 轮：顺时针（CSS 正角度）= 右行触地点相对车体向后。
- 卷速系数：far 0.15 < mid 0.40 < road 1.00 < fg 1.55，近快远慢。

### 附肢独立相位（摘要）

| 部件 | class | 周期 |
|------|-------|------|
| 近/远胸鳍 | `flap-flipper` | 1.1s（远鳍 delay 0.28s） |
| 尾鳍 | `pump-tail` | 1.35s |
| 头/吻 | `nod-head` | 2.1s |
| 呼吸孔水雾 | `spout` | 2.8s |
| 车身 bob | `bob-bus` | 1.6s |
| 车轮 | `spin-wheel` | 2.4s |

---

## 已做过的视觉核验（无头截图，非最终判分）

Playwright Chromium 无头，viewport 1280×720，产物在 `_qa/`：

| 文件 | 用途 |
|------|------|
| `t0.png` / `t1.png` | 加载后 ~0.8s / ~2.3s 两帧 |
| `t2.png` / `t3.png` / `t4.png` | 迭代过程帧 |
| `final.png` | 收尾帧 |

**截图层可观察到（支持性证据，不替代用户目视）：**

- 暮色港湾场景：深蓝夜空 + 月牙 + 星 + 暖橙地平线 + 海堤 + 路面虚线（**非白底**）。
- 青绿车身 + 奶油顶 + 「09」路牌 + 双集电杆接上方双线，杆头有火花点。
- 海豚侧影朝右，戴橙色船长帽，胸鳍/尾鳍可见，位于驾驶舱内。
- 跨帧对比：楼群/电线杆/路面虚线相对车体横向位移；海豚胸鳍与尾鳍姿态变化。

→ 构图与主体可辨认度 **截图层通过**；**运动流畅度与「像不像在开」仍属 UNVERIFIED**（见下）。

---

## UNVERIFIED（需用户浏览器目视自验）

以下为观感/运动质量项，静态代码与单帧截图无法终审。请用本地浏览器直接打开 `art.html`：

1. **UNVERIFIED — 3 秒可辨认度**  
   步骤：打开 `art.html`，3 秒内能否认出「海豚在开无轨电车、朝右前进」？双杆是否接到上方双线？

2. **UNVERIFIED — 右行轮转相位观感**  
   步骤：盯任一轮辐条，应顺时针；同时路面虚线应向左跑。若感觉像倒车，则观感失败。

3. **UNVERIFIED — 附肢相对运动肉眼可见**  
   步骤：盯近侧胸鳍与车身色带至少 4 秒，鳍应与车身 bob 不同步；尾鳍应在车窗后侧独立泵动；偶发可见呼吸孔水雾。

4. **UNVERIFIED — 视差景深是否成立**  
   步骤：对比远景楼群与前景杆影/速度线的横向速度，近景应明显更快；远处楼影掠过屏幕应慢于路灯杆。

5. **UNVERIFIED — 风格达标（禁止白底扁平占位）**  
   步骤：确认为暮色渐变港湾全幅场景，而非 `#fff` 纯白；无 emoji 占位、无默认图标字体。

6. **UNVERIFIED — reduced-motion**  
   步骤（可选）：系统开启「减弱动态效果」后刷新，CSS/JS 动画应全部静止，构图仍完整可读。

7. **UNVERIFIED — 集电杆贴线与火花**  
   步骤：观察双杆头是否始终贴住（或微弹贴住）上方双线；杆头黄点/光晕是否像受电火花。

---

## 未做 / 边界 / 无硬伤说明

- **未改写 `art.html`**：本阶段仅静态核对 + 既有 `_qa` 截图复查，**未发现硬伤**（尺寸、无外链、SVG 主体、动画、多层视差、附肢独立相位、自洽注释均满足 task 清单）。
- 未在真实有头浏览器做像素 diff / 录屏 / 交互点击（本文件无点击 honk 类交互，亦不在验收清单强制项内）。
- 未读取本目录以外的项目文件（A 臂 skill 加载证明见 `load-proof.md`）。
- 未修改本目录以外文件。
- `_qa/` 与 `_qa_shot.js` 为过程证据，非 task 要求交付物；可保留供复核。

---

## 用户最小自验路径（3 分钟）

1. 双击或拖入浏览器打开 `A-skill/art.html`。
2. 对照上文 UNVERIFIED 1–5 逐项目视。
3. （可选）开系统「减弱动态效果」后刷新，核对 UNVERIFIED 6。
4. 满意则本臂阶段2关闭；不满意请指出具体 UNVERIFIED 编号，便于定向返工。
