# SVG003-crab-snowplow · 几何 / 运动自洽说明

工作目录：`<实验根目录>\ab-longrun-300\SVG003-crab-snowplow\B-noskill`  
交付物：`art.html`（单文件，CSS/JS 内联，无 CDN/框架/网络请求）

## 前进方向约定

- **车头在画面右侧**，雪铲朝右，整体朝右推进。
- 侧视、车头朝右时，**车轮顺时针旋转 = 前进**（`@keyframes spinCW: 0 → 360deg`）。
- 地面雪纹 / 履带痕迹向**左**飘（`groundDrift`），与相对地面前进一致。
- 排气烟向**左后方**飘散（`puff` 关键帧 translate 负 X）。
- 雪铲抛雪：雪团从铲面前缘向上后方飞散（`spray` 关键帧向左上），符合推雪物理。

## 层级 / 视差（≥2 层）

| 层 | id | 内容 | 动画 |
|----|-----|------|------|
| L0 | — | 天空渐变 | 静止底色 |
| L1 | `layer-stars` | 星空 + 极光 | `twinkle` / `aurora` 慢闪，几乎不位移（最远） |
| L2 | `layer-far` | 远山剪影 + 雪帽 | `farScroll` 36s / 300px（最慢平移） |
| L3 | `layer-mid` | 针叶林 | `midScroll` 14s / 400px（中速） |
| L4 | `layer-ground` + `hero` | 雪原 + 车体 | 地面纹理 3.2s / 120px；车体基准 |
| L5 | `layer-fore` | 前景雪丘 + 落雪 | 前景雪丘 2.0s / 120px（最快平移）；雪花下落 |

## crab 附肢相对载具（≥2 处，非全身锁死）

| 附肢 | 类 | 动画 | 周期 | 相对关系 |
|------|-----|------|------|----------|
| 左眼柄 | `.eye-stalk-l` | `eyeWobbleL` 旋转 | 1.1s | 独立于车身 bob |
| 右眼柄 | `.eye-stalk-r` | `eyeWobbleR` 旋转（反相） | 0.85s | 与左眼异相 |
| 瞳孔 | `.pupils` | `pupilNudge` 平移 | 1.6s | 相对眼球 |
| 左螯 | `.claw-l` | `clawGripL` 夹持 | 0.72s | 相对方向盘微位移 |
| 右螯 | `.claw-r` | `clawGripR` 夹持（反相） | 0.62s | 相对方向盘 |
| 步足 a/b/c | `.leg-a/b/c` | `legSwing1/2/3` 摆动 | 0.75–1.05s | 相位错开，不与车身刚体同步 |
| 触角 | `.ant-l/r` | `antennaWave` | 1.25–1.4s | 独立摇摆 |

车身自身另有 `bodyBob`（0.55s 竖直微颠 + 微转），与上述附肢周期均不同 → **附肢与载具存在相对运动**。

## 其他循环

- **车轮**：`.wheel` / `.wheel.rear` 顺时针；辐条矩形使旋转肉眼可见。
- **雪铲**：`.plow-blade` 微抖（0.28s），模拟切雪振动。
- **警灯**：`.beacon-glow` 脉冲 0.7s。
- **大灯**：`.headlight-beam` 慢闪 + 光束多边形。
- **排气**：三枚 puff 错相。

## 技术约束

- 无外部样式表 / 字体 / 图片 / CDN / fetch / XHR。
- `xmlns="http://www.w3.org/2000/svg"` 仅为 SVG 命名空间声明，**不是网络请求**。
- 轻量 JS 仅用于向 `#snowfall` 追加装饰性雪花；场景在无 JS 时仍完整可读。
- 文件约 **42 KB**，远超 8KB 门槛。
