# Response · SVG006-mantis-forklift · B-noskill

工作目录：`<实验根目录>\ab-longrun-300\SVG006-mantis-forklift\B-noskill`  
未读取 `<skill安装目录> 或本目录以外项目文件；未修改本目录以外文件。

## 交付物

| 文件 | 大小 | 说明 |
|------|------|------|
| `art.html` | **42173 bytes (≥8KB)** | 单文件 HTML，CSS/JS/SVG 全内联 |
| `notes.md` | 2883 bytes | 几何/运动自洽说明 |
| `response.md` | 本文件 | 核对证据 |

## 验收清单核对

| 项 | 结果 | 证据（自动） |
|----|------|----------------|
| `art.html` 存在且 ≥8KB | **PASS** | `Get-Item` Length=42173 |
| 含 SVG 或 canvas 主体 | **PASS** | 存在 `<svg class="scene" viewBox="0 0 1200 700">`；mantis/forklift 为矢量绘制 |
| 有动画（CSS 或 JS） | **PASS** | 17 处 `@keyframes`；`.wheel-spin` / `.foreleg-*` / `.antenna-*` / `.abdomen` / `.p-*` 等 |
| 两层以上背景/视差 | **PASS** | `.p-far`（48s）/ `.p-mid`（18s）/ `.p-near`（7s）/ `.p-fore`（4.2s）四层不同时长 `translateX` |
| 附肢与载具非完全同步锁死 | **PASS** | 前足 1.6s、触角 2.2/2.5s、腹节 2.0s、中后足 1.9s、头部 1.35s，与车体轮 1.1s、车身刚体不同周期/不同变换 |
| 无外部资源依赖 | **PASS** | 扫描 `http://`、`https://`、`cdn.`、`unpkg`、`jsdelivr`、`googleapis`、外链 `src`/`href` → **0 命中** |
| 自洽说明存在 | **PASS** | `notes.md` + `art.html` 头部 HTML 注释 |
| response 有证据或 UNVERIFIED | **PASS** | 见下 |

## 运动方向自洽（静态结构证据）

- 注释与组结构标明 forklift **faces +X (RIGHT)**。
- 轮子：`@keyframes spinCW`（0→360°，顺时针）+ 轮辐几何 → 与右向前进一致。
- 地面/背景：`scrollLeft*` 全部 `translateX(0 → -1200px)` → 相对镜头向左 → 主体相对向右。
- 排气 `.puff` 向 `translate(-48px,-22px)` 飘散 → 气流朝车后（左）。

## 附肢相对运动清单（≥2）

1. **捕捉式前足** `.foreleg-l` / `.foreleg-r`：握方向盘开合，1.6s，反相。
2. **触角** `.antenna-l` / `.antenna-r`：2.2s / 2.5s 不同相位摆动。
3. **腹部** `.abdomen`：2.0s 纵摆。
4. **中后足** `.mid-legs`：1.9s 踏板/支撑屈伸（两组 0.15s 相位差）。
5. **头部** `.head`：1.35s 点头。

## 视觉项（无法在无头环境完整断言）

- **UNVERIFIED** — mantis 与 forklift 在真实浏览器中的可辨认度（三角头/复眼/捕捉足、门架/货叉/护顶架是否一眼可读）。  
  **用户自验**：用浏览器打开 `art.html`，确认能认出「螳螂」和「叉车」，且朝右行驶。
- **UNVERIFIED** — 视差层次在宽屏/窄屏上是否都自然，循环是否无缝。  
  **用户自验**：缩放窗口宽度，观察天空/围栏/地面/前景是否不同速且无接缝跳变。
- **UNVERIFIED** — 附肢动画是否「看起来像在操作」而非抽搐。  
  **用户自验**：盯方向盘区域 3–5 秒，看前足是否在握持/微调，触角是否独立摆。
- **UNVERIFIED** — 轮子转速与地面滚动的线速度是否视觉匹配（是否打滑感）。  
  **用户自验**：盯轮辐与地面黄线相对运动；若地面过快/过慢，可改 `.wheel-spin` 的 `1.1s` 或 `.p-near` 的 `7s`。
- **UNVERIFIED** — 整体美术风格是否「非白底扁平占位」。  
  **用户自验**：确认天空黄昏渐变、工业黄车身、警戒条纹、货箱「FRAGILE」等细节存在。

## 复现命令（PowerShell）

```powershell
cd '<实验根目录>\ab-longrun-300\SVG006-mantis-forklift\B-noskill'
(Get-Item art.html).Length
Select-String -Path art.html -Pattern 'https?://|cdn\.|unpkg|jsdelivr|googleapis'
```

期望：Length ≥ 8192；第二条无输出。
