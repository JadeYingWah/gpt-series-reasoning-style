# response — WG007-pomodoro-lite · A-skill

交付物：`pomodoro.html`（单文件，无 CDN/框架）+ 本 `response.md`。

辅助证据（非交付要求，可删）：`verify-logic.js`、`verify-html.js`、`mutation-kill.js`、`browser-smoke.js`、`browser-smoke.json`、`shots/`。

Skill：`gpt-series-reasoning-style`（Phase 1 load-proof 见 `load-proof.md`；本文件为 Phase 2 实现与验收证据）。

---

## 【实现前确认】（门禁记录 · 父 Agent 授权后执行）

- **我理解的目标**：在 `A-skill/` 交付极简单文件番茄钟 `pomodoro.html` + 验收说明 `response.md`。
- **风险分档**：中 — 从零新建产物 + 双交付物，不适用轻通道；完全可逆、本地、无外部副作用。
- **形态选择**：单 Agent 主干 — 子 Agent 任务、无跨模型协调需求。
- **已盘点可用资源**：
  - 本地 skill：`gpt-series-reasoning-style`（流程主导）、`playwright`（实操验收，已用）。
  - 可复用模板：同工作区 `B-noskill/pomodoro.html` 已存在，**刻意不复用**以保持 A/B 独立；仅作存在性知悉。
  - 网络参考：无（规格已足够，不引入外链）。
  - frontend-design：已装但未主导 — 验收维度是逻辑/无外链/状态文案，任务名「极简」；视觉按克制单卡片实现。
- **最高影响问题**：倒计时漂移（用墙钟 `endTime` 而非累加 interval）；浏览器 beep 策略拦截（静默降级 + 文案仍「时间到」）；时长输入非法值污染配置。
- **推荐方案**：纯函数 core（parse/format/remaining/transition）+ DOM 壳；Node 可抽取 core 断言；mutation-kill 证明检测力；Playwright 无头实操。
- **其他选项**：localStorage 持久化（规格未要求，否）；秒级 setInterval 累加（漂移，否）；复制 B-noskill（污染对照，否）。
- **完整计划**：实现 → Node 抽取测 pure core → HTML 静态无外链 → mutation-kill → Playwright 交互+截图 → 本文件。
- **澄清方式**：父 Agent 指令「阶段2·实现 / 交付两文件 / 只写 A-skill」= 显式委托，已记录后继续。
- **需要你确认**：无（浏览器听感/真机音量不在本环境可证范围，见 UNVERIFIED）。

---

## 验收清单

| 验收项 | 结果 | 证据 |
|--------|------|------|
| 文件存在 | **PASS** | `A-skill/pomodoro.html`（13685 bytes） |
| 倒计时 25:00 → 0 | **PASS** | 默认 `DEFAULT_MINUTES=25`；`formatMs(25*60*1000)==="25:00"`；Playwright start 1.3s 后 `24:59` |
| 开始/暂停/重置逻辑自洽 | **PASS** | 纯状态机 `ready/running/paused/done`；Node 转移表全绿；Playwright 点按：开始→进行中、暂停冻结时钟、继续、重置回 25:00 就绪 |
| 时长配置生效 | **PASS** | 仅 1–60 正整数；Playwright：`5`→`05:00`，`0/61/abc`→提示且不改配置 |
| 到时状态可见 | **PASS** | `finish` → `状态「时间到」` + `00:00` + 红色强调；截图 `shots/05-finished.png` |
| 无外链 | **PASS** | `verify-html.js` + Playwright network：除本 `file://` 文档外 0 个 http(s) 请求 |
| response 有证据或 UNVERIFIED | **PASS** | 本文件；浏览器已实操，听感见 UNVERIFIED |
| 可选 beep | **已实现** | Web Audio 正弦 740Hz ~0.6s；无外链音频文件；失败静默，状态仍「时间到」 |

---

## 设计要点（审查用）

1. **墙钟倒计时**：`endTime = Date.now() + remainingMs`，tick 只读 `remainingFrom(endMs, nowMs)`，后台标签页回来不漂移。
2. **显示取整**：`Math.ceil(ms/1000)` — 刚开始约 1s 内仍显示 `25:00`（已耗尽不足 1s），属预期；到 0 时保证 `00:00`。
3. **配置锁定**：`running/paused` 禁用时长输入；`done` 后解锁；`done`+开始 = 按当前配置开新一轮。
4. **纯函数 core**：`clampMinutes / parseMinutes / formatMs / minutesToMs / remainingFrom / transition` 与 DOM 分离；`verify-logic.js` **从 HTML 抽取**后 vm 执行，无手工拷贝漂移。

---

## Node 证据

### `node verify-logic.js`（从 pomodoro.html 抽取 pure core）

