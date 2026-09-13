# SVG011 · 核对记录（response）

工作目录：`<实验根目录>\ab-longrun-300\SVG011-puffin-bulldozer\A-skill`

## 验收清单

| 项 | 结果 | 证据 |
|----|------|------|
| `art.html` 存在且 ≥ 8KB | ✅ VERIFIED | 文件大小 **29,221 bytes**（`Get-Item` Length） |
| 含 SVG 或 canvas 主体绘制 | ✅ VERIFIED | `<svg id="scene" viewBox="0 0 1400 720">` 为唯一主画面；主体由 path/rect/ellipse/circle 绘制，无 canvas |
| 有动画（CSS 或 JS） | ✅ VERIFIED | CSS：`@keyframes beltScroll / wheelSpin / chassisBob / riderBounce / headBob / wingL / wingR / tailFan / slideFar / slideMid / slideNear / dustPuff / smokeUp / bladeGlint`；JS：点击 turbo 增强 |
| 两层以上背景/视差 | ✅ VERIFIED | 三层：`.parallax-far`(48s) / `.parallax-mid`(28s) / `.parallax-near`(12s)，每层双 tile 无缝左移；另有静态天空+太阳基底 |
| 附肢与载具非完全同步锁死 | ✅ VERIFIED（代码层） | 载具 `#dozer-rig` bob 0.55s；puffin 另有 `#puffin-head` 1.1s、`.wing-left/.wing-right` 0.55s 但 origin/幅度不同、`#puffin-tail` 0.35s、`#puffin-root` bounce 独立 origin。频率/相位/枢轴均不同 → 非锁死 |
| 无外部资源依赖 | ✅ VERIFIED | `Select-String` 搜索 `http://` `https://` `cdn.` `unpkg` `jsdelivr` `googleapis` `font-awesome` `@import` → **0 匹配**；字体仅 `system-ui`；无图片/字体/脚本外链 |
| 自洽说明存在 | ✅ VERIFIED | `notes.md` 全文 + `art.html` 顶部 HTML 注释同步说明几何/运动 |
| response 有证据或 UNVERIFIED | ✅ VERIFIED | 本文件 |

## 运动方向自洽（代码级核对）

- 前进方向：blade / 车头朝 **+X（右）** → 声明为向右前进
- 履带接地面：`.tread-belt` `translateX(0 → -28px)` = 向左滑 → 符合向右无滑滚动
- 负重轮：`.road-wheel` `rotate(0 → 360deg)` = 顺时针 = 屏幕上向右滚
- 尘土 `.dust` 向左后方抛；烟 `.smoke` 向上飘 — 方向与车体运动无冲突

## 视觉项

| 项 | 状态 | 用户自验步骤 |
|----|------|--------------|
| puffin 可辨认（黑背白脸大彩喙橙脚） | **UNVERIFIED**（无头无浏览器截图） | 用浏览器打开 `art.html`，确认：头部有橙红大三角喙、白脸、黑眼罩；身体黑背白胸；可见橙色脚蹼 |
| bulldozer 可辨认（履带+铲刀+驾驶室+排气） | **UNVERIFIED** | 确认：黄色机身、灰色大铲刀在右侧、黑色履带带转轮、驾驶室与排气管清晰 |
| 视差观感（远近层速度差明显） | **UNVERIFIED** | 观察远山是否明显比近处灌木/沙纹慢；三者应同向（向左）但速度梯度不同 |
| 履带旋转与轮子顺时针是否「看起来」一致 | **UNVERIFIED** | 盯住履带板相对轮毂的滑动方向：应与轮缘接触点切向一致，无「倒转」错觉 |
| 色调/构图无「白底扁平占位」感 | **UNVERIFIED** | 页面应为蓝→金天空渐变 + 沙丘暖色，非白底 |
| 高分屏缩放下 SVG 无锯齿/错位 | **UNVERIFIED** | 在 100% / 150% / 窗口缩放各看一次 |
| 点击 turbo 后动画加速且 2.2s 恢复 | **UNVERIFIED** | 点击画面，履带/轮/视差应明显变快，约 2 秒后回落 |

## 未做 / 范围外

- 未生成预览截图或 GIF（环境未提供无头浏览器自动化到可产出可信视觉证据的路径；不猜测结果）
- 未做跨浏览器矩阵测试
