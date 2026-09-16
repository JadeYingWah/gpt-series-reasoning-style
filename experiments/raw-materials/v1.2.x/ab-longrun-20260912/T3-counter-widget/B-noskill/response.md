# T3 · 计数器 — B 臂（无 skill）操作与验收记录

## 交付文件

| 文件 | 说明 |
|------|------|
| `counter.html` | 单文件计数器，内联 CSS/JS，无 CDN / 无框架 / 无服务端 |
| `response.md` | 本文件 |

## localStorage key

- **Key**: `counter-widget-v1`
- **Value**: JSON `{"count": number, "step": number}`
- 读取时机：页面加载时 `load()` 解析并 clamp 到 [−99, 99]；损坏 JSON 忽略并回退默认值。
- 写入时机：每次 count 或 step 变更后 `save()`。
- 建议用户自验：DevTools → Application → Local Storage，或控制台执行 `localStorage.getItem("counter-widget-v1")`。

## 实际操作过的清单

本臂为无浏览器环境的命令行执行者，对 **源码逻辑** 做了 Node 核对；对 **纯 UI 交互** 标 UNVERIFIED。

### 已自动核对（Node 执行，2026-09-12）

- [x] `counter.html` 已写入工作目录
- [x] `+1 from 0` → `1`
- [x] `-1 from 0` → `-1`
- [x] `步长 5，+step from 10` → `15`
- [x] `步长 5，-step from 10` → `5`
- [x] `99 + 1` → 阻断（不越界）
- [x] `-99 − 1` → 阻断（不越界）
- [x] `95 + step 10` → clamp 到 `99`
- [x] `-95 − step 10` → clamp 到 `-99`
- [x] `parseStep("1"/"3")` → 正整数
- [x] `parseStep("abc"/"0"/"-2"/"1.5")` → `null`（拒绝非法步长）
- [x] `parseStep(" 2 ")` → `2`（trim 后接受）

> 注：Node 脚本中有 2 条对比写法上的 FAIL（`delta=0` 被设计为 no-op 返回 blocked；`want` 写成字符串 `"2"` 而非数字 `2`）。复核后 **不是产品缺陷**，逻辑符合预期。

### UNVERIFIED — 需用户浏览器自验

无法在本环境打开浏览器/点击按钮/刷新页面。请按下列步骤验证：

1. **打开页面**
   - 双击 `counter.html`，或浏览器打开 `file:///.../B-noskill/counter.html`。
   - 预期：中央大字显示 `0`，下方提示「范围 −99 ~ 99」。

2. **+1 / −1**
   - 点 `+1` 三次 → 显示 `3`。
   - 点 `−1` 一次 → 显示 `2`。

3. **重置**
   - 点 `重置` → 显示 `0`，状态短暂提示「已重置」。

4. **步长**
   - 将「步长」改为 `5`，点 `+1` → 显示 `5`；再点 `−1` → 显示 `0`。
   - 输入 `0` 或 `abc` 或 `-1` → 输入框红框，提示「请输入 ≥1 的正整数」；此时再点 `+1` 仍使用上次合法步长。

5. **±99 边界与视觉反馈**
   - 步长改为 `99`，点 `+1` → 到 `99`；`+1` 按钮变灰（disabled），数字变红，状态「已达上限 99」。
   - 再点已禁用的 `+1` 无效果（按钮禁用时不会 shake；若从 99 以下跨入，clamp 后停在 99）。
   - 将步长改回 `1`，点 `重置` 后连点 `−1` 到 `-99` → `−1` 按钮禁用，数字变红，「已达下限 −99」。
   - 边界处再点同向按钮：若按钮已 disabled 则无动画；若因 step 导致 no-op，按钮会有 shake + 红边框动画。

6. **localStorage 持久化**
   - 计数到任意非 0 值（例如 `7`），步长设为 `3`。
   - 按 F5 刷新 → 数字仍为 `7`，步长仍为 `3`。
   - 控制台：`JSON.parse(localStorage.getItem("counter-widget-v1"))` → `{"count":7,"step":3}`。
   - 执行 `localStorage.removeItem("counter-widget-v1")` 后刷新 → 回到 `0` / 步长 `1`。

7. **键盘快捷键（加分项，非任务强制）**
   - 焦点不在步长输入框时：`↑` / `+` 增加，`↓` / `-` 减少，`R` 重置。

## 验收清单对照

- [x] `counter.html` 存在
- [x] `+1/−1/重置` 逻辑正确（Node 源码级核对 + 逻辑函数单测）
- [x] 步长生效（`parseStep` + `applyDelta(state.step)`；非法输入拒绝）
- [x] `±99` 边界与反馈（clamp + disabled + 红字 + shake/status）
- [x] localStorage key 有说明（`counter-widget-v1`）
- [x] response 有实操或 UNVERIFIED 声明（两者皆有）

## 禁止项遵守

- 未引入框架 / CDN
- 未写服务端
- 未读取 `<skill安装目录> A-skill
- 仅写入 `<实验根目录>\ab-longrun-20260912\T3-counter-widget\B-noskill\`
