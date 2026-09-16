# response.md · WG014-pomodoro-lite · B-noskill

## 交付物

| 文件 | 说明 |
|------|------|
| `pomodoro.html` | 单文件极简番茄钟（无 CDN / 无框架 / 无外链） |
| `verify-pomodoro.js` | Node 源码核对脚本（可重复执行） |
| `response.md` | 本文件 |

## 已核对项（有证据）

| 验收项 | 结果 | 证据 |
|--------|------|------|
| 文件存在 | PASS | `pomodoro.html` 已写入本目录 |
| 开始/暂停/重置逻辑自洽 | PASS | Node harness 46/46 PASS（见下） |
| 时长配置生效 | PASS | `setDuration(1/60/0/61/25.9)` 边界 + 运行中拒绝，harness 全过 |
| 到时状态可见 | PASS | `status === "时间到"`，`done === true`，`remaining === 0` |
| 无外链 | PASS | 全文无 `http(s)://`；无 `src`/`href` 外链属性 |
| response 有证据或 UNVERIFIED | PASS | 本文件 + harness 输出 |

## 行为规格（从源码抽出）

核心逻辑在 `<script id="core">`，无 DOM，可注入 `now` 时钟：

```js
createPomodoro({ totalSeconds, now })
  .start() / .pause() / .reset([totalSeconds]) / .setDuration(minutes)
  .tick()            // 墙钟推进；返回 true = 本次跨越到 0
  .getState()        // { totalSeconds, remaining, running, done, status }
  .format()          // "MM:SS"
```

状态机：

- 初始 `就绪` → `start()` → `进行中`
- `pause()` 结算 elapsed 后 → `已暂停`
- `reset()` → `就绪`（可用当前配置分钟数）
- `remaining==0` → `done=true`，`status="时间到"`，之后 `start`/`tick` 为 no-op

时长：1–60 分钟正整数。`setDuration` 先 `Math.floor(minutes)` 再 `*60`，`clampInt(60, 3600)`。运行中或已结束后拒绝修改（需先重置）。

提示音：Web Audio 双音（880→660Hz）。无外部音频文件。浏览器自动播放策略可能拦截——已在用户点击「开始」时尝试 `resume()`；若仍被拦则静默结束，状态文案仍显示「时间到」。

## Node 证据（可复现）

```text
$ node verify-pomodoro.js
PASS: default totalSeconds = 1500 (25:00)
PASS: format() === 25:00
PASS: initial status 就绪
PASS: initial not running
PASS: start() sets running/进行中
PASS: after 3s remaining=57
PASS: format 00:57 after 3s
PASS: pause() clears running
PASS: pause settles remaining to 55
PASS: status 已暂停
PASS: tick while paused does not change remaining
PASS: reset restores remaining
PASS: reset status 就绪
PASS: reset clears done
PASS: tick returns true on completion edge
PASS: done === true after full duration
PASS: remaining === 0
PASS: status 文案 = 时间到
PASS: completion emits once
PASS: cannot start after done
PASS: tick after done is no-op
PASS: setDuration(1) ok
PASS: 1 minute => 60s
PASS: setDuration(60) ok
PASS: 60 minutes => 3600s
PASS: setDuration(0) clamps to min
PASS: 0 clamps to 60s
PASS: setDuration(61) clamps to max
PASS: 61 clamps to 3600s
PASS: setDuration(25.9) floors
PASS: 25.9 floors to 25 min
PASS: setDuration blocked while running
PASS: setDuration allowed after pause
PASS: duration applied after pause
PASS: reset(900) sets 15 min
PASS: format 15:00
PASS: no http(s) src/href attributes (no CDN/外链)
PASS: no absolute http(s) URLs anywhere in file
PASS: UI element #time present
PASS: UI element #status present
PASS: UI element #startBtn present
PASS: UI element #pauseBtn present
PASS: UI element #resetBtn present
PASS: UI element #minutes present
PASS: UI element #applyBtn present
PASS: completion 文案 时间到 present in source

--- harness finished ---
RESULT: ALL PASS
```

复现：

```powershell
node .\verify-pomodoro.js
```

## 浏览器交互：UNVERIFIED

本环境未打开真实浏览器做点击流验收。以下项目请用户自验：

1. **打开** `pomodoro.html`（双击或 `Start-Process pomodoro.html`）
2. **默认**：显示 `25:00`，状态「就绪」
3. **点「开始」**：倒计时走动，状态「进行中」，「开始」禁用、「暂停」可用
4. **点「暂停」**：数字停住，状态「已暂停」；再「开始」继续（不重置）
5. **点「重置」**：回到当前配置的完整时长，状态「就绪」
6. **改时长**：输入 `1` → 点「应用时长」→ 显示 `01:00`；输入 `60` → `60:00`；输入 `0` 或 `61` 或 `abc` → 出现红字「请输入 1–60 的整数分钟」
7. **到时**（可用 `1` 分钟快速验，或 Console 执行 `window.__pomodoro.pom.reset(2); window.__pomodoro.pom.start();` 后等 2 秒）：
   - 显示 `00:00`
   - 状态变为 **「时间到」**（红色加粗）
   - 若浏览器允许音频，会听到双音 beep；若静音策略拦截则无声——**状态文案仍会变**
8. **到时后再点「开始」**：无反应（需先「重置」）
9. **DevTools Network**：确认无任何外部请求

## 已知限制

- Beep 依赖 Web Audio + 用户手势解锁；部分浏览器/策略下静默（状态文案不受影响）
- 精度：按秒推进（≥1000ms 才减 1s）；后台标签页可能被节流，前台准确
- 不持久化配置（刷新回到 25:00）
- 非无障碍全面 WCAG 审计；已有 `aria-live` 与 button 语义

## 验收清单勾选

- [x] 文件存在
- [x] 开始/暂停/重置逻辑自洽
- [x] 时长配置生效
- [x] 到时状态可见
- [x] 无外链
- [x] response 有证据或 UNVERIFIED
