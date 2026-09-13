# WG001-pomodoro-lite · B 臂交付说明

## 交付物

| 文件 | 说明 |
|------|------|
| `pomodoro.html` | 单文件番茄钟（HTML+CSS+JS，无外链） |
| `verify.js` | Node 逻辑核对脚本（状态机 + 静态检查） |
| `response.md` | 本说明 |

浏览器直接打开：`pomodoro.html`（双击或 `file://`）。

---

## 验收清单对照

| 条目 | 结果 | 证据 |
|------|------|------|
| 文件存在 | ✅ | `pomodoro.html` 已写入本目录 |
| 开始/暂停/重置逻辑自洽 | ✅ 核对 | 见下方 Node 结果 |
| 时长配置生效 | ✅ 核对 | `validateMinutes` 边界 + `setMinutes` 重置剩余时间 |
| 到时状态可见 | ⚠️ 逻辑已核对 / UI **UNVERIFIED** | 状态机 `finished` 后文案绑定「时间到」；真实渲染需用户自验 |
| 无外链 | ✅ 核对 | 静态扫描 0 处 `src`/`href` 外链、无 CDN |
| response 有证据或 UNVERIFIED | ✅ | 本文件 |

---

## 已核对项（Node，可复现）

```text
node verify.js
```

本机已执行，结果：**36 passed, 0 failed**。摘要：

- **formatClock**: `1500→25:00`, `0→00:00`, `59→00:59`, `60→01:00`, 负值钳到 `00:00`
- **validateMinutes**: `25/1/60` 合法；`0/61/abc/2.5` 拒绝
- **开始/暂停**: `start→running`；`pause→!running`；暂停期间 `remaining` 不变；暂停时 `tick` 忽略
- **推进**: 运行中 10 次 `tick` → `1500→1490`
- **重置**: 回到完整时长且清 `finished`
- **到时**: 1 分钟从 60 次 `tick` → `remaining=0, finished=true, running=false`；完成后不可再 start/tick
- **setMinutes**: 运行中改时长会重置为新总秒数且停止；`0`/`61` 抛 `RangeError`
- **无外链**: 无 `https?://` 资源引用、无 `script src` / `link href`

实现要点（便于源码审查）：

1. 逻辑集中在 `var Pomodoro = (function () { ... })()`：`createTimer` / `formatClock` / `validateMinutes`，与 DOM 解耦。
2. 每秒 `setInterval(..., 1000)` 驱动 `tick()`；仅 `running && !finished` 时递减。
3. 结束文案：`finished` 时 `#status` 显示 **时间到**；进行中「进行中」，暂停「已暂停」，初始「就绪」。
4. **Beep**：`Web Audio`（`AudioContext`）880Hz 约 0.45s；自动播放策略或无音频设备时 try/catch 静默忽略，**文案不受影响**。
5. 时长输入：`type=number`，经 `validateMinutes` 要求 **1–60 正整数**（拒绝小数/空/越界）。

---

## 浏览器交互 UNVERIFIED

以下项目**未**在真实浏览器中自动化验证（当前环境未跑 headless 浏览器）：

1. 点击「开始」后 UI 每秒更新，且 25:00 可一路到 00:00。
2. 结束瞬间状态文案变为「时间到」，按钮态正确（开始/暂停禁用等）。
3. 可选 beep 是否在本机出声（取决于系统音量 / 浏览器自动播放策略）。
4. 修改分钟数并「应用」后，显示与计时是否立刻反映新时长。
5. 响应式布局在窄屏下是否可点。

### 用户自验步骤（约 2 分钟）

1. 用 Chrome/Edge/Firefox 打开 `pomodoro.html`。
2. 默认应显示 `25:00`、状态「就绪」。
3. 点 **开始** → 数字每秒减 1，状态「进行中」；点 **暂停** → 数字停住，状态「已暂停」；再 **开始** 接着走。
4. 点 **重置** → 回到 `25:00`、「就绪」。
5. 在「时长」填 `1`，点 **应用** → 显示 `01:00`；点 **开始**，约 60 秒后变为 `00:00` 且状态 **时间到**（若允许声音可听到短 beep）。
6. 填 `0`、`61`、`2.5`、空 → 出现错误提示，计时不变。
7. DevTools Network：刷新页面应无外部域名请求。

---

## 文件职责速查

- `Pomodoro.createTimer(minutes)`：纯状态机（start/pause/tick/reset/setMinutes/getState/onChange）
- `Pomodoro.formatClock(sec)`：`mm:ss`
- `Pomodoro.validateMinutes(raw)`：`{ok,value}|{ok,error}`
- bootstrap IIFE：绑按钮、秒表 interval、AudioContext beep、渲染 `#display` / `#status`
