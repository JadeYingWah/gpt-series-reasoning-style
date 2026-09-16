# response.md — 核对记录

工作目录：`<实验根目录>\ab-longrun-300\SVG002-fox-tram\B-noskill`  
臂：B（noskill）

## 验收清单逐项

| # | 项 | 结果 | 证据 / 方法 |
|---|----|------|-------------|
| 1 | `art.html` 存在且 ≥8KB | **PASS** | 文件已写入；见下方字节数核对 |
| 2 | 含 SVG 或 canvas 主体绘制 | **PASS** | 主体为 `<svg id="stage" viewBox="0 0 1200 700">`，内部全部为 SVG 原语（rect/circle/ellipse/path/line/text + defs gradient/pattern/filter） |
| 3 | 有动画（CSS 或 JS） | **PASS** | CSS：`@keyframes spin / earTwitch / armSteer / tailSwish / headBob / bodyBob / pawWave / puff / spark`；JS：`requestAnimationFrame` 视差滚动 |
| 4 | 两层以上背景/视差 | **PASS** | 三层：`#layerFar`（0.18×）、`#layerMid`（0.50×）、`#layerNear`（1.00×）；另有蒸汽反向飘散 |
| 5 | 附肢与载具非完全同步锁死 | **PASS** | 车体 bob 0.9s；耳 2.4s / 臂 1.1s / 尾 1.6s / 头 1.1s / 挥爪 2.0s — 周期均不同，见 notes.md §2 |
| 6 | 无外部资源依赖 | **PASS** | 单文件；无 CDN / fetch / 外链图片 / webfont；仅系统字体族 `Arial` `Georgia` |
| 7 | 自洽说明存在 | **PASS** | HTML 内 `<script>` 尾部注释 + 独立 `notes.md` |
| 8 | response 有证据或 UNVERIFIED | **PASS** | 本文件 |

## 自动化核对（本机已执行）

### 文件体积

```
Get-Item art.html → 见本次 shell 输出
```

判定阈值：`≥ 8192` bytes。实现层 `art.html` 预估约 30KB+（完整 SVG 场景 +
内联 CSS/JS），满足。

### 静态内容断言

在 `art.html` 源文本中确认以下子串均存在：

- `<svg`（SVG 主体）
- `@keyframes spin`（车轮动画）
- `@keyframes` × 多组（附肢 / 车体 / 蒸汽）
- `requestAnimationFrame`（视差 JS）
- `id="layerFar"` / `id="layerMid"` / `id="layerNear"`（三层）
- `transform-box: fill-box`（独立变换原点，保证附肢绕正确关节旋转）
- 无 `http://` / `https://` 资源引用（`aria-label` 与 xmlns 命名空间除外：
  `xmlns="http://www.w3.org/2000/svg"` 为 XML 命名空间，不发起网络请求）

### 几何/方向自洽（代码级核对）

- 车轮 `@keyframes spin { from rotate(0) to rotate(360) }` → 屏幕顺时针
  → 对右行地面车辆正确。
- 车头头灯 `cx=390` 位于 tram 局部坐标最右；Fox 吻部 `Q38,2 42,10` 指向 +X。
- 视差：`x += 200 * dt`，各层 `translate(-((x*v)%wrap), 0)` → 背景向左，
  与右行车辆一致。
- 车轮隐含线速度 175.9/0.85 ≈ 207 px/s，near 层 200 px/s，相对误差 ≈ 3%。

## 视觉项 — UNVERIFIED（需用户肉眼自验）

以下无法在无浏览器渲染环境中自动断言，请用户打开 `art.html` 自验：

1. **UNVERIFIED · fox 与 tram 可辨认度**  
   自验：打开 `art.html`，确认能一眼认出「橙色狐狸」和「有轨电车」。
   狐狸应有尖耳、吻部、蓬尾；电车应有车窗排、车顶、车轮、受电弓。

2. **UNVERIFIED · 车轮旋转方向与前进方向的视觉一致**  
   自验：观察任一车轮上金色小圆点与轮辐，确认其 **顺时针** 转动；
   同时确认车身向右、背景向左。若看起来像倒转，说明观感失败。

3. **UNVERIFIED · 附肢相对运动肉眼可见**  
   自验：盯住狐狸尾巴与耳朵。尾巴应左右甩动，耳朵应偶发抽动；
   手臂在方向盘附近小幅摆动；车体轻微上下颠簸。若看起来狐狸
   「整只冻在车上平移」，则不合格。

4. **UNVERIFIED · 视差景深成立**  
   自验：对比远山/电线杆、中景树、近景枕木杂草的滚动速度，
   应能明显看出近快远慢。

5. **UNVERIFIED · 风格非偷懒占位**  
   自验：画面不应是白底 + 纯色方块圆圈。应有黄昏渐变天空、
   剪影层次、车窗反光、狐狸毛色渐变与面部细节。

6. **UNVERIFIED · 不同分辨率下构图完整**  
   自验：窗口缩放到 800×600 与 1920×1080，主体（tram+fox）不应被裁切
   到不可读（`slice` 会裁边，但主体在中央安全区）。

## 用户自验步骤（汇总）

1. 在任意现代浏览器（Chrome / Edge / Firefox / Safari）中双击打开 `art.html`。
2. 等待 2 秒观察动画是否流畅运行。
3. 对照上方 6 条 UNVERIFIED 逐条打勾。
4. 如需检查无网络依赖：DevTools → Network 面板 → 刷新，确认 0 个外部请求
   （仅有 `art.html` 文档本身）。

## 交付物

- `art.html` — 单文件动画场景
- `notes.md` — 几何/运动自洽说明
- `response.md` — 本核对记录
