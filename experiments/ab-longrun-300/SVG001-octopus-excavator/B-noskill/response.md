# response.md · SVG001-octopus-excavator (B-noskill)

## 交付文件

| 文件 | 路径 | 状态 |
|------|------|------|
| `art.html` | `<实验根目录>\ab-longrun-300\SVG001-octopus-excavator\B-noskill\art.html` | ✅ 36.21 KB (≥8KB) |
| `notes.md` | 同目录 | ✅ 几何/运动自洽说明 |
| `response.md` | 本文件 | ✅ |

## 验收清单核对

| 项 | 结果 | 证据 |
|----|------|------|
| `art.html` 存在且 ≥8KB | ✅ VERIFIED | `SizeBytes=37077` / `SizeKB=36.21`（PowerShell `Get-Item`） |
| 含 SVG 或 canvas 主体绘制 | ✅ VERIFIED | `hasSVG=True`；主体为内联 `<svg id="scene" viewBox="0 0 1200 640">` |
| 有动画（CSS 或 JS） | ✅ VERIFIED | `hasAnimation=True`；含 `@keyframes`（tread-scroll / wheel-cw / bob / boom-dig / arm-* / drift-* / dust-rise / blink 等）及 `requestAnimationFrame` 指针视差 |
| 两层以上背景/视差 | ✅ VERIFIED | `parallaxFar=True` `parallaxMid=True` `parallaxNear=True`；L1 远山 80s / L2 工业天际线 40s / L3 前景杂草 18s，JS 指针系数 ×6 / ×14 / ×28 |
| 附肢与载具非完全同步锁死 | ✅ VERIFIED (结构) | `armCtrlL/True` `armCtrlR=True` `armHang=True` `armWave=True`；周期分别为 1.3s / 1.55s / 2.1s / 1.7s，与 `.vehicle-bob` 2.4s 不同相 |
| 无外部资源依赖 | ✅ VERIFIED | `externalScript=False` `externalLink=False` `externalImg=False` `cdn=False` `extImageHref=False` |
| 自洽说明存在 | ✅ VERIFIED | `notes.md` 存在（`notesFile=True`）；HTML 头部亦有注释 |
| response 有证据或 UNVERIFIED | ✅ 本文件 | 见上表 + 下方 UNVERIFIED 项 |

## 实际执行的自动化命令（证据）

```powershell
# 文件体积
$f = "...\\art.html"; $item = Get-Item $f
# → SizeBytes=37077  SizeKB=36.21

# 内容匹配
$c = Get-Content -Raw $f
# → hasSVG=True
# → hasAnimation=True
# → externalScript=False  externalLink=False  externalImg=False  cdn=False
# → octopusId=True  excavatorId=True
# → parallaxFar/Mid/Near=True
# → armCtrlL/R, armHang, armWave=True
# → trackTread=True  wheelSpin=True
# → notesFile=True
```

HTML 内嵌自检对象 `window.__SVG001_CHECKS__`（打开页面后可在 DevTools Console 查看 `[SVG001 self-check]`）。

## UNVERIFIED（需用户目视自验）

以下项无法用文件级命令自动断言，请在浏览器打开 `art.html` 后按步骤核对：

1. **octopus 与 excavator 可辨认**
   - 打开页面，确认右侧有一只品红色章鱼（头+眼+多腕）位于橙色挖掘机驾驶舱内。
   - 自验步骤：肉眼识别头部椭圆、双眼、至少 4–6 条可见触腕；底盘有履带与轮组，前方有动臂+斗杆+铲斗。

2. **履带/车轮循环方向与前进一致**
   - 自验步骤：观察履带花纹向**左**滚动、车轮**顺时针**转、地面刻痕向左移 → 载具相对世界向**右**前进。若履带向右滚而车轮顺时针，则方向不一致（当前实现二者均匹配右前进）。

3. **章鱼附肢相对载具的运动观感**
   - 自验步骤：盯住驾驶舱，应看到左右操纵臂不同步、至少一条腕伸出窗外独立摆动；章鱼不应随车体完全刚性平移。

4. **视差/景深观感**
   - 自验步骤：左右晃动鼠标，远山几乎不动、中景天际线轻移、前景杂草移动最快；无鼠标时 CSS 自动漂移仍可见三层速度差。

5. **非「白底 + 默认扁平占位」审美**
   - 自验步骤：确认场景为深蓝黄昏工业工地风格，有渐变、阴影、警示条、玻璃反光，而非白底 SVG 默认图标。

6. **画面无裁切/比例失真**
   - 自验步骤：窗口拉伸时 `preserveAspectRatio="xMidYMid slice"` 应铺满且主体不被完全裁掉。

## 残留风险

- `transform-box: view-box` + `transform-origin` 在极旧浏览器（IE / 旧 Safari <16）可能不生效，附肢旋转会退化为绕默认原点。现代 Chrome / Edge / Firefox / Safari 16+ 正常。
- 指针视差使用 `style.translate`（较新），旧浏览器忽略该增强，不影响 CSS 主动画。
