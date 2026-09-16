# response · WG012-pomodoro-lite

工作目录：`<实验根目录>\ab-longrun-300\WG012-pomodoro-lite\B-noskill`
交付文件：`pomodoro.html`（单文件，无构建）

## 验收清单

| 项 | 结果 | 证据 |
|---|---|---|
| 文件存在 | DONE | `B-noskill/pomodoro.html` 已写出 |
| 开始/暂停/重置逻辑自洽 | DONE（源码） | 状态机 `idle/running/paused/done`；`start` 不可重复启动；`pause` 仅在 running；`reset` 清定时器并回到 idle |
| 时长配置生效 | DONE（源码） | `parseDurationInput` → `clampMinutes` 限制 1–60 整数；idle/done 下 change 即刷新 remaining；running/paused 禁改输入 |
| 到时状态可见 | DONE（源码） | `remaining==0` → `state="done"`，`#status` 文案「时间到」并加 class `done` |
| 无外链 | DONE | 全文件无 `http://` / `https://` / `cdn` / `src=` 外部资源；仅本地 CSS/JS |
| response 有证据或 UNVERIFIED | DONE | 见下；浏览器交互 UNVERIFIED |

## 源码逻辑核对（可被 Node / 审查复核）

纯函数暴露于 `window.__pomodoroLite`：`formatTime` / `clampMinutes` / `getState`。

等价逻辑（Node 可直接验）：

```js
function clampMinutes(n) {
  if (!isFinite(n) || isNaN(n)) return 25;
  n = Math.floor(n);
  if (n < 1) return 1;
  if (n > 60) return 60;
  return n;
}
function formatTime(totalSeconds) {
  var s = Math.max(0, totalSeconds | 0);
  var m = Math.floor(s / 60);
  var r = s % 60;
  return (m < 10 ? "0" : "") + m + ":" + (r < 10 ? "0" : "") + r;
}
// 期望：
// clampMinutes(0.9)===1; clampMinutes(25.7)===25; clampMinutes(60)===60; clampMinutes(61)===60; clampMinutes(NaN)===25
// formatTime(0)==="00:00"; formatTime(59)==="00:59"; formatTime(60)==="01:00"; formatTime(1500)==="25:00"
```

状态机要点：
- `start`: idle → 立刻按输入重算 `remaining`；done → 重新拉满后 running；running 时忽略。
- `pause`: 仅 running → paused；`clearTimer`。
- `reset`: 任意状态 → idle，remaining = 当前输入×60。
- tick 每秒 `remaining--`，到 0 置 done 并 `clearInterval`。
- 运行/暂停期间 `#minutes` 禁用，避免配置与倒计时冲突。

无 beep：未使用 Audio / WebAudio；hint 文案已说明「未启用提示音（单文件无音频资源）」。

## 浏览器交互 UNVERIFIED

本环境未打开真实浏览器做点击验收。请用户自验：

1. 用浏览器打开 `pomodoro.html`（双击或 file://）。
2. 默认显示 `25:00`，状态「就绪」。
3. 点「开始」→ 数字每秒减 1，状态「进行中」，「暂停」可点。
4. 点「暂停」→ 数字停住，状态「已暂停」；再「开始」继续。
5. 改「时长」为 1，点「重置」→ 显示 `01:00`。
6. 改时长为 1，「开始」后等 60 秒 → 显示 `00:00`，状态「时间到」。
7. DevTools Network：无外部请求。
8. 可选：控制台执行 `__pomodoroLite.getState()` 看状态与文案。

## 未做 / 边界

- 不提供结束 beep（规格允许「无则说明」）。
- 不持久化配置（刷新回 25）。
- 不依赖任何 skill / CDN / 框架。
