# SVG012-moth-gondola · B 臂核对记录

工作目录：`<实验根目录>\ab-longrun-300\SVG012-moth-gondola\B-noskill`

## 验收清单

| 项 | 结果 | 证据 |
|----|------|------|
| `art.html` 存在且 ≥ 8KB | ✅ PASS | 实测文件大小 **31880 bytes** |
| 含 SVG 或 canvas 主体绘制 | ✅ PASS | 根节点 `<svg id="scene" viewBox="0 0 1200 700">`，gondola hull / moth / 背景均为 SVG path/ellipse/circle |
| 有动画（CSS 或 JS） | ✅ PASS | 内联 `<style>` 含 `@keyframes`：`parallaxFar/Mid/Near`、`craftBob`、`spinProp`、`wingFL/FR/HL/HR`、`antL/R`、`tillerSwing`、`gripL/R`、`wakeStream` 等；JS 仅做 tile 克隆无缝循环 |
| 两层以上背景/视差 | ✅ PASS | **3 层**：`#parallax-far`（远山/城郭，48s）、`#parallax-mid`（云带/浮岛，28s）、`#parallax-near`（枝影/萤火，14s）；周期比约 48:28:14 ≈ 3.4:2:1 |
| 附肢与载具非完全同步锁死 | ✅ PASS | 见下方「相对运动」表；moth 附肢动画周期均 ≠ 船体 bob(3.2s)/pitch(5.1s) |
| 无外部资源依赖 | ✅ PASS | 无 `http(s)://`、无 CDN、无 `<link>`、无 `@import`、无 `src=` 外链；全部内联 |
| 自洽说明存在 | ✅ PASS | `art.html` 头部 HTML 注释 + 本文件 |
| response 有证据或 UNVERIFIED | ✅ PASS | 本文件 |

## 运动自洽（已写入 HTML 注释，此处摘要）

### 推进方向 = 画面右侧
- 侧置双叶螺旋桨 `#prop-a` / `#prop-b` 绕自身轴心连续旋转（0.45s/圈）
- 尾部 wake 粒子 `#wake-stream`：`translate(+20 → -120)`，向左喷射，与右移一致
- 前进感由三层背景向左视差表达（craft 在 X 上不做平移，避免与视差双重位移）

### moth 相对载具运动（≥2 处，实为 5 处）

| # | 附肢/部位 | 动画 | 周期 | 与船体关系 |
|---|-----------|------|------|------------|
| 1 | 前足握舵 `#fore-l-grip` `#fore-r-grip` | `gripL/gripR` 独立弧线 + `#tiller` 摇摆 | 2.8s | ≠ bob 3.2s / pitch 5.1s |
| 2 | 触角 `#ant-l` `#ant-r` | `antL` / `antR` 左右摆 | 2.3s / 2.7s | 相位互异，非船体同步 |
| 3 | 四翅 `#wing-fl/fr/hl/hr` | 缓慢扇动 ±16–18° | 2.4s | 与船体异步 |
| 4 | 中足 `#leg-mid-l/r` | 微调 | 4.0s / 3.6s | 独立 |
| 5 | 躯干 `#moth-torso` | 呼吸/前倾 | 3.0s | 仅轻微，非锁死平移 |

### 视差层

| 层 | 元素 | CSS 动画周期 | 相对速度 |
|----|------|--------------|----------|
| L1 far | 远山 silhouette、远塔、暗窗 | 48s / 1200px | 1× |
| L2 mid | 云带、浮岛、雾带 | 28s / 1200px | ~1.7× |
| L3 near | 前景枝影、叶片、萤火 motes | 14s / 1200px | ~3.4× |

JS `cloneTile` 为每层克隆一份 tile 置于 x=+1200，配合 `translateX(0 → -1200)` 实现无缝循环。

## 视觉项（需人眼确认）— UNVERIFIED

以下无法在无头环境用像素断言，**请用户打开 `art.html` 自验**：

1. **moth 可辨认**  
   打开页面后应看到：淡绿色 luna moth（大翅、羽状触角、复眼）位于船舱上方，双手握住右侧金色舵杆。  
   → 若翅膀/触角被船体遮挡或比例过小，说明 z-order/缩放需调。

2. **gondola 可辨认**  
   应看到：深紫船体 + 金色饰边，右舷尖锐 ferro（船首饰），左舷艉卷，两侧灯笼发光，船底挂饰球。  
   → 若更像飞艇吊舱而不像 gondola，可接受（本设计为「飞行 gondola」混合体）；若完全无法辨认请反馈。

3. **螺旋桨旋转方向与前进一致**  
   观察左侧双叶桨：应连续旋转；尾迹粒子向左飘散。  
   → 若感觉「桨在拖船」可翻转 `spinProp` 方向。

4. **附肢非锁死**  
   盯住 moth 前足与触角：应与船体上下浮动明显不同步。  
   → 若整体像贴图一起动，检查浏览器是否支持 SVG `transform-box: fill-box`（Chrome/Edge/Firefox/Safari 近年版本均可）。

5. **三层景深**  
   远山几乎不动，云/岛中速，枝影与萤火明显快过主体附近元素。

6. **风格非「白底扁平占位」**  
   暮色渐变天空、月晕、星光闪烁、金饰船体、半透明翅脉——非 Material 占位图标风。

## 自验步骤

```
1. 用 Chrome / Edge / Firefox 直接打开 art.html（无需服务器）
2. 观察 10 秒：背景是否连续流动、有无跳帧/白闪
3. 盯 moth 前足与触角 5 秒：是否与船体 bob 不同步
4. 看左侧螺旋桨与尾迹粒子：方向是否「船向右、迹向左」
5. DevTools → Network：应无任何外部请求（仅 document）
6. DevTools → Console：无报错
```

## 未做 / 边界

- 未做响应式触控交互（任务未要求）
- 未做音频（任务未要求）
- `transform-box: fill-box` 在极旧浏览器可能失效 → 附肢动画会退化为原点旋转，但页面仍可看
