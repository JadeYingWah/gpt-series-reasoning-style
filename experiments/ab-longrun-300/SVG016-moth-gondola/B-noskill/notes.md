# SVG016-moth-gondola · B-noskill 设计笔记

工作目录：`<实验根目录>\ab-longrun-300\SVG016-moth-gondola\B-noskill`

臂指令：飞蛾驾驶贡多拉朝右；单文件 `art.html` + `notes.md` + `response.md`；
约束：无外链、附肢相对运动、≥2 层视差、视觉项标 UNVERIFIED。禁止读 `<skill安装目录>

---

## 1. 创意方向

| 项 | 取值 |
|----|------|
| 场景 | 威尼斯新月运河夜航（Crescent Canal Night） |
| 主角 | 天蚕蛾科 luna-moth 船娘/船夫，戴草帽 |
| 载具 | 经典非对称贡多拉，船首饰 **ferro** 在右（前进方向） |
| 色调 | 深蓝紫夜空 + 淡绿翅 + 金饰 + 暖灯 |
| 风格 | 矢量插画 / 童话夜景，非扁平占位图标 |

## 2. 文件结构

```
B-noskill/
  art.html     # 唯一交付物：HTML + 内联 CSS + 内联 SVG + 极简 JS（仅克隆 tile）
  notes.md     # 本文件：设计与实现笔记
  response.md  # 验收核对 + UNVERIFIED 视觉清单
```

无 package.json、无构建、无 CDN。`file://` 直开即用。

## 3. 场景图（SVG viewBox 1200×700）

```
svg#scene
├── sky / stars / moon-halo          固定层（不滚）
├── #plx-far                         远景：塔楼、穹顶、屋脊剪影（55s 滚）
│   └── #far-tile-a  + JS 克隆 tile-a-clone @ translate(1200,0)
├── #plx-mid                         中景：palazzo 立面、暖窗、远拱、岸灯（32s）
│   └── #mid-tile-a  + clone
├── water (fixed) + #water-sheen     水面与高光
├── #gondola-rig                     载具整体（bob 3.4s；X 不平移）
│   └── #gondola-hull                pitch 5.2s
│       ├── hull / gold gunwale / ferro (右) / stern curl (左)
│       ├── lanterns, seat, ball ornament
│       ├── #oar-group               oarStroke 2.6s
│       │   └── #oar-blade           flex 2.6s
│       └── #moth                    translate(560,400) 朝右
│           ├── #wing-hl / #wing-hr 远翅
│           ├── #leg-mid-l/r        中足搭舷
│           ├── #wing-fl / #wing-fr 近翅
│           ├── #moth-abdomen       腹脉动 3.05s
│           ├── #moth-torso         胸前倾 3.05s
│           │   ├── head + eye + palps（朝右）
│           │   └── #ant-l / #ant-r  触角 2.1s / 2.55s
│           ├── #leg-fore-l/r       前足伸向右前方桨杆 2.85s
│           └── #hat                草帽
├── #wake-stream / wake-a…d          尾迹左漂
├── #plx-near                        前景：大拱桥、bricola、萤火（16s）
└── vignette + signature text
```

## 4. 运动系统

### 4.1 前进方向自洽（画面右侧）

| 信号 | 方向 | 机制 |
|------|------|------|
| 背景 3 层 | 向左 | `translateX(0 → -1200)` |
| 尾迹 / 波纹 | 向左 | `translateX(+10 → -160/-200)` |
| 船体 X | 固定 | 避免与视差双重位移 |
| 船桨 | 右舷下水后扫 | 把水推向后（左）→ 反作用力向右 |

**阅读规则**：船不动、景物向左 = 船向右。

### 4.2 视差（≥2，实为 3）

| 层 | 周期 / 1200px | 相对速度 |
|----|---------------|----------|
| far | 55s | 1× |
| mid | 32s | ~1.7× |
| near | 16s | ~3.4× |

JS `cloneTile` 把每层 tile 克隆一份放到 `translate(1200,0)`，配合 `0→-1200` 无缝循环。

### 4.3 附肢相对载具（≥2，实为 6 组）

船体参考：bob **3.4s**、pitch **5.2s**。

| 部位 | 周期 | 说明 |
|------|------|------|
| 触角 ant-l / ant-r | 2.1s / 2.55s | 左右互异相，绝非锁死 |
| 四翅 wing-fl/fr/hl/hr | 2.35s | 缓扇 ±14–18°，origin 在翅根 |
| 前足 leg-fore-l/r | 2.85s | 握桨弧线，延迟 0.1s |
| 中足 leg-mid-l/r | 3.7s | 搭舷缘微调，延迟 0.2s |
| 胸 thorax | 3.05s | 轻微前倾/呼吸 |
| 腹 abdomen | 3.05s | 局部 scaleX/Y 脉动（形变，非平移） |

所有附肢用 `transform-box: fill-box` + 各自 `transform-origin`，避免绕 SVG 原点飞转。

### 4.4 其他氛围动画

- 灯笼 flicker 1.7s / 2.1s 异相
- 星 twinkle 2.2–3.8s 多档
- 月晕 moonBreath 6s
- 萤火 moteFloat 5s 左上漂
- 桨滴 dripFall 2.6s
- 水面 sheen 7s

共 **25** 组 `@keyframes`。

## 5. 可辨认性设计要点

**Moth（朝右）**
- 头在 `cx=16`，复眼在 `cx=22`（右侧）
- 前足路径 `L38,22 L70,28` / `L42,30 L78,34` 向右伸向桨杆
- 羽状触角、淡绿四翅、翅脉、眼斑、毛茸胸、腹节纹、草帽

**Gondola（船首饰右）**
- 主船体 path 从左艉弧扫到右侧尖艏
- `#ferro` 在 `translate(918,415)`，梳齿朝右上
- 左艉上卷 + 金球；金舷缘线贯穿
- 双灯笼、乘客舱剪影、船底挂球
- forcola 桨架 + 木桨在右舷（前进侧）

## 6. 技术约束落实

| 约束 | 做法 |
|------|------|
| 单文件 | HTML/CSS/SVG/JS 全内联 |
| 无外链 | 无 CDN / `<link>` / `src=` / `@import` / fetch；仅 SVG xmlns URI（非网络） |
| 附肢相对 | 独立 keyframes + fill-box origin + 周期互异 |
| ≥2 视差 | 3 层，速度比约 1 : 1.7 : 3.4 |
| UNVERIFIED 视觉 | response.md 列人眼核对项，不伪称像素验收 |

## 7. 已知边界

- 非响应式触控交互（未要求）
- 无音频 / 无物理引擎（表现层动画）
- 极旧浏览器若无 `transform-box: fill-box`，附肢会退化为绕默认原点，页面仍可看
- 动画为 CSS 无限循环，无 JS 时间轴；JS 仅负责 tile 克隆

## 8. 自验清单（人眼）

1. 打开 `art.html`（file://）
2. 10s：背景连续左流，无白闪/接缝
3. 5s：前足与触角 vs 船体 bob 明显不同步
4. 右桨 + 左尾迹 = 「船向右、水花向左」
5. Network 零外部请求；Console 零报错

详见 `response.md`。
