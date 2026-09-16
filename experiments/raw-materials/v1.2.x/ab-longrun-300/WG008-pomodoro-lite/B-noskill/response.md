# WG008-pomodoro-lite · B 臂响应

## 交付物

| 文件 | 说明 |
|------|------|
| `pomodoro.html` | 单文件番茄钟（HTML + CSS + 内联 JS，无外链/无框架） |
| `verify.js` | Node 侧源码审查/逻辑核对脚本 |
| `response.md` | 本响应 |

## 已实现需求

1. **倒计时 25:00 → 0**：默认 25 分钟，显示 `mm:ss`（tabular-nums 等宽）。
2. **开始 / 暂停 / 重置**
   - 开始：`idle|paused|done → running`，启动 1s `setInterval`；`done` 后再点开始会重新满时长计时。
   - 暂停：仅 `running → paused`，停止 ticker。
   - 重置：回 `idle`，剩余时长恢复为当前配置分钟数。
3. **结束状态**：`remaining` 到 0 时 `status = done`，状态文案变为 **「时间到」**。
   - **Beep**：使用 Web Audio（`OscillatorNode` 880Hz，约 0.6s）。若浏览器策略/不支持则静默，文案仍可见（页面 hint 已说明）。
4. **可配置时长**：`<input type="number" min="1" max="60" step="1">`。
   - `normalizeMinutes` 只接受 1–60 的正整数；非法值回退默认 25。
   - 输入框 `change` 时归一化并回写；**running/paused 时禁止修改**（输入框 disabled，逻辑也忽略）。
5. **无 CDN/框架**：无 `http(s)://`、无 `<script src>`、无 `<link href>`、无第三方库。

## 架构（可核对性）

纯逻辑与 DOM 分离：

- `normalizeMinutes(raw, fallback)`
- `formatTime(totalSeconds) → "mm:ss"`
- `createTimer(durationMinutes)` 状态机：`idle | running | paused | done`

`typeof module !== "undefined"` 时 `module.exports` 导出上述 API；`typeof document !== "undefined"` 时才绑定 UI。Node 可直接 `vm` 加载脚本块做断言（见 `verify.js`）。

## 已核对项（Node，证据）

在本目录执行：

```text
node verify.js
```

输出：

```text
ALL CHECKS PASSED
 - no external http(s)/cdn/script src/link href
 - formatTime / normalizeMinutes / createTimer extracted via vm
 - start/pause/reset/setDuration/tick/done verified
 - duration 1–60 bounds + fallback verified
 - countdown 60s → done + restart after done verified
```

覆盖的断言摘要：

| 项 | 证据 |
|----|------|
| 文件存在 | `pomodoro.html` 在本目录 |
| 无外链 | 正则扫描无 `http(s)/cdn/script src/link href` |
| 开始/暂停/重置逻辑自洽 | `start→running`，`pause→paused`，暂停中 `tick` 不减秒，`reset→idle` 且 remaining 恢复 |
| 时长配置生效 | `setDuration(5)` → remaining=300、`formatTime`=`05:00`；running 时忽略 setDuration |
| 边界 1–60 | `createTimer(1/60)` 正确；0/61/`abc`/`2.5` 回退 25 |
| 到时状态 | 60 秒倒计时至 `status=done`、`remaining=0`、显示 `00:00`；done 后 tick 不为负；再 start 重满时长 |
| 状态文案 | 源码含「时间到」；`STATUS_TEXT.done = "时间到"` |

## UNVERIFIED（浏览器交互，需用户自验）

以下无法在本环境用真实浏览器/音频策略验证：

1. **UI 渲染与按钮点击**（开始/暂停/重置/改时长）。
2. **Beep 是否实际发声**（需用户手势解锁 AudioContext；静默属预期降级）。
3. **`aria-live` 朗读**、小屏布局。

### 建议自验步骤

1. 用现代浏览器打开 `pomodoro.html`（双击或本地静态服务均可，无需网络）。
2. 确认初始显示 `25:00`、状态「就绪」。
3. 点「开始」→ 状态「计时中」，数字每秒递减；点「暂停」→「已暂停」且数字停住；再「开始」继续。
4. 点「重置」→ 回 `25:00`「就绪」（或你配置的分钟数）。
5. 把时长改为 `1`，开始，等待至 `00:00`，状态应变为 **「时间到」**；若允许声音则有一声短 beep。
6. 将时长改为 `0` 或 `61` 或清空后失焦 → 应回退为 `25`。
7. 计时过程中尝试改时长 → 输入框应禁用/无效。
8. 开发者工具 Network：确认无外部请求。

## 验收清单对照

- [x] 文件存在
- [x] 开始/暂停/重置逻辑自洽（`verify.js` 断言）
- [x] 时长配置生效（1–60 + 回退）
- [x] 到时状态可见（文案「时间到」）
- [x] 无外链
- [x] response 有证据 + 浏览器交互 UNVERIFIED
