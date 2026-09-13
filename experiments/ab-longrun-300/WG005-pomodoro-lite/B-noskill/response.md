# WG005-pomodoro-lite · B 臂交付说明

## 交付物

| 文件 | 说明 |
|------|------|
| `pomodoro.html` | 单文件极简番茄钟（无 CDN / 无框架 / 内联 CSS+JS） |
| `verify-core.js` | Node 核心逻辑核对脚本（从 HTML 提取 `PomodoroCore` 后跑用例） |
| `response.md` | 本说明 |

复现核对：

```bash
node verify-core.js
```

---

## 已核对项（Node / 源码审查，非浏览器）

命令输出：**36/36 passed**（工作目录下执行 `node verify-core.js`）。

### 交付清单对照

| 验收项 | 结果 | 证据 |
|--------|------|------|
| 文件存在 | ✅ | `pomodoro.html` 已写入；脚本校验 doctype |
| 开始/暂停/重置逻辑自洽 | ✅ | VM 提取 `PomodoroCore` 后测 `start`/`pause`/`reset`/`tick` 往返与 no-op |
| 时长配置生效 | ✅ | `clampMinutes`：1/60 边界通过，0/61/非数拒绝；`reset(m)` → `m*60` 秒 |
| 到时状态可见 | ✅（逻辑层） | 源码含「时间到」文案；`finished` 标志与 `remaining===0` 同步；**DOM 渲染 UNVERIFIED** |
| 无外链 | ✅ | 正则扫 CDN/http src/href/@import，无命中；仅本地内联资源 |
| response 有证据或 UNVERIFIED | ✅ | 本文件 + `verify-core.js` 逐条 PASS |

### 需求点

1. **倒计时 25:00 → 0，开始/暂停/重置**
   - `reset(25)` → `remaining=1500`，`formatTime(1500)==="25:00"`
   - 连续 `tick` 至 0：第 60 次 tick（1 分钟场景）后 `remaining=0, finished=true, running=false`
   - 暂停保留 `remaining`；恢复继续递减；结束后再 tick 为 no-op
   - 结束后 `reset` 恢复满时长

2. **结束时状态文案「时间到」+ 可选 beep**
   - 源码字符串 `时间到` 存在；UI 分支：`finished` → 「时间到」
   - beep：Web Audio API 双音（880→660Hz），**浏览器内是否出声依赖用户手势与自动播放策略 → UNVERIFIED**；文案不依赖音频

3. **可配置时长 1–60 正整数**
   - `clampMinutes` 对 `0`/`61`/`"abc"`/`NaN` 返回 `null`（拒绝）
   - `25.9` floor 为 `25`；边界 `1`、`60` 通过
   - UI：`input[type=number] min=1 max=60 step=1` +「应用」按钮；非法值走 `setCustomValidity` + `reportValidity`

4. **无 CDN/框架；逻辑可被 Node 或源码审查核对**
   - 单文件、无外部 script/link/font
   - 纯函数模块 `PomodoroCore` 挂到 `globalThis`，`verify-core.js` 用 `vm` 从 HTML 文本提取并执行

---

## 浏览器交互：UNVERIFIED / 用户自验步骤

本环境未打开真实浏览器点击 UI，以下 **UNVERIFIED**，请本地自验：

### 自验步骤

1. 用浏览器直接打开 `pomodoro.html`（双击或拖入窗口即可，无需服务器）。
2. **默认态**：显示 `25:00`，状态「就绪」；「暂停」应禁用。
3. **开始**：点「开始」→ 数字每秒减 1，状态「专注中…」，「开始」禁用、「暂停」可用。
4. **暂停**：点「暂停」→ 冻结当前时间，状态「已暂停」；再点「开始」应从该秒继续。
5. **重置**：点「重置」→ 回到当前配置的满时长，状态「就绪」。
6. **时长配置**：
   - 将「时长」改为 `1`，点「应用」→ 显示 `01:00`。
   - 输入 `0` 或 `61` 或清空后「应用」→ 浏览器应报 validity 错误，计时不变。
7. **到时**：设为 `1` 分钟并开始，等到 `00:00` → 状态变为 **「时间到」**，显示可能变色（warn）。是否听到 beep 取决于是否已在本页点击过（激活 AudioContext）及系统音量；**听不到 beep 不算逻辑失败**。
8. **无外链**（可选）：DevTools Network 面板刷新，除文档本身不应有第三方请求。

### 预期按钮禁用矩阵

| 状态 | 开始 | 暂停 | 重置 |
|------|------|------|------|
| 就绪 / 已暂停 | 可用 | 禁用 | 可用 |
| 运行中 | 禁用 | 可用 | 可用 |
| 时间到 | 禁用 | 禁用 | 可用 |

---

## 实现摘要

- 状态机：`{ remaining, running, finished }`，全部变更走 `PomodoroCore`，UI 只负责 `setInterval(1000)` + `render`。
- 倒计时用「每秒 tick 减 1」而非 deadline 差值，便于 Node 确定性核对；长时间后台节流时浏览器可能漂移（与同类 setTimeout 方案相同），本任务为 lite 范围未做 deadline 校正。
- 无 localStorage、无多番茄会话、无标签页标题提醒——按「极简」刻意省略。

## 残留风险

- 真实浏览器点击与音频播放 **UNVERIFIED**（见上）。
- 后台标签页 `setInterval` 节流可能导致计时变慢（浏览器通用行为）。
