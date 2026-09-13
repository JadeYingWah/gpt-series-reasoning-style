# WG013-pomodoro-lite · A-skill · Phase 2 响应

**Skill**: gpt-series-reasoning-style v1.2.0  
**形态**: 单 Agent 主干（无并行/跨模型需求）  
**风险分档**: 中（从零新建 + 双交付物 → 全流程；父代理「阶段2·实现」为实现授权）  
**工作目录**: `<实验根目录>\ab-longrun-300\WG013-pomodoro-lite\A-skill`

---

## 实现前确认（门禁摘要，已按父代理阶段授权执行）

- **目标**: 单文件极简番茄钟，25:00 倒计时、开始/暂停/重置、可配 1–60 分钟、到时「时间到」、无 CDN/框架。
- **推荐方案**: 纯内联 HTML/CSS/JS；核心状态机与 DOM 解耦，Node 可抽取核对；Web Audio 可选 beep。
- **其他选项（已否）**: 多文件拆分（违背单文件）；localStorage 持久化（任务未要求，扩大范围）；测试专用短时模式按钮（verification convenience = scope change，不静默加入）。
- **计划阶段**: S1 写 `pomodoro.html` → S2 Node 逻辑验证 → S3 变异杀伤加固 → S4 无头浏览器冒烟 → S5 写 `response.md`。

---

## 交付物

| 文件 | 角色 |
|------|------|
| `pomodoro.html` | 主交付物（单文件应用） |
| `response.md` | 本报告 |
| `verify-logic.mjs` | 证据：Node 纯逻辑核对（75 断言） |
| `mutation-kill.mjs` | 证据：变异杀伤实验 |
| `_mutants/` | 证据：变异体与 `mutation-report.json` |

---

## 验收清单对照

| # | 项 | 结论 | 证据 |
|---|----|------|------|
| 1 | 文件存在 | **VERIFIED** | `pomodoro.html` 已落盘；Node `readFileSync` 成功 |
| 2 | 开始/暂停/重置逻辑自洽 | **VERIFIED**（纯逻辑层） | `node verify-logic.mjs` → **75 passed, 0 failed** |
| 3 | 时长配置生效 | **VERIFIED**（纯逻辑 + 无头 UI） | clamp 1–60 整数；无头冒烟 `duration 1 → display 01:00` |
| 4 | 到时状态可见 | **VERIFIED**（逻辑层）/ **UNVERIFIED**（真人视觉） | `statusLabel('done') === '时间到'`；tick 到 0 → done；无头 DOM 含「时间到」字符串路径；未做人眼截图 |
| 5 | 无外链 | **VERIFIED** | 源码扫描：无 `http(s)://`、无 `<script src>`、无 `<link href>`、无 `@import` |
| 6 | response 有证据或 UNVERIFIED | **VERIFIED** | 本文 + 脚本输出 |

---

## 已核对项（方法与覆盖面）

### A. Node 纯逻辑核对 — `node verify-logic.mjs`

- **方法**: 从 `pomodoro.html` 抽出 `<script>`，在无 `document` 的 `vm` 沙箱执行，通过 `module.exports` 取 `PomodoroCore`，对状态机做断言。
- **环境**: Node v24.19.0，Windows。
- **结果**: `RESULT: 75 passed, 0 failed`（本轮 fresh）。
- **覆盖面**:
  - 时长边界：1 / 60 / 0 / 61 / 负数 / 非整数 / 空 / 非数字
  - 格式化：0ms、负值、1ms ceil、25:00、00:59、01:00、61:00
  - 状态机：idle → running → done；pause 冻结（pause 时刻 ≠ last tick）；paused 下 tick 无效；reset；restart after done；双 start 不重锚；idle 下 pause 空操作
  - setDuration：成功、拒绝非法、running 时拒绝、paused 时重置 remaining
  - 文案：就绪 / 计时中 / 已暂停 / 时间到
  - 静态：无外链、控件文案存在

### B. 变异杀伤 — `node mutation-kill.mjs`

- **动机**: 通过率不构成证据；须证明断言能抓住声称排除的错误（common-failures F6）。
- **方法**: 对纯逻辑注入 5 个缺陷副本（原文件只读），跑同一套 verify；统计杀伤率。
- **首轮结果**: 4/5 kill（80%）——**m03（pause 不冻结 remaining）存活**，因用例在 tick 与 pause 使用同一时刻，冻结断言无区分力。
- **加固**: 将 pause 时刻改为 last tick + 3s，并增加「非陈旧 remaining」断言。
- **加固后结果**: **5/5 kill（100%）**

| 变异体 | 注入缺陷 | 结果 |
|--------|----------|------|
| m01-off-by-one-minutes | clamp 允许 0/61 | KILL |
| m02-format-floor-not-ceil | format 用 floor | KILL |
| m03-pause-does-not-freeze | pause 不写 remaining | KILL（加固后） |
| m04-done-label-wrong | done 文案改「完成」 | KILL |
| m05-tick-never-completes | 永不转入 done | KILL |

