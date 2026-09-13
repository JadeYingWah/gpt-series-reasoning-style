# response.md — 验收核对记录

**作品**：`art.html`（单文件 HTML/SVG）  
**方向**：夜班电车 · Night Tram（冒险直选，创意方向豁免）  
**落盘**：仅本目录 `A-skill/`

---

## 自动化已核对项

| 验收清单项 | 结果 | 证据 |
|---|---|---|
| `art.html` 存在且 ≥8KB | **PASS** | 文件 38,750 bytes |
| 含 SVG 或 canvas 主体绘制 | **PASS** | 存在完整 `<svg id="scene" viewBox="0 0 1200 700">` 及多组 path/rect/circle |
| 有动画（CSS 或 JS） | **PASS** | 15 组 `@keyframes`；多处 `animation:`；轮组/附肢/视差层均有绑定 |
| 两层以上背景/视差 | **PASS** | 5 层：`layer-stars` / `layer-city-far` / `layer-city-mid` / `layer-poles` / `layer-track`，周期与位移不同 |
| 附肢与载具非完全同步锁死 | **PASS（结构）** | 独立节点：`fox-head-group`、`fox-ear-l/r`、`fox-tail`、`fox-scarf`、`fox-arm`、`fox-body`，各自有独立 keyframes 与 duration |
| 无外部资源依赖 | **PASS** | 无 `src=` / `href=` / `@import` / CDN；唯一 URL 为 SVG `xmlns="http://www.w3.org/2000/svg"`（命名空间，非网络请求） |
| 自洽说明存在 | **PASS** | `notes.md` + `art.html` 内注释 |
| response 有证据或 UNVERIFIED | **PASS** | 本文件 |

### 运动方向一致性（静态代码审查）

- 车轮全部使用 `spin-cw`（0°→360° 顺时针）= 车头朝右时的滚动方向 → **与前进一致**
- 背景层全部 `translateX(0 → 负值)` = 相对车体向左流 = 车向右前进 → **一致**
- 烟雾向 **上后方**（`translate(-22px, -48px)`）= 车向右前进时烟落后 → **一致**

---

## UNVERIFIED（无法在本环境自动化的视觉项）

本执行环境无法打开 GUI 浏览器进行截图/实操，以下项**未亲眼观看渲染结果**，请按步骤自验：

### U1 · Fox / Tram 是否可辨认
1. 用浏览器打开 `art.html`
2. 确认画面中部有一辆红色有轨电车，车头朝右，驾驶室窗口内有一只戴帽、围围巾的橙色狐狸
3. 确认能看到：尖耳、白吻、蓬尾、受电弓、车轮、侧窗、头灯

### U2 · 动画是否在播、方向是否正确
1. 观察车轮辐条是否**顺时针**旋转
2. 观察电杆/枕木是否**从右向左**掠过（相对车体）
3. 观察狐狸耳朵是否偶尔抽动、围巾是否飘、尾巴是否摆
4. 确认不是「整只狐狸 + 电车一起锁死平移」

### U3 · 视差是否可感知
1. 同时看星空（几乎不动）→ 远楼（很慢）→ 中楼（中速）→ 近杆（很快）→ 轨（快）
2. 应有明显前后景深感

### U4 · `prefers-reduced-motion`
1. 系统开启「减弱动态效果」后刷新
2. 所有循环动画应停止，静帧仍可辨认 fox + tram

### U5 · 构图与「非白底占位图标」禁令
1. 背景应为深靛蓝→紫灰的夜空渐变，而非纯白
2. 整体应接近电影静帧气质，而非扁平 Material 占位图

### U6 · 烟雾方向
已改为向上后方（`translate(-22px, -48px)`），与车向右前进一致。可自验烟是否向左后飘。

---

## 未做的自动化

- 未跑浏览器截图 / 无头 Chromium（本环境未提供 GUI 自动化工具授权路径）
- 未做像素级对比

以上缺口全部体现在 UNVERIFIED 条目，**未声称视觉良好**。

---

## 文件清单

- `art.html` — 主交付
- `notes.md` — 几何/运动自洽
- `response.md` — 本文件
- `task.md` / `load-proof.md` — 阶段输入（未改动）
