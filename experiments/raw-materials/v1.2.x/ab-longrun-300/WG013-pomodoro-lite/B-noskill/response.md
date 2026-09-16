# response · WG013-pomodoro-lite · B-noskill

交付：`pomodoro.html`（单文件，无构建）+ 本文件 + 辅助核对脚本 `verify-logic.mjs`。

## 交付物

| 文件 | 说明 |
|------|------|
| `pomodoro.html` | 极简番茄钟 UI + 逻辑，纯原生 HTML/CSS/JS |
| `verify-logic.mjs` | 将核心纯函数抽出，用 Node 断言核对 |
| `response.md` | 本文件 |

## 已核对项（可复现证据）

### 1. 文件存在

- `pomodoro.html`、`response.md`、`verify-logic.mjs` 均在本目录。

### 2. 无 CDN / 无框架（源码审查）

对 `pomodoro.html` 检索外链关键词（`http`/`https`/`cdn.`/`unpkg`/`jsdelivr`/`jquery`/`react`/`vue`/`angular`/`bootstrap`）：

```
No files found
```

- `<head>` 仅有内联 `<style>`；脚本为页内 `<script>`。
- 无 `link`/`script src`，无 import map，无网络请求 API（除 `AudioContext` 本地振荡器）。

### 3. 开始 / 暂停 / 重置逻辑自洽（Node 可跑）

```bash
cd "<实验根目录>\ab-longrun-300\WG013-pomodoro-lite\B-noskill"
node verify-logic.mjs
```

输出（节选）：

```
OK   idle can start => true
OK   running cannot start again => false
OK   cannot apply while running => false
OK   cannot apply while paused => false
OK   apply 10 while idle => true
OK   apply 0 rejected => false
OK   apply 61 rejected => false
OK   mode -> done when remaining<=0 => done
OK   remaining zero => 0

All assertions passed.
```

状态机在 HTML 中实现为：

- `idle` → 点「开始」→ `running`（`setInterval` 200ms + `Date.now` 目标时刻，抗节流漂移）
- `running` → 点「暂停」→ `paused`（用 `endAt - now` 固化剩余）
- `paused` → 点「继续」→ `running`（以当前剩余重算 `endAt`）
- 任意非 `idle` → 点「重置」→ `idle`（剩余 = 时长）
- 剩余 ≤ 0 → `done`：显示 `00:00`，状态文案「时间到」，尝试 beep
- `done` 时「开始」禁用；需「重置」或「应用」新时长后再开

### 4. 时长配置生效（1–60 正整数）

- 输入框 `type="number" min=1 max=60 step=1`，另在 JS 再校验。
- `parseMinutes` 只接受整数；拒绝 `0` / `61` / `-5` / `25.5` / 非数字 / 空。
- 运行或暂停中「应用」被拒绝，并提示先重置。
- 应用成功后：`durationMs = remainingMs = minutes * 60 * 1000`，回 `idle`。

Node 断言覆盖边界：`1`、`25`、`60` 通过；`0`、`61`、`25.5`、空、`abc` 拒绝。

### 5. 到时状态可见

- 到时强制 `display` 为 `00:00`，`#status` 文本为「时间到」并加 `done` 样式（成功色）。
- `aria-live="polite"` 在状态文案上，便于读屏。
- 提示音：使用 Web Audio `OscillatorNode`（880Hz，~0.35s）本地合成，**无音频资源文件**。浏览器若无 `AudioContext` 或因自动播放策略拒绝，则 **catch 后静默**，视觉文案「时间到」不受影响。

### 6. 逻辑可被 Node 或源码审查核对

- 核心纯函数：`parseMinutes` / `clampMinutes` / `formatClock`，无 DOM 依赖，已镜像进 `verify-logic.mjs` 并跑通。
- 状态迁移约束与按钮禁用规则在 `render()` 中集中映射，便于源码对照。

## UNVERIFIED（浏览器交互，需用户自验）

本环境未启动真实浏览器点击/计时，以下为 **UNVERIFIED**：

| 项 | 自验步骤 |
|----|----------|
| 点击「开始」倒计时走动 | 打开 `pomodoro.html`，确认 `25:00` 开始秒级递减，按钮变「暂停」 |
| 暂停冻结 / 继续接续 | 运行中点「暂停」，数字停住且状态「已暂停」；点「继续」从剩余时间接着走 |
| 重置 | 点「重置」回到初始显示与「就绪」，「开始」可再点 |
| 改时长 | 改为 `1` 后点「应用」，显示变为 `01:00`；再点「开始」验证 1 分钟全流程 |
| 非法时长 | 输入 `0` / `60` 以外或小数后「应用」，应提示「请输入 1–60 的正整数分钟」 |
| 到时文案 | 用 `1` 分钟（或开发者工具把 `durationMs` 临时改小）等待到 0，确认显示 `00:00` 且状态为「时间到」 |
| 提示音 | 到时应有短「叮」；若系统静音/浏览器拦截无声，属预期降级（文案仍可见） |
| 深浅色 | 跟随 `prefers-color-scheme`；可切换系统主题看卡片与配色 |
| 本地打开 | 建议用 `file://` 或任意静态服务直接打开；无需 Node 跑 UI |

### 快速缩短等待的调试技巧（可选）

浏览器控制台将剩余设为 3 秒再开始（文件内变量在 IIFE 外不可见时，可临时改源码里 `DEFAULT_MINUTES` 或 `durationMs` 为更小值后刷新）。源码中 `DEFAULT_MINUTES = 25` 在脚本顶部，便于临时改。

## 验收清单自评

| 清单项 | 自评 |
|--------|------|
| 文件存在 | 已满足 |
| 开始/暂停/重置逻辑自洽 | 状态机 + Node 断言通过；**浏览器手感 UNVERIFIED** |
| 时长配置生效 | 边界断言通过；**输入框交互 UNVERIFIED** |
| 到时状态可见 | 源码保证文案/显示；**真实到时视觉 UNVERIFIED** |
| 无外链 | 检索无命中 |
| response 有证据或 UNVERIFIED | 本文件已分列 |
