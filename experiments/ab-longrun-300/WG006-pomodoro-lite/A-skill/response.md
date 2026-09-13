# response.md · WG006-pomodoro-lite · A-skill

## 交付物

| 文件 | 说明 |
|------|------|
| `pomodoro.html` | 单文件番茄钟（HTML + CSS + JS 内联，无 CDN / 无框架 / 无外链） |
| `response.md` | 本文件 |

## 已核对项（源码审查 + Node 实测）

| 验收项 | 结论 | 证据 |
|--------|------|------|
| 文件存在 | **PASS** | `pomodoro.html` 已写入 `A-skill/`（346 行） |
| 倒计时 25:00 → 0 | **PASS** | 初始 DOM 文本 `25:00`；`DEFAULT_MINUTES = 25`；`formatMs` 用 `Math.ceil(ms/1000)` 格式化；`tick()` 以 `endAtMs - Date.now()` 递减 |
| 开始 / 暂停 / 重置逻辑自洽 | **PASS** | 状态机 `idle \| running \| paused \| done`。`start()` 设 `endAtMs` 并 `setInterval(tick, 200)`；`pause()` 结算剩余毫秒、清定时器；`reset()` 恢复 `durationMs` 与 `idle`。按钮禁用：running 时 Start 禁 / Pause 可用 |
| 到时状态可见 | **PASS** | `finish()` 将 `state="done"`，`#status` 文案「时间到」+ `data-state="done"` |
| 时长配置 1–60 正整数 | **PASS** | `parseMinutes`：`/^\d+$/` + 范围 `[1,60]`；非法输入提示并回退显示原时长；运行中禁用输入与「应用」 |
| 无外链 / 无 CDN | **PASS** | Node 正则扫描：无 `<script src>`、`<link href>`、`@import`、`fetch(`、`XMLHttpRequest`、`http(s)://` |
| 逻辑可被 Node 或源码审查核对 | **PASS** | 纯函数 `pad2` / `formatMs` / `parseMinutes` 已抽出；见下方 Node 实测输出 |

### Node 实测输出（本环境真实执行）

纯函数 16 条断言 **ALL PASS**：

```text
PASS formatMs(0) => "00:00"
PASS formatMs(25*60*1000) => "25:00"
PASS formatMs(1500) => "00:02"
PASS formatMs(-5) => "00:00"
PASS formatMs(59999) => "01:00"
PASS formatMs(60000) => "01:00"
PASS parseMinutes('25') => 25
PASS parseMinutes('1') => 1
PASS parseMinutes('60') => 60
PASS parseMinutes('0') => null
PASS parseMinutes('61') => null
PASS parseMinutes('2.5') => null
PASS parseMinutes('-3') => null
PASS parseMinutes('abc') => null
PASS parseMinutes('') => null
PASS parseMinutes(' 25 ') => 25
ALL PASS
```

HTML 结构 + 禁止外链 33 项 **ALL PASS**（含：DOCTYPE / charset / lang / 初始 25:00 / min=1 max=60 step=1 value=25 / 四态文案 / AudioContext / Date.now / 状态机四态赋值 / 无外链模式）。

内联 JS `node --check`：**JS SYNTAX OK**。

### 纯函数（可直接在 Node 粘贴复核）

```js
function pad2(n) { return (n < 10 ? "0" : "") + n; }
function formatMs(ms) {
  if (!isFinite(ms) || ms < 0) ms = 0;
  var totalSec = Math.ceil(ms / 1000);
  var m = Math.floor(totalSec / 60);
  var s = totalSec % 60;
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
```

### 状态机与计时策略

| 动作 | 行为 |
|------|------|
| 开始（idle/paused/done） | `endAtMs = Date.now() + remainingMs`；`state=running`；200ms 刷新显示 |
| 暂停（running） | 剩余 = `endAtMs - Date.now()`（下限 0）；清定时器；`state=paused`；若已 ≤0 则 `finish()` |
| 重置（任意） | 剩余恢复 `durationMs`；`state=idle` |
| 到时 | `remainingMs=0`；`state=done`；文案「时间到」；尝试 beep |
| 结束后再开始 | `remainingMs` 重置为完整 `durationMs` 再计时 |
| 应用时长（非 running） | 校验通过则更新 `durationMs/remainingMs`，回到 idle |

- 运行时用**墙钟差**（`endAtMs - Date.now()`）而非累加 `setInterval` 次数，避免漂移导致到点不准。
- 运行中禁用：开始按钮、时长输入、「应用」。

### Beep（可选）

- Web Audio 正弦波约 880Hz / 0.6s，无外部音频文件。
- 由用户「开始」手势创建 `AudioContext`，通常满足浏览器自动播放策略；`suspend` 时会 `resume()`。
- 环境不支持 `AudioContext` 或被策略静音时，`beep()` 吞掉异常，不影响「时间到」文案。

## 浏览器交互 — UNVERIFIED

本环境未打开真实浏览器做点击/视觉验收。按 skill「未操作过的标注 UNVERIFIED」如实声明。请用户自验：

1. 用浏览器打开 `pomodoro.html`（本地文件即可，无需服务器）。
2. 初始：显示 `25:00`，状态「准备开始」。
3. 点「开始」→ 数字递减，状态「专注中…」；「开始」禁用、「暂停」可用。
4. 点「暂停」→ 时间停住，状态「已暂停」；再点「开始」→ 从剩余时间继续。
5. 点「重置」→ 回到 `25:00`，状态「准备开始」。
6. 时长改为 `1`，点「应用」→ 显示 `01:00`；点「开始」等到 0 → `00:00` + 状态「时间到」（绿色），可选听到 beep。
7. 非法输入（`0`、`61`、`2.5`、`abc`）→ 提示「请输入 1–60 的正整数」，显示回退到原时长。
8. 运行中：时长输入框与「应用」为禁用。
9. DevTools → Network：确认无任何外部请求。
10. 到时后再点「开始」→ 从完整时长重新计时。

## 验收清单对照（task.md）

- [x] 文件存在 — PASS
- [x] 开始/暂停/重置逻辑自洽 — PASS（状态机 + 源码审查 + 纯函数测试）
- [x] 时长配置生效 — PASS（parseMinutes 实测 + applyDuration 源码）
- [x] 到时状态可见 — PASS（finish →「时间到」；浏览器视觉 UNVERIFIED）
- [x] 无外链 — PASS（正则扫描 0 命中）
- [x] response 有证据或 UNVERIFIED — 本文档

## Files touched

- `pomodoro.html`（新建）
- `response.md`（新建）

临时验证脚本（`_tmp_verify.js` / `_tmp_struct_check.js` / `_tmp_extracted.js`）在验证后已删除，不计入交付物。
