# response.md · WG002-pomodoro-lite

## 交付物

| 文件 | 说明 |
|------|------|
| `pomodoro.html` | 单文件极简番茄钟（HTML+CSS+JS，无外链） |
| `response.md` | 本报告 |
| `verify-extract.mjs` | 主证据：从 HTML 抽出真实源码 + DOM stub + 可控时钟，执行状态机 |
| `verify-logic.mjs` | 辅助：静态外链扫描 + 边界契约（与主脚本独立交叉） |

## 需求对照

| # | 需求 | 状态 | 证据 |
|---|------|------|------|
| 1 | 倒计时 25:00 → 0，开始/暂停/重置 | **已核对** | `verify-extract.mjs`：初始 25:00；开始→进行中/暂停钮；暂停→已暂停/开始钮且 remaining 保留；重置→25:00/就绪 |
| 2 | 结束状态「时间到」+ 可选 beep | **逻辑已核对** | 可控时钟推进 61s 后真实进入 `finish()`：文案「时间到」、`done` class、显示 `00:00`、ticker 清空；beep 为 Web Audio，Node stub 未提供 AudioContext（静默路径）；**真实发声 UNVERIFIED** |
| 3 | 可配置时长 1–60 正整数 | **已核对** | 改为 1 → `01:00`；改为 7 → `07:00`；输入 0 被拒绝/钳制；`clampMinutes` 对 0/61/2.5/NaN 返回 null |
| 4 | 无 CDN/框架；逻辑可被 Node 核对 | **已满足** | `verify-logic.mjs` 扫描 0 处 `http(s)`；两份 Node 脚本均 exit 0 |
| 5 | 本 response | 交付 | — |

## 已核对项（Node，可复现）

主命令（判别力强：跑的是 shipped 源码，不是平行重写）：

```text
node verify-extract.mjs
```

结果：`pass=39 fail=0`（exit 0）

覆盖面摘要：

- 导出与常量：`PomodoroLogic.clampMinutes` / `formatClock` / DEFAULT 25 / MIN 1 / MAX 60
- 时长钳制：1/25/60 通过；0/61/2.5/NaN 拒绝
- 时钟格式：00:00 / 00:01 / 25:00 / 59:59 / 小数上取整 / 负数钳 0
- DOM 状态机（真实 event handler）：就绪 → 开始 → 暂停 → 重置
- 配置生效：1 分钟、7 分钟；非法 0 被拒
- **到时路径**：开始后把 mock 墙钟推进 61s，触发 interval → `finish()` → 「时间到」+ `00:00` + 按钮复位 + ticker 清除；结束后再开始会满时长重启

辅命令：

```text
node verify-logic.mjs
```

结果：`pass=27 fail=0`（静态外链/结构扫描 + 同契约边界）

## 浏览器交互 · UNVERIFIED

本环境无 GUI/截图闭环，下列项 **未亲手在浏览器操作**：

- 真实点击手感、布局/配色在各视口的呈现
- 真实墙钟走秒与标签页节流表现（逻辑用绝对 `endAt`，Node 已验，浏览器未实测）
- beep 是否在用户手势后发声（autoplay 策略）
- 多浏览器（Chrome/Firefox/Safari）与移动端触控

### 用户自验步骤

1. 浏览器打开 `pomodoro.html`（双击 file:// 即可）。
2. 确认初始 `25:00`，状态「就绪」，主按钮「开始」。
3. 开始 → 「进行中」且数字递减；再点 → 「暂停」数字停住；再点 → 从剩余时间继续。
4. 重置 → 回到配置时长，状态「就绪」。
5. 时长改为 `1`，重置 → `01:00`；开始约 60s → `00:00`、红色「时间到」、短 beep。
6. 试 `0` / `61` / `1.5` / 空，确认不会出现非法倒计时。
7. 刷新页面：状态回到就绪（有意无持久化）。

## 设计说明

- 绝对时间戳倒计时（`endAt = Date.now() + remainingMs`）：interval 抖动/后台节流不累计漂移。
- beep 用 Web Audio 振荡器，无音频文件/CDN；失败只丢提示音，「时间到」文案不受影响。
- 单文件内联，无构建步骤。

## 风险与边界

- 视觉/真机交互全部 UNVERIFIED（见上）。
- 页面刷新丢失运行状态（极简有意设计）。
- 未做跨浏览器矩阵。
