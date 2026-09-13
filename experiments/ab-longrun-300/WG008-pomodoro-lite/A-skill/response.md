# WG008-pomodoro-lite · A 臂响应（gpt-series-reasoning-style）

## 交付物

| 文件 | 说明 |
|------|------|
| `pomodoro.html` | 单文件番茄钟（HTML + CSS + 内联 JS，无 CDN/框架） |
| `verify.js` | Node 侧可复跑核对脚本（证据源） |
| `response.md` | 本响应 |

## 实现前门禁（阶段2）

- **理解的目标**：极简单文件番茄钟，默认 25:00 倒计时；开始/暂停/重置；结束文案「时间到」；时长 1–60 正整数可配；无外链；response 附证据与浏览器 UNVERIFIED。
- **风险分档**：轻-中 — 单文件本地产物、完全可逆、无外部副作用；多交付物为「主产物 + 响应文档」，形态与位置由 task.md 完整指定。
- **形态选择**：单 Agent 主干 — 任务无并行/隔离需求，无需扩展。
- **已盘点资源**：`task.md`、`load-proof.md`、skill `gpt-series-reasoning-style` v1.1.0（load-proof 记 1.2.0，以本机 SKILL.md/VERSION 为准）；同级 `B-noskill` 仅作对照不改其文件；无适用外部模板需安装。
- **推荐方案**：纯逻辑（`normalizeMinutes` / `formatTime` / `createTimer`）与 DOM 分离；`module.exports` 便于 Node `vm` 抽出断言；Web Audio beep 可降级静默。
- **授权判定**：阶段2「实现」指令 + task.md 已完整指定产物类型/位置/形态，按 skill 该指令本身即为授权，不另等用户确认。

## 已实现需求

1. **倒计时 25:00 → 0**：默认 25 分钟，`mm:ss`，`tabular-nums` 等宽。
2. **开始 / 暂停 / 重置**
   - 开始：`idle|paused|done → running`，1s `setInterval`；`done` 后再开始会满时长重启。
   - 暂停：仅 `running → paused`，停 ticker。
   - 重置：回 `idle`，剩余恢复为当前配置分钟。
3. **结束状态**：剩余到 0 → `status=done`，文案 **「时间到」**。
   - **Beep**：Web Audio 正弦 880Hz ≈0.6s；无 AudioContext / 被策略拦截则静默，文案仍可见（页面 hint 已说明）。
4. **可配置时长**：`<input type="number" min="1" max="60" step="1">`。
   - `normalizeMinutes` 仅接受 1–60 正整数；非法回退 25。
   - running/paused 时输入框 disabled，逻辑层亦忽略 `setDuration`。
5. **无 CDN/框架**：无 `http(s)`、无 `<script src>`、无 `<link href>`、无第三方库。

## 可核对架构

纯逻辑与 DOM 分离：

- `normalizeMinutes(raw, fallback)`
- `formatTime(totalSeconds) → "mm:ss"`
- `createTimer(durationMinutes)`：`idle | running | paused | done`

`typeof module !== "undefined"` 时导出；`typeof document !== "undefined"` 时才绑 UI。Node 可用 `vm` 加载脚本块断言。

## 已核对项（Node，本轮 fresh 证据）

在本目录执行：

```text
node verify.js
```

本轮实际输出：

```text
ALL CHECKS PASSED
 - no external http(s)/cdn/script src/link href
 - formatTime / normalizeMinutes / createTimer extracted via vm
 - start/pause/reset/setDuration/tick/done verified
 - duration 1–60 bounds + fallback verified
 - countdown 60s → done + restart after done verified
 - STATUS_TEXT.done is 时间到
```

| 验收项 | 证据指针 |
|--------|----------|
| 文件存在 | `pomodoro.html` / `verify.js` / `response.md` 均在 A-skill 目录 |
| 无外链 | `verify.js` 正则扫 `http(s)/cdn/script src/link href`，0 hit |
| 开始/暂停/重置自洽 | vm 断言：`start→running`，`pause→paused`，paused 中 `tick` 不减秒，resume 可继续，`reset→idle` 且 remaining 恢复 |
| 时长配置生效 | `setDuration(5)` → remaining=300、`05:00`；running 时忽略 |
| 1–60 边界 | `createTimer(1/60)` 正确；0/61/`abc`/`2.5`/`-3` 回退 |
| 到时状态可见 | 60s 倒计时至 `done`、remaining=0、`00:00`；再 start 满时长重启 |
| 状态文案 | `STATUS_TEXT.done = "时间到"`（断言存在） |

## UNVERIFIED（浏览器交互，需用户自验）

本环境无真实浏览器/GUI/音频策略，以下 **UNVERIFIED**：

1. UI 渲染、按钮点击、时长输入框交互。
2. Beep 是否实际发声（依赖用户手势解锁 AudioContext；静默属预期降级）。
3. `aria-live` 朗读、小屏/高分屏布局。

### 用户自验步骤

1. 用现代浏览器打开 `pomodoro.html`（双击即可，无需网络）。
2. 初始应显示 `25:00`、状态「就绪」。
3. 点「开始」→「计时中」，数字每秒递减；点「暂停」→「已暂停」且数字停住；再「开始」继续。
4. 点「重置」→ 回 `25:00`「就绪」（或你配置的分钟数）。
5. 时长改为 `1`，开始，等到 `00:00`，状态应变为 **「时间到」**；若允许声音则有一声短 beep。
6. 时长改为 `0` / `61` / 清空后失焦 → 应回退 `25`。
7. 计时过程中尝试改时长 → 输入框应禁用。
8. 开发者工具 Network → 确认无外部请求。

## 验收清单对照

- [x] 文件存在
- [x] 开始/暂停/重置逻辑自洽（`node verify.js` 断言）
- [x] 时长配置生效（1–60 + 回退）
- [x] 到时状态可见（文案「时间到」）
- [x] 无外链
- [x] response 有证据 + 浏览器交互 UNVERIFIED

## 范围说明

- 只写入 `A-skill/`；未改 `B-noskill`、`meta.json`、`task.md`、`load-proof.md`。
- `verify.js` 为证据支撑文件，不在 task.md 必交两项内，保留便于复跑。
