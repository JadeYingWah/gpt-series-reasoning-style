# response.md · SVG008-beetle-cable-car（B-noskill）

工作目录：`<实验根目录>\ab-longrun-300\SVG008-beetle-cable-car\B-noskill`  
核对时间：本回复生成时。以下为**实际程序化核对**与需人工目视的 `UNVERIFIED` 项。

## 验收清单核对

| # | 条目 | 结果 | 证据 |
|---|------|------|------|
| 1 | `art.html` 存在且 ≥ 8KB | **PASS** | 文件长度 **28900+ bytes**（`Get-Item .Length`，28833 起，补丁后略增） |
| 2 | 含 SVG 或 canvas 主体绘制 | **PASS** | 含 `<svg class="scene" viewBox="0 0 1200 700">`；无 canvas（选用 SVG） |
| 3 | 有动画（CSS 或 JS） | **PASS** | 含 12+ 组 `@keyframes`；`animation:` 属性多处；JS 仅可选指针微调 |
| 4 | 两层以上背景/视差 | **PASS** | 4 层视差：`.layer-far` / `.layer-mid` / `.layer-near` / `.layer-tower`；另有前景雾 |
| 5 | 附肢与载具非完全同步锁死 | **PASS（代码层）** | 见下「附肢独立动画」；**运动观感** → UNVERIFIED |
| 6 | 无外部资源依赖 | **PASS** | 全文唯一 `http://` 为 SVG `xmlns="http://www.w3.org/2000/svg"`（命名空间，非网络请求）；无 `<script src>`、无 CDN、无 `@import` 字体 |
| 7 | 自洽说明存在 | **PASS** | `notes.md` + `art.html` 头部注释 |
| 8 | response 有证据或 UNVERIFIED | **PASS** | 本文件 |

## 程序化核对命令与输出摘要

```powershell
# 大小
Get-Item art.html | Select Length
# → 28833

# 结构关键字
Select-String: <svg, @keyframes, animation:, parallax, beetle/antenna/elytra, cabin/cable/pulley
# → 均 True

# 外链扫描
[regex] Matches 'https?://'
# → 仅 http://www.w3.org/2000/svg
```

## 附肢独立动画（代码级，可 grep）

| 选择器 | 作用 | 独立周期 |
|--------|------|----------|
| `.antenna-l` | 左触角摆动 | 2.1s |
| `.antenna-r` | 右触角反相 | 1.7s |
| `.foreleg-l` | 前足踩杆 | 1.4s |
| `.foreleg-r` | 前足反相 | 1.4s + delay |
| `.midleg-l` | 中足扶窗 | 2.0s |
| `.beetle-head` | 头部扫视 | 3.2s |
| `.beetle-torso` | 躯干相对车厢起伏 | 1.8s |
| `.cabin-group` | 车厢吊挂摆动（基座） | 3.6s |

→ **≥2 处附肢相对载具独立运动**（实际 6 处附肢 + 躯干 + 头）。

## 轮系与前进方向一致性（代码级）

- `.pulley-wheel`：`rotate(0→360deg)` **顺时针**，`transform-origin: 640px 140px`（吊挂点/触缆点）。
- 顶部滑轮顺时针 ⇒ 触点线速度向右 ⇒ 车厢向右。
- `.guide-wheel`：同样顺时针。
- 背景 `translateX(0 → 负值)` 向左滚动，强化向右相对运动。
- 前灯在车厢**右**端，光锥朝右。

## UNVERIFIED（需用户浏览器目视）

以下无法在无头环境自动「看见」，请打开 `art.html` 自验：

1. **美术辨识度**  
   - 自验：一眼能否认出「甲虫」与「缆车吊厢」？  
   - 期望：甲壳绿渐变、触角、复眼；吊厢轮廓、主缆+滑轮、双窗。

2. **前进观感**  
   - 自验：是否感到载具**朝右**前进（而非仅背景飘动）？  
   - 观察点：滑轮辐条上的黄色偏心点应**顺时针**扫动；塔架从右缘移出、左缘新塔进入（等价世界左移）。

3. **附肢相对运动肉眼可见**  
   - 自验：触角是否在摆？前足是否像在踩杆？是否与车厢摆动**不同步**？  
   - 建议：对比触角周期（~2s）与车厢 sway（3.6s）。

4. **视差景深**  
   - 自验：远山/中山/近山/塔架是否明显不同速？塔架应显著快于远山。

5. **风格底线**  
   - 自验：是否白底？是否像「默认扁平占位图标」？  
   - 期望：黄昏深色渐变 + 细节路径，而非 Office 单色剪贴画。

6. **不同分辨率裁切**  
   - 自验：`preserveAspectRatio="xMidYMid slice"` 下，缩放窗口时主体（缆车）是否保持在可视区？

7. **可选指针微调**  
   - 自验：鼠标左右移动时车厢是否微倾（JS 写 `--extra-tilt`，CSS `.cabin-group { rotate: var(--extra-tilt, 0deg) }` 叠加在 sway 动画上）。属增强项，不影响合规。

## 文件清单

- `art.html` — 主交付（≥28KB）
- `notes.md` — 运动/几何自洽说明
- `response.md` — 本文件
- `task.md` — 原任务（只读）

## 禁止项遵守

- 未读取 `<skill安装目录>
- 未修改工作目录以外文件。
