# Q02 · A 臂 · response.md（由 lead 在限流后据磁盘证据补写；**2026-09-13 勘误 V-02**）

> 说明：A 臂执行者在 429 限流中断前已产出 `app.html` 与**完整的验证证据树**，仅未及写本 response.md。
> ~~未留正式 `response.md` 与验证脚本~~ **09-13 勘误（V-02）**：A 臂在 `evidence\` 子目录留有
> 105 文件的完整验证树（14:13-14:28 落盘，mutation-summary.json=14:28:49，早于 09-12 判分时刻
> 15:28），09-12 补写时漏盘导致本文件初版失实，现勘误。交付物由 A 臂产出。

## 磁盘清单（09-13 递归盘点修正）
- `app.html`（29,775 字节，单文件内联，零外部依赖，含 3 组 `@keyframes` 与游戏主循环）
- `evidence\`（105 文件，A 臂原生验证树）：
  - `README.md`（3.6KB，验证方法学说明）、`run-all.log`（6.5KB 全量运行日志）
  - `results-app.json`（15KB，冻结产物全量验证结果）
  - `mutants.mjs`（变异杀伤实验脚本，含事前预测）+ `mutants\m01-m10.html`（10 个变异体副本）
  - `mutant-results\m01-m10.json`（逐变异体结果）+ `mutation-summary.json`（10/10 KILLED）
  - `shots\` + `mutant-results\shots\`（截图 80+ 张）

## 交付物性质（lead 结构性抽检 + 09-13 复算）
- DOCTYPE 1；`<script src>` 0；`http(s)://` 0（无任何外部引用）。
- 含 初始/发球/挡板移动/碰撞/计分/生命/重开 等 breakout 核心要素。

## 验证（~~未留下正式验证脚本/报告~~ 09-13 勘误：验证树完整且经 lead 全量复算）
- **[lead复算 09-13 隔离副本]** `node evidence/mutants.mjs` → **杀伤率 10/10 全量复现**
  （2m37s；基线先全绿、10 个单点变异体全部被 ≥1 项检查杀死 exit 1；m04/m05 预测偏严细节亦复现）。
- 基线验证（`run-all.log`）：静态 S1/S1b/S2 + 交互 C1-C23+（含球/砖/挡板/墙碰撞、计分 DOM 一致性、
  运行时网络零外联、无未捕获异常）。
- 变异判据（A 臂原生定义）：「被杀死 = 该变异体运行 exit 1 且至少 1 项检查转红；predictedKill
  仅作事前预测对照，不参与判定」——m04/m05 预测偏严如实记录。

## 诚实/可追溯
- A 臂执行者无不实声称（其未及写 response；磁盘证据全部真实）。
- 本文件初版（09-12）「未留正式验证脚本/报告」「本臂缺失 lead 可复算的验证凭据」的表述**错误**，
  系 lead 漏盘 evidence/ 所致（V-02，见 `_judge/violations.md`）。
- 可追溯维度记 1：原生过程记录（README/run-all.log/json）完整，但结论性 response 系 lead 补写（W2）。

## 不确定项（如实标注）
- 发球/挡板键盘鼠标控制、砖块碰撞、生命耗尽重开的**真人视觉/手感**走查未做（无头浏览器断言为主）。
- `results-app.json` 的交互项明细 lead 未逐项重跑（已由 mutants.mjs 的基线先行全绿覆盖其主干）。
