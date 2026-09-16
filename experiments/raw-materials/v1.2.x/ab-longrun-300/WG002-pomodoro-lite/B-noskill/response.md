# response · WG002-pomodoro-lite · B-noskill

交付文件：`pomodoro.html`（单文件，无外链）+ 本 `response.md`。

## 实现摘要

| 需求 | 实现 |
|------|------|
| 倒计时 25:00 → 0 | 默认 `totalSeconds = 25*60`，`display` 以 `mm:ss` 渲染 |
| 开始 / 暂停 / 重置 | 按钮绑定 `start` / `pause` / `reset`；`deadlineTs` 对齐防漂移 |
| 结束状态「时间到」 | `state === 'done'` 时状态文案为「时间到」；并尝试 Web Audio 880Hz beep |
| 时长配置 1–60 正整数 | `normalizeMinutes` 截断并校验；非法值拒绝并显示错误；运行中锁定输入 |
| 无 CDN / 框架 | 纯 HTML + 内联 CSS/JS；逻辑暴露为 `window.Pomodoro` 便于审查 |

状态机：`idle → running ⇄ paused`；任一计时路径 `remainingSeconds <= 0` → `done`；`done` 后再点开始会从当前配置总时长重新计；`reset` 回到 `idle` 与总时长。

## 已核对项（Node 源码抽离断言，全部 PASS）

从 `pomodoro.html` 正则抽取 `Pomodoro` 核心对象后，以 Node 断言（共 29 项）：

- `format`：`0→00:00`、`59→00:59`、`60→01:00`、`1500→25:00`、负值钳制为 `00:00`
- `normalizeMinutes`：接受 1/60；`25.9→25`；拒绝 0、61、非数字、空串
- `setDuration`：30 分钟写入 `totalSeconds=1800` 且 `remaining=1800`；拒绝 0/61；**运行中拒绝修改**
- `start`：`idle/paused` 进入 `running` 并武装定时器；running 中重复 start 为 ok no-op
- `pause`：进入 `paused` 并清理定时器；二次 pause 拒绝
- `reset`：回 `idle` 且 `remaining` 恢复为总时长
- 结束路径：`deadlineTs` 在过去时 `_syncFromDeadline` 得 `remainingSeconds === 0`；`done` 后 `start` 会重载总时长
- 静态源码检查：无 `http(s)://` / `cdn.` / 外部 `<script src>` / `<link href>`；含「时间到」文案；含 `AudioContext` beep 实现

命令（可复现，于 `B-noskill` 目录）：

```text
node -e "…从 html 抽取 Pomodoro 后 assert…"
```

输出末行：`ALL CHECKS PASSED`（29 PASS）。

## 浏览器交互 UNVERIFIED

以下**未**在真实浏览器自动化/截图中核验（本臂未跑 headless 浏览器）：

- 按钮点击、输入框、样式与无障碍 `aria-live` 实际渲染
- Web Audio beep 是否被自动播放策略允许（需用户手势后首次 `AudioContext`；当前 beep 在「时间到」时创建，若此前已有用户点击开始，一般可出声）
- 切后台 / 系统休眠时 `setInterval`+`deadlineTs` 的表现（逻辑上以 deadline 对齐，理论可恢复正确剩余，但未实测）

## 用户自验步骤

1. 用浏览器直接打开 `pomodoro.html`（双击或 `file://`）。
2. 确认初始显示 `25:00`，状态「就绪」。
3. 点「开始」→ 数字每秒递减，状态「计时中」，「开始」禁用、「暂停」可用。
4. 点「暂停」→ 数字停住，状态「已暂停」；再点「开始」继续。
5. 点「重置」→ 回到当前配置的完整时长与「就绪」。
6. 将时长改为 `1` 并回车/失焦 → 显示 `01:00`；改 `0` 或 `61` → 出现错误提示且时长不变；运行中输入框变灰不可改。
7. 设为 1 分钟并开始，等待至 0 → 状态变为「时间到」，尝试一声短 beep（无声则为浏览器策略/不支持，功能仍完整）。
8. DevTools Network：确认无对外 CDN/字体/脚本请求。

## 验收清单对照

- [x] 文件存在（`pomodoro.html`）
- [x] 开始/暂停/重置逻辑自洽（Node 断言）
- [x] 时长配置生效（1–60 校验 + setDuration）
- [x] 到时状态可见（源码含「时间到」+ done 状态机）
- [x] 无外链（源码正则检查）
- [x] response 有证据或 UNVERIFIED（上文）
