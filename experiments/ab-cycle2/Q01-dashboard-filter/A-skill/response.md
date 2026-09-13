# Q01 · A 臂 · response.md（由 lead 在限流后据磁盘证据补写；**2026-09-13 勘误 V-02**）

> 说明：A 臂执行者在 429 限流中断前已产出 `app.html` 与**完整的验证证据链**，仅未及写本 response.md。
> 本文件由 lead 依据磁盘产物补写。~~未留正式 `response.md` 与验证脚本~~
> **09-13 勘误（V-02）**：A 臂在 `evidence\` 子目录留有 29 文件的完整验证链（14:06-14:27 落盘，
> 早于 09-12 判分时刻 15:28），09-12 补写时漏盘该子目录导致本文件初版多处失实，现逐条勘误。
> 交付物由 A 臂产出。

## 磁盘清单（09-13 递归盘点修正）
- `app.html`（24,615 字节，单文件内联 CSS/JS，零外部依赖）
- `evidence\`（29 文件，A 臂原生验证链）：
  - `independent-recompute.mjs` + `expected.json` + `recompute.log`（独立复算，14:06）
  - `browser-check.mjs` + `browser-check.json`（38 项）+ `browser-check.log` + `shots\` 8 场景截图（14:23-24）
  - `mutation-test.mjs` + `mutation-test.json` + `mutation-test.log` + `_mutant.html`（变异测试输入）+ `shots-mutant\` 8 张（14:26-27）
  - `static-check.mjs` + `static-check.log`
- `pre-gate.md`（**自发实现前门禁落盘**，14:05，早于 app.html 14:13——~~属内部探索遗留~~ 勘误：这是「无人应答床自发落盘方向」的正面证据，含风险分档/形态选择/保守·大胆方向否决对比/完整计划）
- `load-proof.md`（版本 1.2.0 逐字、硬规则首条逐字）

## 交付物性质（lead 结构性抽检 + 09-13 复算）
- DOCTYPE 1；`<script src>` 0；`http` 字符串仅 `createElementNS('http://www.w3.org/2000/svg', …)`（命名空间，非外链）。
- 满足任务书部件级清单：内嵌数据集、数字卡、地区筛选、柱状图、空态文案、全局兜底均存在。

## 验证（~~未留下~~ 09-13 勘误：验证链完整且可复算）
- **[lead复算 09-13 隔离副本]** `node evidence/browser-check.mjs` → **38/38 全过复现**
  （含 KPI 独立复算对账、筛选联动、轴稳定、空态、非法输入 C4c 全家桶、超长文本、缩放、
  正控红检 C5-detector-red——证明检查器非空转、断网重载 C7-offline）。
- 变异测试：10 变异体 **6 杀 4 存活**（killRate 0.6），A 臂原生如实记录存活项与 M9 锚点未命中
  （`evidence/mutation-test.json`）。
- ~~本项由 lead 抽检替代~~ 勘误：以上均为 A 臂原生证据 + lead 实跑复算。

## 诚实/可追溯
- A 臂执行者无不实声称（其未及写 response；磁盘证据全部真实）。
- 本文件初版（09-12）关于「缺失可复算凭据」的表述**错误**，系 lead 漏盘 evidence/ 所致（V-02，
  见 `_judge/violations.md`）。
- 可追溯维度记 1：原生过程记录（log/json/截图）完整，但结论性 response 系 lead 补写（W2）。

## 不确定项（如实标注）
- 变异测试 4 个存活变异体（M4/M7/M9/M10）未修复复验——A 臂原生如实记录，如实转记。
- 未做真人视觉走查。
- ~~`pre-gate.md`/`_mutant.html` 为中途探索残留，建议清理~~ 勘误：两者分别是自发门禁落盘证据与
  变异测试输入，**属验证链组成部分，不得清理**。