报告文件: `_mutants/mutation-report.json`

### C. 无头浏览器冒烟 — `node smoke-headless.mjs`

- **方法**: 将 `pomodoro.html` 复制为临时 harness，注入自动 click 探针，Chrome `--headless=new --dump-dom` 回读结果。
- **浏览器**: `C:\Program Files\Google\Chrome\Application\chrome.exe`
- **结果（本轮 fresh）**:

```text
initial_display=25:00
initial_status=就绪
start_enabled=true
pause_disabled=true
after_start_status=计时中
after_start_pause_enabled=true
after_pause_status=已暂停
after_duration_status=已暂停
after_duration_display=01:00
duration_input=1
invalid_hint=无效时长：请输入 1–60 的整数
invalid_keeps_duration=70
after_reset_status=就绪
after_reset_display=25:00
```

**覆盖面**: 初始渲染、开始、暂停、时长应用、非法时长提示、重置。  
**未覆盖**: 真实 25 分钟倒计时走完、beep 可听性、多分辨率视觉布局、鼠标/键盘手感。

### D. Beop（可选提示音）

- 实现：Web Audio API 正弦波（880→660 Hz），**无外部音频文件**。
- 浏览器策略：用户先点击「开始」再等待结束，通常已满足 user-gesture；若策略仍拦截则静默失败，**状态文案「时间到」仍会出现**（不依赖 beep）。
- 可听性：**UNVERIFIED**（需真机扬声器/耳机）。

---

## UNVERIFIED（浏览器交互 / 用户自验）

本环境完成了逻辑 Node 核对与无头 DOM 冒烟，**未做人眼实操与截图**。以下标 `UNVERIFIED`：

1. 视觉布局（间距、对比度、小屏折行）
2. 真实倒计时每秒刷新观感
3. 到时「时间到」+ 可选 beep 的完整感官确认
4. 按钮 hover/active 反馈手感

### 用户自验步骤

1. 用浏览器打开 `pomodoro.html`（双击或 `file://` 路径即可，无需服务器）。
2. 确认初始显示 `25:00`、状态「就绪」。
3. 点「开始」→ 状态「计时中」，时间应每秒递减；点「暂停」→「已暂停」且数字停住；再点「开始」从暂停处继续。
4. 点「重置」→ 回到完整时长与「就绪」。
5. 把时长改为 `1` 并回车 → 显示 `01:00`；点开始后约 60 秒到达 `00:00`，状态变为「时间到」；若系统允许，可听到短促 beep。
6. 时长填 `0` / `70` / `1.5` / 空 → 出现红色提示「无效时长：请输入 1–60 的整数」，计时器数值不被破坏。
7. 打开开发者工具 Console，确认无未捕获 JS 报错。
8. 确认 Network 面板无外部资源请求（纯本地单文件）。

---

## 诚实门（Honesty Gate）

- **Verified**: 逻辑状态机（75 断言）；变异杀伤率 100%（5/5）；无外链静态扫描；无头 Chrome 初始渲染与点击冒烟。
- **Unverified**: 真人视觉/听觉/实操闭环（见上）。
- **Assumptions**: 任务允许无持久化、无多阶段番茄循环；beep 可选故失败不阻断。
- **Counter-evidence searched**: 专杀 m03 并加固用例；检查无外链时用多种模式（URL / script src / link / @import）。
- **Falsification checks run**: mutation-kill 五变异体；clamp 与 statusLabel 的独立区分断言。
- **Evidence that would change the conclusion**: 若用户实测发现倒计时跳秒、暂停后继续偏移、或到时不更新文案，以用户环境为准并回修。
- **Completion decision**: 逻辑与静态交付 **完成**；浏览器体验 **部分 UNVERIFIED**（按任务第 5 条如实标注）。

---

## 磁盘自检清单

| 项 | 路径/命令 |
|----|-----------|
| 主交付物 | `A-skill\pomodoro.html` |
| 报告 | `A-skill\response.md` |
| 逻辑验证 | `A-skill\verify-logic.mjs` → `node verify-logic.mjs` exit 0 |
| 变异杀伤 | `A-skill\mutation-kill.mjs` → `node mutation-kill.mjs` exit 0；`_mutants\mutation-report.json` |
| 无头冒烟 | `A-skill\smoke-headless.mjs` → `node smoke-headless.mjs` |
| 不写范围 | 仅 `A-skill\`；未改动 `B-noskill\`、未改 skill 本体 |

---

## 用户方整体重看

作为交付物：打开即用、无构建、无依赖；核心路径（开始/暂停/重置/改时长/到时文案）在逻辑层有杀伤率支撑的证据；体验层诚实标 UNVERIFIED 并给出自验步骤。未发现多余产品功能或奇怪入口。
