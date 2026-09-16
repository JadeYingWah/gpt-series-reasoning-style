# response.md · SVG017-beetle-cable-car（B-noskill）

工作目录：`<实验根目录>\ab-longrun-300\SVG017-beetle-cable-car\B-noskill`  
说明：该目录原先不存在，亦无 `task.md`。按臂指令自建创意 SVG —— **甲虫驾驶缆车朝右**。  
风格：黄昏紫金山谷；与既有 SVG008 同题材但独立构图/调色/动画周期。  
核对时间：本回复生成时。

## 验收清单核对

| # | 条目 | 结果 | 证据 |
|---|------|------|------|
| 1 | `art.html` 存在且 ≥ 8KB | **PASS** | `Get-Item.Length` = **30314 bytes** |
| 2 | 含 SVG 或 canvas 主体绘制 | **PASS** | 根节点 `<svg class="scene" viewBox="0 0 1200 700">`；主体为 path/ellipse/rect/circle，无 canvas |
| 3 | 有动画（CSS 或 JS） | **PASS** | **19** 组 `@keyframes`，**26** 处 `animation:`；JS 仅可选指针微倾 |
| 4 | 两层以上背景/视差 | **PASS** | **4 层**：`.layer-far` 48s / `.layer-mid` 28s / `.layer-near` 14s / `.layer-tower` 9s；另加雪粒与前景雾 |
| 5 | 附肢与载具非完全同步锁死 | **PASS（代码层）** | 见下表；**运动观感** → UNVERIFIED |
| 6 | 无外部资源依赖 | **PASS** | 全文唯一 `http://` 为 `http://www.w3.org/2000/svg`（XML 命名空间）；`<script src>` / `<link>` / `@import` / CDN 均 False |
| 7 | 自洽说明存在 | **PASS** | `notes.md` + `art.html` 头部 HTML 注释 |
| 8 | response 有证据或 UNVERIFIED | **PASS** | 本文件 |

## 程序化核对输出摘要

```text
LENGTH=30314
SVG=True  CANVAS=False
KEYFRAMES=19  ANIMATION=26
LAYER_FAR/MID/NEAR/TOWER=True
ANTENNA/FORELEG/MIDLEG/HEAD/TORSO/PULLEY=True
SPIN_CW=True  SCROLL=True
BEETLE=True  CABLECAR=True
SCRIPT_SRC=False  LINK_TAG=False  IMPORT=False  CDN=False
REDUCED=True  VIEWBOX=True
唯一 http 匹配：http://www.w3.org/2000/svg
```

## 附肢独立动画（代码级）

| 选择器 | 作用 | 周期 | 与车厢关系 |
|--------|------|------|------------|
| `.antenna-l` | 左触角摆 | 2.15s | ≠ sway 3.7s / bob 2.9s |
| `.antenna-r` | 右触角反相 | 1.75s + 0.3s delay | 异相 |
| `.foreleg-l` | 前足踩杆 | 1.35s | 独立 |
| `.foreleg-r` | 前足反相 | 1.35s + 0.55s delay | 独立 |
| `.midleg-l` | 中足扶窗 | 2.4s | 独立 |
| `.midleg-r` | 中足扶窗 | 2.6s | 独立 |
| `.beetle-head` | 头部扫视 | 3.4s | 独立 |
| `.beetle-torso` | 躯干呼吸 | 2.05s | 独立 |
| `.elytra-shimmer` | 鞘翅高光 | 4.8s | 独立 |

→ **≥2 处附肢相对载具独立运动**（实为 8 处附肢/部位）。

## 前进方向 = 画面右侧（代码级）

- `.pulley-wheel`：`spinCW` 顺时针；偏心黄点 `cy=-9` 随组旋转可目视旋向。
- 顺时针顶部滑轮 ⇒ 触点线速度向右 ⇒ 车厢向右。
- 四层背景 `scrollLeft`：`translateX(0→-1200)`，景物左移强化向右相对运动。
- 前灯在舱体**右**端（`cx=698`），光锥张向 +X。
- 甲虫头/眼/触角/前足均朝右；操纵杆在右前方。

## 视差层

| 层 | 周期 | 内容 | 相对速度 |
|----|------|------|----------|
| L1 far | 48s | 远峰 + 雪顶 | 1× |
| L2 mid | 28s | 中脊 + 松 + 暖窗 | ~1.7× |
| L3 near | 14s | 近松、巨石 | ~3.4× |
| L4 tower | 9s | 支撑塔架 | ~5.3× |

无缝循环：每层 `#*-tile` + `<use href="#*-tile" x="1200"/>`。

## UNVERIFIED（需用户浏览器目视）

请打开 `art.html` 自验：

1. **甲虫可辨认**  
   期望：紫渐变鞘翅、中缝、复眼、双羽状触角、多足；透过驾驶窗可见。  
2. **缆车可辨认**  
   期望：吊厢 + 吊杆滑轮骑主缆 + 双窗 + 前灯/尾灯 + 编号 17B。  
3. **朝右前进观感**  
   期望：滑轮辐条/黄点顺时针扫；塔架从右出左入；前灯光锥朝右。  
4. **附肢非锁死**  
   盯触角与前足 5 秒：应与车厢 sway/bob 明显不同步。  
5. **四层景深**  
   远山几乎不动，塔架显著更快。  
6. **风格底线**  
   非白底；非 Office 单色剪贴画；应为黄昏深紫金渐变 + 细节路径。  
7. **可选指针微倾**  
   鼠标左右移动时整车微倾（作用在 `#car-tilt` 包装层，不覆盖 sway 动画）。  
8. **不同分辨率**  
   `preserveAspectRatio="xMidYMid slice"` 下主体是否保持在可视区。

## 文件清单

- `art.html` — 主交付（30314 bytes）
- `notes.md` — 运动/几何自洽说明
- `response.md` — 本文件

## 禁止项遵守

- 未读取 `<skill安装目录>
- 未修改工作目录以外文件（仅创建缺失的 `B-noskill` 目录本身）。