```text
OK   MIN_MINUTES -> 1
OK   MAX_MINUTES -> 60
OK   DEFAULT_MINUTES -> 25
OK   parse "25" -> 25
OK   parse "1" -> 1
OK   parse "60" -> 60
OK   parse "  10  " -> 10
OK   parse "007" -> 7
OK   parse "0" -> null
OK   parse "61" -> null
OK   parse "25.5" -> null
OK   parse "-5" -> null
OK   parse "abc" -> null
OK   parse "" -> null
OK   parse null -> null
OK   format 0 -> "00:00"
OK   format -1 -> "00:00"
OK   format 1 -> "00:01"
OK   format 999 -> "00:01"
OK   format 60000 -> "01:00"
OK   format 25min -> "25:00"
OK   format 59m58.5s remaining -> "59:59"
OK   format just under 60min -> "60:00"
OK   remaining future -> 1500
OK   remaining past clamps 0 -> 0
OK   remaining equal 0 -> 0
OK   25min ms -> 1500000
OK   ready+start -> "running"
OK   ready+start status -> "进行中"
OK   running+pause -> "paused"
OK   paused+start -> "running"
OK   running+reset -> "ready"
OK   paused+reset -> "ready"
OK   running+tick0 -> "done"
OK   running+tick0 status -> "时间到"
OK   running+tick0 finished flag -> true
OK   running+tick>0 no-op -> null
OK   done+start restarts -> "running"
OK   done+reset -> "ready"
OK   done+setMinutes -> "ready"
OK   ready+start zero rejected -> null
OK   ready+setMinutes -> "ready"
OK   running+setMinutes ignored -> null
OK   sim remaining 3000 -> 3000
OK   sim remaining 1000 -> 1000
OK   sim remaining 0 -> 0
OK   sim format mid -> "00:02"
OK   sim format end -> "00:00"
OK   default cycle ms -> 1500000
OK   default display -> "25:00"
ALL PASS (extracted from pomodoro.html pure core)
```

### `node verify-html.js`

```text
HTML static checks PASS
bytes 13685
script tags 1
external refs 0
markers wallClock, setInterval, clearInterval, audioBeep, stateMachine, finishedStatus, defaultMinutes, pureParse, pureFormat, pureTransition
```

### `node mutation-kill.js`（检测力：防的错误做一次必须红）

```text
CONTROL PASS (clean HTML -> green)
KILLED  parseMinutes accepts 0 (drop MIN check)
KILLED  formatMs floors instead of ceils
KILLED  remainingFrom does not clamp negative
KILLED  finish status string wrong
KILLED  pause never fires from running
KILLED  default minutes not 25
---
killed 6/6
mutation-kill PASS
```

---

## 浏览器交互 — 已实操（Playwright headless Chrome）

方法：`playwright-core` + 系统 Chrome channel；真实 click/fill；`shots/*.png` 截图；`Date.now` 偏移 +61s 触发到时（不空等 60s）。完整记录：`browser-smoke.json`。

| 检查 | 结果 |
|------|------|
| 初始 25:00 / 就绪 / 开始 | PASS |
| 开始 → 进行中 / 暂停 / 锁配置 | PASS |
| 1.3s 后显示 24:59 | PASS |
| 暂停冻结时钟（400ms 不变） | PASS |
| 继续 → 进行中 | PASS |
| 重置 → 25:00 / 就绪 / 解锁 | PASS |
| 时长 5 → 05:00 | PASS |
| 非法 0 / 61 / abc → 提示且不改配置 | PASS |
| 到时 → 00:00 / 「时间到」/ 开始 / 解锁 | PASS |
| 无 http(s) 外链请求 | PASS |

截图（`shots/`）：`01-ready.png`、`02-running.png`、`03-paused.png`、`04-reset.png`、`05-finished.png`。  
已人工查看 ready 与 finished：卡片清晰，到时红色强调「时间到」可见。

复跑（需临时安装，非交付依赖）：

```bash
cd A-skill
npm install --no-save playwright-core
node browser-smoke.js
node verify-logic.js
node verify-html.js
node mutation-kill.js
```

---

## UNVERIFIED / 用户自验

1. **真机扬声器听感**：headless 中 `playBeep()` 返回成功并更新 note，但本环境无法证明您能听到 740Hz 提示音。请到时留意是否有声；无声时检查浏览器是否自动播放/音频策略拦截——状态文案仍应为「时间到」。
2. **非 Chrome 浏览器**：仅在 headless Chrome（channel）验证。请用 Edge/Firefox/Safari 打开再点一轮。
3. **长时间跑满 25 分钟**：finish 用时钟偏移验证；未实跑 25 分钟墙钟。
4. **刷新行为**：无 localStorage，刷新丢进度（预期）。未在浏览器里专项点验刷新，属设计说明。

---

## 已知边界 / 预期行为

- 无持久化：刷新回到输入框当前值对应的就绪态。
- 显示 `ceil`：开始后约 1 秒内可能仍见 `25:00`。
- Beep 依赖 AudioContext；失败静默。
- 时长输入仅在非运行/暂停时可改；「重置」会先尝试应用当前输入再回到配置时长。

## Files touched（仅 A-skill）

- **交付**：`pomodoro.html`、`response.md`
- **证据**：`verify-logic.js`、`verify-html.js`、`mutation-kill.js`、`browser-smoke.js`、`browser-smoke.json`、`shots/01-ready.png`…`05-finished.png`
- **未改动**：`task.md`、`load-proof.md`、B-noskill/**、meta.json
