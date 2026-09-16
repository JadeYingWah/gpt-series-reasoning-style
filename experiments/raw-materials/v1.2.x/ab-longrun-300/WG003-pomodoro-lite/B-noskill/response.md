# WG003-pomodoro-lite · B 臂响应

## 交付文件

- `pomodoro.html` — 单文件番茄钟（无 CDN / 无框架 / 无外链）
- `verify-logic.js` — 纯逻辑 Node 核对脚本（24 项断言）
- `check-html.js` — HTML 结构与无外链源码审查脚本（13 项断言）

## 已核对项（自动化证据）

在本机执行 `node verify-logic.js` 与 `node check-html.js`，输出全部 PASS。

### 定时逻辑（`verify-logic.js`，24 PASS）

| 核对点 | 结果 |
|--------|------|
| 25 分钟格式化为 `25:00` | PASS |
| 0 / 负值显示 `00:00` | PASS |
| 秒数向上取整（1ms → `00:01`） | PASS |
| 599s → `09:59`，600s → `01:00` | PASS |
| 时长校验：拒绝空、0、负数、61、小数、非数字 | PASS |
| 时长校验：接受 1 / 25 / 60 / 前后空白 | PASS |
| 到时分支：`remainingMs <= 0` → `finished` + 状态「时间到」 | PASS |
| 未到时仍 running | PASS |
| 开始 → running=true | PASS |
| 重复开始为 no-op | PASS |
| 暂停冻结 remainingMs | PASS |
| 已暂停再暂停为 no-op | PASS |
| 重置恢复 totalMs 且 running=false | PASS |

### 结构 / 无外链（`check-html.js`，13 PASS）

| 核对点 | 结果 |
|--------|------|
| 无 `<script src>` / `<link href>` / 外链 `<img>` | PASS |
| 无 `http(s)://` 字符串 | PASS |
| 关键 id：display / status / btnStart / btnPause / btnReset / minutes / btnApply | PASS |
| 状态文案含「时间到」 | PASS |
| `input` min=1 max=60 | PASS |
| 初始显示 `25:00` | PASS |
| Web Audio beep 存在（无外部音频文件） | PASS |

### 功能对照任务要求

1. 倒计时 25:00 → 0，开始 / 暂停 / 重置 — 实现于 `pomodoro.html`；逻辑经 Node 状态机断言。
2. 结束时状态文案「时间到」— 实现；另有 Web Audio 880Hz 短 beep（约 0.6s，gain 衰减）；`AudioContext` 构造失败或静音环境时静默不报错。
3. 可配置时长 1–60 分钟正整数 — 输入框 +「应用」；非法输入回显错误提示并恢复原值；运行中禁用修改。
4. 无 CDN / 框架 — 纯 HTML + 内联 CSS + 内联 IIFE JS。
5. 逻辑可被 Node 核对 — 见 `verify-logic.js`。

## 浏览器交互 UNVERIFIED

以下项**未在本环境的真实浏览器中实测**（Node 只能核对纯逻辑与源码结构）。请用户自验：

1. 用浏览器打开 `pomodoro.html`（双击或 `file://` 即可）。
2. 点「开始」→ 显示应每秒递减，状态「进行中」；「暂停」按钮变为可用。
3. 点「暂停」→ 数字冻结，状态「已暂停」；再点「开始」应从剩余时间继续。
4. 点「重置」→ 恢复当前配置的整分时长，状态「就绪」。
5. 将时长改为 `1`，点「应用」→ 显示 `01:00`；开始后约 60 秒应变为 `00:00`，状态变为**「时间到」**（加粗红字），并可能听到一声短促提示音（系统静音或不支持 Web Audio 时听不到，属预期）。
6. 时长填 `0` / `61` / `2.5` / `abc` 后点「应用」→ 状态提示「请输入 1–60 的正整数」，输入框恢复原值，计时不受影响。
7. 运行中尝试改时长 → 输入框与「应用」应为禁用。
8. DevTools → Network：确认无第三方请求（仅本地文件）。

## 验收清单对照

- [x] 文件存在（`pomodoro.html`）
- [x] 开始/暂停/重置逻辑自洽（Node 状态机 + no-op 断言 PASS）
- [x] 时长配置生效（校验 1–60 + reset 用 totalMs，PASS）
- [x] 到时状态可见（「时间到」字符串 + finished 分支 PASS；浏览器渲染 UNVERIFIED）
- [x] 无外链（源码审查 PASS）
- [x] response 有证据或 UNVERIFIED（本文件）

## 残留风险

- 浏览器 paint / focus / `aria-live` 实际效果未在 GUI 中点验。
- Web Audio 在个别浏览器需用户手势后才可出声（首次点「开始」即为手势，通常可响）。
