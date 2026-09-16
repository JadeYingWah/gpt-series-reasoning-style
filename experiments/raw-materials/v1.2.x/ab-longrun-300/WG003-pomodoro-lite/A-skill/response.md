# response.md · WG003-pomodoro-lite · A-skill

## 交付物

| 文件 | 说明 |
|------|------|
| `pomodoro.html` | 单文件极简番茄钟（HTML+CSS+JS，无外链） |
| `response.md` | 本报告 |
| `verify-extract.mjs` | 主证据：从 HTML 抽出真实源码 + DOM stub + 可控时钟，执行状态机 |
| `verify-static.mjs` | 辅助：静态外链/结构扫描 |

## 流程说明（gpt-series-reasoning-style）

- Skill 加载：阶段1 `load-proof.md` 已记录；本阶段复读 `SKILL.md` + `VERSION`（磁盘版本 **1.1.0**；load-proof 写的 1.2.0 与磁盘不一致，以磁盘为准）。
- 硬性规则第一条（逐字）：宣布阶段序列不是确认。
- 协作架构：单 Agent 主干（本任务为单文件小应用，无并行/多模型需求）。
- 风险分档：中（全新产物）→ 但指令已完整指定产物类型（单文件 HTML 番茄钟）、位置（A-skill/）、形态（`pomodoro.html` + `response.md`）与全部功能/验收条款；父 Agent 以「阶段2·实现」显式授权执行。子 Agent 无法向终端用户二次确认，故按已授权完整规格直接实现，并在本报告中留下可复核证据。
- 实操体验闭环：本环境无 GUI/截图能力 → 浏览器视觉/手势项标 `UNVERIFIED`，并给出用户自验步骤。

## 需求对照

| # | 需求 | 状态 | 证据 |
|---|------|------|------|
| 1 | 倒计时 25:00 → 0，开始/暂停/重置 | **已核对** | `verify-extract.mjs`：初始 `25:00`/就绪；开始→进行中+ticker；暂停→已暂停且 remaining 保留；再开始从剩余继续；重置→`25:00`/就绪 |
| 2 | 结束状态「时间到」+ 可选 beep | **逻辑已核对** | 可控时钟推进至期满后真实进入 `finish()`：文案「时间到」、`done` class、显示 `00:00`、ticker 清空、开始钮禁用；beep 为 Web Audio 振荡器，Node stub 无 AudioContext（静默路径）；**真实发声 UNVERIFIED** |
| 3 | 可配置时长 1–60 正整数 | **已核对** | 应用 `1` → `01:00`；应用 `7` 会重置计时；`0`/`61`/`2.5`/`abc` 被拒并回写上次合法值；`60` → `60:00`；Enter 触发应用 |
| 4 | 无 CDN/框架；逻辑可被 Node 核对 | **已满足** | `verify-static.mjs`：0 处 `http(s)`、0 外链 script/link/img、单内联 script；两份 Node 脚本均 exit 0 |
| 5 | 本 response | 交付 | — |

## 已核对项（Node，可复现）

主命令（跑的是 shipped 源码，不是平行重写）：

```text
cd <实验根目录>\ab-longrun-300\WG003-pomodoro-lite\A-skill
node verify-extract.mjs
```

结果：`pass=56 fail=0`（exit 0）

覆盖面摘要：

- 导出与常量：`window.PomodoroLite` / MIN 1 / MAX 60 / DEFAULT 25
- 时钟格式：`00:00` / `00:01`(ceil) / `25:00` / `09:59` / `59:59` / 负数钳 0
- 时长解析：拒 empty/0/61/2.5/abc；收 1/25/60/带空白
- DOM 状态机（真实 event handler）：就绪 → 开始 → 双击开始 no-op → 推进 10 分钟 → 暂停 → 暂停 no-op → 继续 → 重置
- **到时路径**：墙钟推进超 remaining → `finish()` →「时间到」+ `00:00` + ticker 清除；结束后重置可再启
- 配置：1 分钟到时、7 分钟应用重置、非法输入拒绝且输入框回写

辅命令：

```text
node verify-static.mjs
```

结果：`pass=19 fail=0`（外链/ID/文案/结构扫描）

## 浏览器交互 · UNVERIFIED

本环境无 GUI/截图闭环，下列项 **未亲手在浏览器操作**：

- 真实点击手感、布局/配色/视口呈现
- 真实墙钟走秒与标签页节流（逻辑用绝对 `endAt`，Node 已验，浏览器未实测）
- beep 是否在用户手势后发声（autoplay 策略）
- 多浏览器与移动端触控

### 用户自验步骤

1. 浏览器打开 `pomodoro.html`（双击 file:// 即可，无需服务器）。
2. 确认初始 `25:00`，状态「就绪」，主按钮「开始」。
3. 开始 → 「进行中」且数字递减；再点开始无效（已禁用）；点暂停 → 「已暂停」数字停住；再开始 → 从剩余时间继续。
4. 重置 → 回到配置时长，状态「就绪」。
5. 时长改为 `1`，应用 → `01:00`；开始约 60s → `00:00`、红色「时间到」、短 beep。
6. 试 `0` / `61` / `1.5` / 空，确认提示非法且不出现非法倒计时。
7. 刷新页面：状态回到就绪（有意无持久化）。

## 设计说明

- 绝对时间戳倒计时（`endAt = Date.now() + remainingMs`）：interval 抖动/后台节流不累计漂移。
- beep 用 Web Audio 振荡器，无音频文件/CDN；失败只丢提示音，「时间到」文案不受影响。
- 应用时长会重置到新时长的就绪态（极简语义，避免「改一半」状态）。
- 单文件内联，无构建步骤；`window.PomodoroLite` 导出纯函数与 `getState` 供审查/自动化。

## 验收清单

- [x] 文件存在
- [x] 开始/暂停/重置逻辑自洽（Node 状态机 56 项）
- [x] 时长配置生效（1/7/60 + 非法拒绝）
- [x] 到时状态可见（「时间到」+ 00:00，逻辑已核；视觉 UNVERIFIED）
- [x] 无外链（静态扫描 19 项）
- [x] response 有证据或 UNVERIFIED

## 风险与边界

- 视觉/真机交互/beep 实听全部 UNVERIFIED（见上）。
- 页面刷新丢失运行状态（极简有意设计）。
- 未做跨浏览器矩阵。
