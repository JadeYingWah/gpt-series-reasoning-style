# SVG016-moth-gondola · B 臂核对记录

工作目录：`<实验根目录>\ab-longrun-300\SVG016-moth-gondola\B-noskill`

说明：该目录原先不存在，亦无 `task.md`。按臂指令自建创意 SVG —— **飞蛾驾驶贡多拉朝右**。主题取威尼斯新月运河夜航，与既有 SVG012 同题材但独立构图/风格。

## 验收清单

| 项 | 结果 | 证据 |
|----|------|------|
| `art.html` 存在且 ≥ 8KB | ✅ PASS | 实测 **38148 bytes** |
| 含 SVG 或 canvas 主体绘制 | ✅ PASS | 根节点 `<svg id="scene" viewBox="0 0 1200 700">`；船体/飞蛾/运河建筑均为 SVG path/ellipse/rect/circle |
| 有动画（CSS 或 JS） | ✅ PASS | 内联 `<style>` 含 **25** 个 `@keyframes`：`scrollLeftFar/Mid/Near`、`hullBob`、`hullPitch`、`oarStroke`、`oarBladeFlex`、`wakeDriftA/B`、`flapFL/FR/HL/HR`、`antSwayL/R`、`gripFore/Mid`、`thoraxLean`、`abdomenPulse`、`lampFlicker`、`twinkle`、`moonBreath`、`moteFloat`、`dripFall`、`waterSheen`；JS 仅做 tile 克隆无缝循环 |
| 两层以上背景/视差 | ✅ PASS | **3 层**：`#plx-far`（远塔/穹顶，55s）、`#plx-mid`（沿岸 palazzo+灯，32s）、`#plx-near`（前景拱桥+桩+萤火，16s）；周期比 55:32:16 ≈ 3.4:2:1 |
| 附肢与载具非完全同步锁死 | ✅ PASS | 见下表；附肢周期均 ≠ 船体 bob 3.4s / pitch 5.2s |
| 无外部资源依赖 | ✅ PASS | 全文仅 `http://www.w3.org/2000/svg`（XML 命名空间，非网络请求）；无 CDN、无 `<link>`、无 `src=`、无 `@import`、无 `fetch`/`XHR` |
| 自洽说明存在 | ✅ PASS | `art.html` 顶部 HTML 注释 + 本文件 |
| response 有证据或 UNVERIFIED | ✅ PASS | 本文件 |

## 运动自洽

### 推进方向 = 画面右侧

| 机制 | 实现 | 方向核对 |
|------|------|----------|
| 船桨 `#oar-group` | `oarStroke` 2.6s：下水 → 向后扫 → 抬起 | 桨叶绕 forcola 顺时针扫水，把水推向后（左） |
| 尾迹 `#wake-stream` | `wakeDriftA/B`：`translateX(+10 → -160/-200)` | 水花/波纹向 **左** 飘散 = 船向 **右** |
| 三层背景 | `scrollLeftFar/Mid/Near` 全部 `translateX(0 → -1200)` | 景物向左移 = 观察者相对右移 |
| 船体 X | 固定，不平移 | 避免与视差双重位移；相对运动由背景+尾迹表达 |

### moth 相对载具运动（≥2 处，实为 6 处）

| # | 附肢/部位 | 动画 | 周期 | 与船体关系 |
|---|-----------|------|------|------------|
| 1 | 前足 `#leg-fore-l/r` 握桨 | `gripFore` 弧线 | 2.85s | ≠ bob 3.4s / pitch 5.2s |
| 2 | 中足 `#leg-mid-l/r` 搭舷缘 | `gripMid` 微调 | 3.7s | 独立 |
| 3 | 触角 `#ant-l` / `#ant-r` | `antSwayL/R` 异相摆 | 2.1s / 2.55s | 相位与周期互异 |
| 4 | 四翅 `#wing-fl/fr/hl/hr` | 缓慢扇动 ±14–18° | 2.35s | 与船体异步 |
| 5 | 胸部 `#moth-torso` | 前倾/呼吸 | 3.05s | 轻微，非锁死平移 |
| 6 | 腹部 `#moth-abdomen` | 缩放脉动 | 3.05s | 与胸同频但为局部形变 |

### 视差层

| 层 | 元素 | CSS 周期 | 相对速度 |
|----|------|----------|----------|
| L1 far | 钟楼、穹顶、远屋脊剪影 | 55s / 1200px | 1× |
| L2 mid | palazzo 立面、暖窗、远拱桥、沿岸灯 | 32s / 1200px | ~1.7× |
| L3 near | 前景大拱桥、系泊桩 bricola、萤火 | 16s / 1200px | ~3.4× |

JS `cloneTile` 为每层克隆一份 tile 置于 `translate(1200,0)`，配合 `translateX(0 → -1200)` 无缝循环。

### 可辨认性设计要点

- **Moth**：淡绿 luna-moth 四翅 + 翅脉 + 眼斑、羽状触角、毛茸胸、复眼、腹部节纹、滑稽草帽（gondolier）
- **Gondola**：非对称深紫黑船体、右舷金色 **ferro**（梳齿状船首饰）、左舷艉卷、金舷缘线、双灯笼、船底挂饰球、forcola 桨架 + 木桨

## 视觉项（需人眼确认）— UNVERIFIED

以下无法在无头环境用像素断言，**请用户打开 `art.html` 自验**：

1. **moth 可辨认**  
   应看到：淡绿大翅飞蛾站在船中段，草帽、羽状触角、双手伸向右前方桨杆。  
   → 若翅被船体遮住或过小，调 `#moth` 的 `translate(560,400)`。

2. **gondola 可辨认**  
   应看到：深紫长舟，**尖锐金色船首饰在右侧**，左端上卷船艉，两盏暖灯。  
   → 若像普通小船，可接受（卡通化）；若完全不像 gondola 请反馈。

3. **桨动与前进一致**  
   右侧木桨应周期性下压扫水；水花/波纹向左漂；背景向左流。  
   → 若感觉桨在拖船，可反向 `oarStroke` 的 rotate。

4. **附肢非锁死**  
   盯前足、触角 5 秒：应与船体上下浮动明显不同步。  
   → 若整体像贴图平移，检查浏览器对 SVG `transform-box: fill-box` 的支持（现代 Chrome/Edge/Firefox/Safari 均支持）。

5. **三层景深**  
   远塔几乎不动，palazzo 中速，前景桥/桩明显更快。

6. **风格非「白底扁平占位」**  
   深夜运河渐变天空、新月光晕、星光闪烁、金饰船体、半透明翅脉、水面反光条 —— 非 Material 占位图标风。

## 自验步骤

```
1. 用 Chrome / Edge / Firefox 直接打开 art.html（file://，无需服务器）
2. 观察 10 秒：背景是否连续向左流动、有无跳帧/白闪/接缝
3. 盯飞蛾前足与触角 5 秒：是否与船体 bob 不同步
4. 看右侧船桨与左侧尾迹：是否「船向右、水花向左」
5. DevTools → Network：应无任何外部请求（仅 document）
6. DevTools → Console：无报错
```

## 边界 / 未做

- 未做响应式触控交互（任务未要求）
- 未做音频（任务未要求）
- 未做真实物理/刚体（纯 CSS/JS 表现层）
- 极旧浏览器若无 `transform-box: fill-box`，附肢旋转会退化为相对 SVG 默认原点，页面仍可看

## 文件

- `art.html` — 38148 bytes 单文件交付
- `notes.md` — 设计与实现笔记（场景图、运动系统、约束落实）
- `response.md` — 本核对记录
