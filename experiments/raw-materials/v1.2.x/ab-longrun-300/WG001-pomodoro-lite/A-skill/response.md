# response · WG001-pomodoro-lite · A-skill

## 交付

| 文件 | 说明 |
|------|------|
| `pomodoro.html` | 单文件番茄钟（无 CDN / 无框架） |
| `response.md` | 本文件 |
| `verify-logic.js` | 从 HTML 抽取纯逻辑并跑断言的 Node 核对脚本（辅助证据） |

风险分档：**轻通道**（指令已指定产物类型=单文件 HTML、位置=A-skill、形态=task.md 五条功能；影响面小、可逆、无外部副作用）。形态：单 Agent 主干。

---

## 验收清单对照

| 项 | 状态 | 证据 |
|----|------|------|
| 文件存在 | **已核对** | `pomodoro.html` 已写入本目录 |
| 开始/暂停/重置逻辑自洽 | **已核对（逻辑层）** | Node 状态机断言 26/26 PASS，见下 |
| 时长配置生效 | **已核对（逻辑层）** | `clampMinutes` + `setMinutes` 边界用例 PASS |
| 到时状态可见 | **部分已核对** | 源码含 `text = "时间到"`；浏览器呈现 **UNVERIFIED** |
| 无外链 | **已核对** | 无 `<script src>` / `<link>` / `<img>` / `<iframe>`；无 `http(s)://` 资源属性 |
| response 有证据或 UNVERIFIED | **已核对** | 本文件 |

---

## 已核对项（Node / 源码）

复现命令：

```text
node <实验根目录>\ab-longrun-300\WG001-pomodoro-lite\A-skill\verify-logic.js
```

实际输出摘要：

```text
RESULT pass=26 fail=0
```

覆盖点：

1. **格式化**：`1500 → 25:00`，`0 → 00:00`，`65 → 01:05`
2. **时长校验**：1 / 25 / 60 合法；0 / 61 / 1.5 / `"abc"` 拒绝
3. **初始态**：25 分钟 → `remaining=1500`，`phase=ready`
4. **开始**：`ready → running`；结束后再 start 为 no-op
5. **暂停**：`running → paused`，剩余秒数冻结；paused/ready 下 tick 为 no-op
6. **重置**：跑掉 10 秒后 reset → `remaining=120`，`phase=ready`
7. **到时**：1 分钟完整 60 tick → `remaining=0`，`phase=finished`，`running=false`
8. **改时长**：运行中 `setMinutes(10)` → `remaining=600`，回到 ready；非法值抛 `RangeError`
9. **通知**：`onChange` 在 start + tick 时触发
10. **无外链 / 无 CDN 加载标签**
11. **源码含「时间到」文案**（finished 分支）

### 实现要点（便于审查）

- 纯逻辑 `Pomodoro`（`createTimer` / `formatClock` / `clampMinutes`）与 DOM 绑定分离；`typeof document === "undefined"` 时 bootstrap 直接 return，故可在 Node 中抽取执行。
- 状态机：`ready → running → paused → running → finished`；`reset` 回到 `ready`。
- 范围：正整数 1–60；默认 25。
- 到时：状态文案「时间到」+ Web Audio 880Hz 短 beep（约 0.45s）。beep 在「开始」点击时预热 `AudioContext`；若浏览器自动播放策略或静音环境导致无声，**不影响**「时间到」文案可见。

---

## UNVERIFIED（无 GUI，未做浏览器实操）

本环境未打开真实浏览器，以下 **全部标 UNVERIFIED**：

- [ ] 页面视觉布局 / 响应式
- [ ] 点击「开始」后每秒倒计时递减
- [ ] 「暂停」按钮 enable/disable 与剩余时间冻结
- [ ] 「重置」恢复配置时长并回到「就绪」
- [ ] 「应用」后显示新时长（如 1 → `01:00`）
- [ ] 非法输入（0 / 61 / 小数）显示错误文案且不改计时
- [ ] 倒计时至 `00:00` 时状态变为「时间到」（绿色）
- [ ] beep 是否实际发声（依赖声卡与自动播放策略）
- [ ] Enter 键在时长输入框触发「应用」

### 用户自验步骤

1. 用浏览器打开 `pomodoro.html`（双击或拖入窗口）。
2. 确认初始显示 `25:00`，状态「就绪」；「暂停」为禁用。
3. 点「开始」→ 约 1–2 秒后显示 `24:5x`，状态「进行中」；「开始」禁用、「暂停」可用。
4. 点「暂停」→ 时间冻结，状态「已暂停」；再点「开始」继续。
5. 点「重置」→ 回到 `25:00` / 「就绪」。
6. 时长输入 `1` → 点「应用」→ 显示 `01:00`。
7. 输入 `0` 或 `61` → 「应用」→ 出现红色错误提示，计时不变。
8. 再「应用」为 `1`，开始并等待约 60 秒 → `00:00`，状态「时间到」；若未静音应有一声短 beep。
9. DevTools → Network：确认无第三方域请求。
10. （可选）DevTools → Console 无报错。

---

## 未做 / 边界说明

- 未接入系统通知、标题栏闪烁、番茄统计、长短休息等——超出 task.md 范围。
- `setInterval(1000)` 存在浏览器节流下的轻微漂移；对 1–60 分钟量级可接受，未做 deadline 对齐。
- Node 核对覆盖状态机与校验，**不能**替代浏览器交互验收。
