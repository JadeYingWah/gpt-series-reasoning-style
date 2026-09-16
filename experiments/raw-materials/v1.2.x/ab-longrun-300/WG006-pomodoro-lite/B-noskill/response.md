# response.md · WG006-pomodoro-lite · B-noskill

## 交付物

- `pomodoro.html` — 单文件番茄钟（HTML + CSS + JS 内联，无 CDN / 无框架 / 无外链）
- `response.md` — 本文件

## 已核对项（源码审查 + Node 可测逻辑）

| 验收项 | 结论 | 证据 |
|--------|------|------|
| 文件存在 | PASS | `pomodoro.html` 已写入工作目录 |
| 倒计时 25:00 → 0 | PASS | 初始 `DEFAULT_MINUTES = 25`；`formatMs` 输出 `MM:SS`；`tick` 用 `endAtMs - Date.now()` 递减 |
| 开始 / 暂停 / 重置 | PASS | `start()` 启动 `setInterval`；`pause()` 结算剩余毫秒并清定时器；`reset()` 恢复 `durationMs` |
| 到时状态可见 | PASS | `finish()` 将 `#status` 设为「时间到」并加 class `done` |
| 时长配置 1–60 正整数 | PASS | `parseMinutes` 用 `/^\d+$/` + 范围检查；非整数/越界显示提示并回退 |
| 无外链 / 无 CDN | PASS | 无 `<script src>`、`<link href>`、`@import`、`fetch`、`XMLHttpRequest` |
| 逻辑可被 Node 或源码审查核对 | PASS | 核心纯函数：`pad2`、`formatMs`、`parseMinutes`；计时用 wall-clock 差值，不依赖 `setInterval` 累加误差 |

### 纯函数行为（可直接在 Node 粘贴核对）

```js
function pad2(n) { return (n < 10 ? "0" : "") + n; }
function formatMs(ms) {
  if (ms < 0) ms = 0;
  var totalSec = Math.ceil(ms / 1000);
  var h = Math.floor(totalSec / 3600);
  var m = Math.floor((totalSec % 3600) / 60);
  var s = totalSec % 60;
  if (h > 0) return h + ":" + pad2(m) + ":" + pad2(s);
  return pad2(m) + ":" + pad2(s);
}
function parseMinutes(raw) {
  var s = String(raw == null ? "" : raw).trim();
  if (s === "") return null;
  if (!/^\d+$/.test(s)) return null;
  var n = parseInt(s, 10);
  if (!isFinite(n)) return null;
  if (n < 1 || n > 60) return null;
  return n;
}

// 期望：
// formatMs(0) === "00:00"
// formatMs(25*60*1000) === "25:00"
// formatMs(1500) === "00:02"   // ceil
// parseMinutes("25") === 25
// parseMinutes("1") === 1
// parseMinutes("60") === 60
// parseMinutes("0") === null
// parseMinutes("61") === null
// parseMinutes("2.5") === null
// parseMinutes("-3") === null
// parseMinutes("abc") === null
// parseMinutes("") === null
```

### 计时策略说明

- 运行时记录 `endAtMs = Date.now() + remainingMs`，`tick` 每 200ms 用墙钟差更新剩余时间，避免 `setInterval` 漂移导致到点不准。
- 暂停时把剩余量写回 `remainingMs`；重置恢复完整 `durationMs`。
- 结束后再次「开始」会从完整时长重新计时（`isDone` 分支）。

### Beep

- 实现了可选 Web Audio 正弦 beep（约 880Hz / 0.6s），无外部音频文件。
- 浏览器自动播放策略可能在无用户手势时静音；由「开始」按钮手势创建 `AudioContext`，通常可用。
- 若环境不支持 `AudioContext`，beep 静默失败，不影响「时间到」文案。

## 浏览器交互 — UNVERIFIED

本环境未打开真实浏览器做点击验收。以下步骤请用户自验：

1. 用浏览器打开 `pomodoro.html`（本地文件即可，无需服务器）。
2. 确认初始显示 `25:00`，状态「准备开始」。
3. 点「开始」→ 显示开始递减，状态「专注中…」；「开始」禁用、「暂停」可用。
4. 点「暂停」→ 时间停住，状态「已暂停」；再点「开始」→ 从剩余时间继续。
5. 点「重置」→ 回到 `25:00`，状态「准备开始」。
6. 将时长改为 `1`，点「应用」→ 显示 `01:00`；点「开始」等待到 0 → 显示 `00:00`，状态变为「时间到」（绿色），可选听到 beep。
7. 输入非法值（`0`、`61`、`2.5`、`abc`）→ 出现提示「请输入 1–60 的正整数」，显示不被破坏。
8. 运行中时长输入框与「应用」应为禁用。
9. DevTools → Network：确认无任何外部请求（无 CDN）。

## Files touched

- `pomodoro.html`（新建）
- `response.md`（新建）
