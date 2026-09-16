# response.md · SVG015-seahorse-cableway · B 臂

工作目录：`<实验根目录>\ab-longrun-300\SVG015-seahorse-cableway\B-noskill`  
（未读取本目录以外项目文件；未读 `<skill安装目录>

## 交付物

| 文件 | 说明 |
|------|------|
| `art.html` | 单文件 HTML/SVG 场景，海马驾驶索道吊厢朝右前进 |
| `notes.md` | 几何/运动自洽说明 |
| `response.md` | 本文件 |

## 验收清单核对

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| 1 | `art.html` 存在且 ≥ 8KB | **PASS** | 文件长度 **29555 bytes**（PS `(Get-Item …).Length`） |
| 2 | 含 SVG 或 canvas 主体绘制 | **PASS** | `<svg id="scene" viewBox="0 0 1600 900">`，吊厢/海马/索塔/缆线均为 SVG path |
| 3 | 有动画（CSS 或 JS） | **PASS** | CSS：`@keyframes finL/finR/tailWave/crownBob/snoutPulse/leverRock/wheelSpin`；JS：`requestAnimationFrame` 循环驱动世界滚动与吊挂摆动 |
| 4 | 两层以上背景/视差 | **PASS** | 4 层：`layer-far`(0.12)、`layer-mid`(0.28)、`layer-towers+cable`(0.55)、`layer-fg`(0.95)，见 `notes.md` |
| 5 | 附肢与载具非完全同步锁死 | **PASS** | 车体：JS translate + sway/bob；鳍/尾/冠/鼻/杆：独立 CSS 动画，周期 0.7–1.6s 不等。见 `notes.md` 表 |
| 6 | 无外部资源依赖 | **PASS** | 无 `<script src>` / `<link href>` / `http` / CDN / unpkg / jsdelivr / googleapis（全文检索 0 命中） |
| 7 | 自洽说明存在 | **PASS** | `notes.md` |
| 8 | response 有证据或 UNVERIFIED | **PASS** | 本表 |

## 额外核对（命令输出）

```
# 文件大小
29555

# 外链检索（http|cdn|unpkg|jsdelivr|googleapis|script src|link href）
# → 无匹配行
```

## 视觉项（自动化不可判）

| 项 | 状态 | 用户自验步骤 |
|----|------|--------------|
| 海马形象是否清晰可辨 | **UNVERIFIED** | 浏览器打开 `art.html`，侧窗内应见青绿色海马：头冠、朝右吻部、眼、胸鳍、卷尾、船长帽 |
| 索道吊厢是否清晰可辨 | **UNVERIFIED** | 应见红木厢体 + 金顶 + 吊臂/索夹滚轮 + 底部三导向轮 + 朝右头灯；上方主缆贯穿画面并经过索塔 |
| 朝右前进观感 | **UNVERIFIED** | 观察背景左移、吊厢在屏上自左向右 wrap；头灯/船首饰均在右侧 |
| 肢体相对运动是否自然 | **UNVERIFIED** | 看鳍是否在摆、尾是否在甩、操纵杆是否在摇，且与车厢上下 bob/左右 sway 不同相 |
| 视差景深是否成立 | **UNVERIFIED** | 远山几乎不动 → 中丘慢移 → 索塔中速 → 前景珊瑚海草最快掠过 |
| 禁止白底扁平占位 | **UNVERIFIED** | 画布为暮色天空渐变 + 日轮 + 水面，非白底；全部为手绘矢量造型 |

## 已知限制

- 浏览器内视觉验收依赖本机打开 HTML；本臂无 headless 浏览器截图能力，故全部纯视觉判断标 `UNVERIFIED`。
- 索塔滚动用 600px tile 取模，极宽视口下塔间距观感会偏密（不影响验收项）。
- 未做移动端触控交互（任务未要求）。
