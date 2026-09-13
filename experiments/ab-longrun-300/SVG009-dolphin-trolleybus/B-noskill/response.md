# SVG009 · response.md — 实际核对记录

## 验收清单

| 项 | 结果 | 证据 |
|----|------|------|
| `art.html` 存在且 ≥ 8KB | ✅ VERIFIED | `Get-Item` → **39910 bytes (39.0 KB)** |
| 含 SVG 或 canvas 主体绘制 | ✅ VERIFIED | 全文以 `<svg class="scene" viewBox="0 0 1600 900">` 为唯一画布；`grep` 无 `<canvas` |
| 有动画（CSS 或 JS） | ✅ VERIFIED | CSS：`@keyframes` spin-wheel / drift-* / dolphin-bob / flipper-* / tail-flap 等；JS：点击 honk |
| 两层以上背景/视差 | ✅ VERIFIED（代码层） | `.layer-far` `.layer-mid` `.layer-near` `.layer-road` + 静态天空；见 `notes.md` §3 |
| 附肢与载具非完全同步锁死 | ✅ VERIFIED（代码层） | 周期表：chassis 1.10s vs torso 1.65s / flipper-r 1.35s / flipper-l 2.05s / tail 1.15s / dorsal 2.4s；见 `notes.md` §2 |
| 无外部资源依赖 | ✅ VERIFIED | 无 `<link>`、无 `@import`、无 `src=` 外链、无 `fetch`/`XMLHttpRequest`。唯一 `http` 字符串为 `http://www.w3.org/2000/svg`（SVG 命名空间，非网络） |
| 自洽说明存在 | ✅ VERIFIED | `notes.md` + `art.html` 头部 HTML 注释 |
| response 有证据或 UNVERIFIED | ✅ 本文件 | |

## 代码/静态核对（已做）

```text
# 大小
art.html = 39910 bytes ≥ 8192

# 外链扫描（应仅命中 SVG namespace）
Select-String "http://|https://|cdn\.|unpkg|jsdelivr|googleapis"
→ 仅 line 960: createElementNS('http://www.w3.org/2000/svg', 'g')

# 主体结构
- <svg viewBox="0 0 1600 900">          ✓
- 双集电杆 .pole / .pole-b               ✓ trolleybus 特征
- 轮 .wheel ×2 + #wheelArt 辐条          ✓ 右行顺时针
- 海豚：吻部/背鳍/双胸鳍/尾鳍/呼吸孔/微笑/船长帽 ✓
- 方向盘在右胸鳍 group 内                ✓
```

## UNVERIFIED（需用户目视自验）

以下为 **视觉/观感** 项，无法在无头环境自动判分，请用浏览器打开 `art.html` 自查：

1. **UNVERIFIED — 海豚与电车可辨认度**  
   步骤：打开 `art.html`，3 秒内能否认出「海豚在开无轨电车」？车顶双杆是否接到上方双线？

2. **UNVERIFIED — 车轮旋转方向是否像右行**  
   步骤：注视任一轮辐条，确认顺时针；同时路面虚线应向左跑。若感觉像倒车，说明观感失败。

3. **UNVERIFIED — 附肢相对运动肉眼可见**  
   步骤：盯住左胸鳍（挥手）与车身侧条纹至少 4 秒，应看到鳍与车身不同步；尾鳍应在车窗外侧有独立鞭动。

4. **UNVERIFIED — 视差景深是否成立**  
   步骤：对比远景楼群与近景路灯的横向速度，近景应明显更快；路灯掠过屏幕应短于远处楼影。

5. **UNVERIFIED — 风格是否达标（非白底扁平占位）**  
   步骤：确认背景为黄昏海色渐变 + 夜城，而非 `#fff` 纯白；无 emoji 占位、无默认 Font-Awesome 类图标。

6. **UNVERIFIED — 交互**  
   步骤：点击画面任意处，应出现 “HONK!” 并短暂加速导线电流虚线，约 0.7s 后恢复。

7. **UNVERIFIED — reduced-motion**  
   步骤（可选）：系统开启「减弱动态效果」后刷新，动画应全部静止且构图仍完整。

## 未做 / 边界

- 未在真实浏览器跑像素 diff / 录屏（本臂环境仅做文件与静态结构核对）。
- 未读 `<skill安装目录> 及工作目录以外任何项目文件（按 B 臂协议）。
- 未修改本目录以外文件。
