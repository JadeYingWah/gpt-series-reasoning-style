# response · WG009-pomodoro-lite · A-skill

## 交付物

| 文件 | 说明 |
|------|------|
| `pomodoro.html` | 单文件极简番茄钟（内联 CSS + JS，无外链） |
| `check.js` | Node 源码/纯函数核对脚本（`node check.js`） |
| `response.md` | 本说明 |

形态：单 Agent 主干。任务指令具体、单文件可逆、无外部副作用；轻通道直接执行，产物证据如下。

## 实现要点

| 需求 | 实现 |
|------|------|
| 倒计时 25:00 → 0 | 默认 `configuredMinutes = 25`，显示 `formatTime(remainingMs)` |
| 开始 / 暂停 / 重置 | `#startPause` 切换 开始↔暂停；`#reset` 恢复配置总时长 |
| 结束状态「时间到」 | `finish()` 置 `finished=true`，`#status` 文案「时间到」；可选 Web Audio 880Hz 短 beep（约 0.45s，可能被浏览器手势策略拦截，文案不受影响） |
| 可配置时长 1–60 | `#minutes` number 输入 + 「应用」；`clampInt` 拒绝越界/非整数并回写原值 |
| 无 CDN/框架 | 无 `http(s)://` src/href；无 React/Vue/jQuery |

计时采用 **wall-clock**：`endAtMs = Date.now() + remainingMs`，`setInterval` 只负责刷新显示；暂停时从目标时刻回写 `remainingMs`，避免按 tick 累加漂移。

## 已核对项（Node）

命令：

```bat
cd /d <实验根目录>\ab-longrun-300\WG009-pomodoro-lite\A-skill
node check.js
```

结果：

```text
27/27 passed
```

覆盖：

- 无 CDN/外链 `src`/`href`
- `formatTime`：`25:00` / `00:00` / ceil 边界（999ms→00:01）/ 负值钳到 `00:00`
- `clampInt`：1、60 边界通过；0、61、非数字为 `null`；25.9 截断为 25
- DOM id：`startPause` / `reset`；状态文案「时间到」
- 默认 25、input `min=1` `max=60`
- start/pause/reset 与 wall-clock 源码模式自洽（`endAtMs` 写入/回写/`remainingMs` 复位）
- 无框架库关键字

## 浏览器交互 — UNVERIFIED

本环境未打开真实浏览器点按 UI。请用户自验：

1. 打开 `pomodoro.html`（双击或任意现代浏览器）。
2. 默认显示 `25:00`，状态「准备开始」。
3. 点「开始」→ 状态「专注中…」，按钮变「暂停」，数字递减。
4. 点「暂停」→ 数字停住，状态「已暂停」；再点「开始」从剩余时间继续。
5. 点「重置」→ 回到配置的完整时长，状态「准备开始」。
6. 时长改为 `1`，点「应用」→ 显示 `01:00`；约 60 秒后状态变为 **「时间到」**，可能有短 beep。
7. 时长输入 `0` / `61` / `abc` 后点「应用」→ 提示「请输入 1–60 的整数分钟」，配置不被破坏。
8. DevTools Network：仅文档本身，无第三方域名请求。
9. （可选）控制台：`__pomodoroLite.getState()`；`__pomodoroLite._setRemainingMs(1500); __pomodoroLite._finish()` 可立刻看到「时间到」。

### beep 说明

使用 `AudioContext` 正弦波 880Hz，约 0.45s。若浏览器要求用户手势或策略拦截，计时与「时间到」文案仍正常（try/catch 静默忽略）。

## 验收清单对照

- [x] 文件存在：`pomodoro.html`
- [x] 开始/暂停/重置逻辑自洽：`node check.js` 27/27
- [x] 时长配置生效：clamp 1–60 + apply/reset 路径已核对（UI 点击 UNVERIFIED）
- [x] 到时状态可见：源码含「时间到」+ `finished` 分支；实机 60s 测试 UNVERIFIED
- [x] 无外链：check.js 扫描通过
- [x] response 有证据或 UNVERIFIED：见上
