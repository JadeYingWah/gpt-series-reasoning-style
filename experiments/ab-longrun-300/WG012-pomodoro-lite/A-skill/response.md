# response · WG012-pomodoro-lite · A-skill

工作目录：`<实验根目录>\ab-longrun-300\WG012-pomodoro-lite\A-skill`  
交付文件：`pomodoro.html`（单文件，无构建，无 CDN/框架）

## 协作形态（skill 要求）

单 Agent 主干。理由：单文件小交付、无并行/外部协调需求。

## 验收清单

| 项 | 结果 | 证据 |
|---|---|---|
| 文件存在 | DONE | `A-skill/pomodoro.html` 已写出 |
| 开始/暂停/重置逻辑自洽 | DONE（源码 + Node） | 状态机 `idle/running/paused/done`；`start` 在 running 时忽略；`pause` 仅 running；`reset` 清 interval 并回 idle |
| 时长配置生效 | DONE（源码 + Node） | `clampMinutes` 限制 1–60 整数；idle/done 下 change 刷新 remaining；running/paused 禁用输入 |
| 到时状态可见 | DONE（源码） | `remaining<=0` → `state="done"`，`#status` 文案「时间到」并加 class `done`；附 Web Audio beep |
| 无外链 | DONE（源码 + Node） | 无 `http(s)://`、无 `cdn`、无外部 `script src` / `link href`；beep 用 Web Audio API |
| response 有证据或 UNVERIFIED | DONE | 见下；浏览器交互 UNVERIFIED |

## Node 逻辑核对（实测输出）

命令：`node test-logic.js`（同目录 harness，函数体与 HTML 内嵌逻辑一致）

```
PASS all assertions (helpers + source checks)
clampMinutes(0.9,1,25.7,60,61,NaN) = 1,1,25,60,60,25
formatTime(0,59,60,1500) = 00:00 | 00:59 | 01:00 | 25:00
```

纯函数暴露于 `window.__pomodoroLite`：`clampMinutes` / `formatTime` / `getState` / `start` / `pause` / `reset`。

### 状态机要点（源码审查）

- `start`：idle/done → 按当前输入重算 remaining 后 running；paused → 从 remaining 续跑；running 忽略。
- `pause`：仅 running → paused，`clearInterval`。
- `reset`：任意状态 → idle，remaining = 输入×60。
- tick 每秒 `remaining--`，到 0 置 done 并 `clearInterval` + `beep()`。
- running/paused 时 `#minutes` 禁用，避免配置与倒计时冲突。
- 默认显示 `25:00`，状态「就绪」。

### Beep

到时用 `AudioContext` 播 880Hz / 0.35s 正弦（gain 0.08）。无外部音频文件。失败静默（`try/catch`）。

## 浏览器交互 UNVERIFIED

本环境未打开真实浏览器做点击验收。请用户自验：

1. 用浏览器打开 `pomodoro.html`（双击或 `file://`）。
2. 默认显示 `25:00`，状态「就绪」。
3. 点「开始」→ 数字每秒减 1，状态「进行中」，「开始」禁用、「暂停」可点。
4. 点「暂停」→ 数字停住，状态「已暂停」；再「开始」继续。
5. 将「时长」改为 `1`，点「重置」→ 显示 `01:00`。
6. 改时长为 1，「开始」后等约 60 秒 → 显示 `00:00`，状态「时间到」，可听到一声 beep。
7. DevTools Network：无外部请求。
8. 可选：控制台执行 `__pomodoroLite.getState()` 查看 `{state, remaining, display, status}`。

## 未做 / 边界

- 不持久化配置（刷新回 25）。
- 不支持秒级自定义（规格只要求分钟 1–60）。
- 无音量/静音开关（规格未要求）。
