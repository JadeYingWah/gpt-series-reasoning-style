# response.md · WG014-pomodoro-lite · A-skill

## 交付物

| 文件 | 说明 |
|------|------|
| `pomodoro.html` | 单文件极简番茄钟（无 CDN / 无框架 / 无外链） |
| `verify-pomodoro.js` | Node 源码核对脚本（可复现） |
| `response.md` | 本文件 |

## Skill 执行摘要

- Skill：`gpt-series-reasoning-style`（阶段1 load-proof 已完成）
- 形态：单 Agent 主干（父任务已明确「阶段2·实现」并授权交付；子代理按指令自主执行）
- 风险：轻–中（指令完整指定产物类型/位置/形态，单目录可逆，无外部副作用）
- 资源盘点：task.md 验收清单 + 阶段1 load-proof；未引用外部实现
- 门禁：父代理「阶段2·实现 + 交付 pomodoro.html + response.md」视为本阶段实现授权

## 已核对项（有证据）

| 验收项 | 结果 | 证据 |
|--------|------|------|
| 文件存在 | PASS | `pomodoro.html` / `verify-pomodoro.js` / `response.md` 已写入本目录 |
| 开始/暂停/重置逻辑自洽 | PASS | Node harness 全过：start/pause/resume/reset 状态机与 remaining 结算 |
| 时长配置生效 | PASS | `setDuration(1/60/0/61/25.9)`；运行中/结束后拒绝；null/空/非数拒绝 |
| 到时状态可见 | PASS | `status === "时间到"`，`done === true`，`remaining === 0`，`format === "00:00"` |
| 无外链 | PASS | 无 `http(s)://`；无外部 `script src` / `link href`；无框架标记 |
| response 有证据或 UNVERIFIED | PASS | 本文件 + 下方 harness 输出 |

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
- `pause()` 结算 elapsed 后 → `已暂停`；再 `start()` 从剩余继续
- `reset()` → `就绪`（可选新 totalSeconds；UI 按输入框分钟重置）
- `remaining==0` → `done=true`，`status="时间到"`，之后 `start`/`tick` 为 no-op

时长：1–60 分钟。`setDuration` 拒绝 `null`/`undefined`/空串/非数；对数值 `Math.floor` 后再 `clamp` 到 `[60, 3600]` 秒。运行中或已结束后拒绝修改；暂停时允许，并会把 `remaining` 重置为新时长（「应用」语义）。

提示音：Web Audio 双音（784→988Hz），无外部音频文件。浏览器自动播放策略可能拦截——已在用户点击「开始」时尝试 `resume()`；若仍被拦则静默结束，状态文案仍显示「时间到」。

## Node 证据（可复现）

```text
$ node verify-pomodoro.js
...
--- harness finished ---
PASSED: 76 FAILED: 0
RESULT: ALL PASS
```

复现：

```powershell
cd <实验根目录>\ab-longrun-300\WG014-pomodoro-lite\A-skill
node .\verify-pomodoro.js
```

覆盖要点（节选，完整见脚本输出）：

- 默认 `25:00` / `就绪` / 未运行
- `start` → `进行中`；假时钟 3s → `00:57`
- `pause` 结算 elapsed → `已暂停`；暂停期间 `tick` 不减
- 恢复后从剩余继续；`reset` 回到完整时长与 `就绪`
- 到时：`tick` 返回 true 一次；`done`；`时间到`；`00:00`；之后不可 start
- 时长：1/60 分钟生效；0/61 clamp；25.9 floor；null/空/abc 拒绝
- 运行中禁改时长；暂停可改；结束后禁改
- 无外链、无外部 script/link、无框架

## 浏览器交互：UNVERIFIED

本环境未打开真实浏览器做点击流验收。以下项目请用户自验：

1. **打开** `pomodoro.html`（双击，或 `Start-Process pomodoro.html`）
2. **默认**：显示 `25:00`，状态「就绪」
3. **点「开始」**：倒计时走动，状态「进行中」；「开始」禁用、「暂停」可用
4. **点「暂停」**：数字停住，状态「已暂停」；再「开始」继续（不重置）
5. **点「重置」**：回到当前配置的完整时长，状态「就绪」
6. **改时长**：
   - 输入 `1` → 点「应用」→ 显示 `01:00`
   - 输入 `60` → 点「应用」→ 显示 `60:00`
   - 输入 `0` / `61` / `abc` → 红字「请输入 1–60 的整数分钟」
   - 运行中点「应用」→ 红字提示需先重置
7. **到时**（建议用 1 分钟，或 Console：`window.__pomodoro.pom.reset(2); window.__pomodoro.pom.start();`）：
   - 显示 `00:00`
   - 状态变为 **「时间到」**（红色加粗）
   - 若浏览器允许音频，会听到双音 beep；被拦截则无声——**状态文案仍会变**
8. **到时后再点「开始」**：无反应（需先「重置」）
9. **DevTools Network**：确认无外部请求

## 已知限制

- Beep 依赖 Web Audio + 用户手势解锁；部分策略下静默（状态文案不受影响）
- 精度：按秒推进（≥1000ms 才减 1s）；后台标签页可能被节流
- 不持久化配置（刷新回到 25:00）
- 非完整 WCAG 审计；已有 `aria-live` 与 button 语义

## 验收清单勾选

- [x] 文件存在
- [x] 开始/暂停/重置逻辑自洽
- [x] 时长配置生效
- [x] 到时状态可见
- [x] 无外链
- [x] response 有证据或 UNVERIFIED
