# BASE03 · A 臂 · response.md（由 lead 在限流后据磁盘证据补写）

> 说明：A 臂执行者在 429 限流中断前已产出全部交付物与 `selftest.js`（72/72 通过），仅差 `response.md` 收尾。
> 本文件由 lead 据 A 臂自有产物（`app.html` + `selftest.js` + `selftest-output.txt` + `_verify/` + 运行日志）补写。

## 磁盘清单
- `app.html`（单文件内联，零外部依赖）
- `selftest.js`、`selftest-output.txt`（自检：通过 72 项 / 失败 0 项）
- `_verify/`（验收脚本集合：`make-compact-probe.js` / `make-harness.js` / `make-previews.js` / `make-probe.js`）
- 运行临时物：`_browsers.txt` / `_env.txt` / `_cp.log` / `_pb.log` / `_uirun.log` 等多份日志

## 验证（lead 复核 A 臂报告）
- `selftest-output.txt`：**72/72 通过**。
  - 金额先规整四舍五入→整数分，人均 floor + 余数分配，保证合计恒等于总额、极差 ≤1 分。
  - **随机 20,000 组守恒测试全过**（校验 sumCents == totalCents）。
  - 边界：1 万亿元/999,999 人 守恒且无 NaN；人数 0/负/超长、金额空/非数字/负/超长等全拒。
- 静态抽检（A 臂）：无 `http(s)://`、无 `<script src>`、无 `fetch`/`XHR`/`import`、含全局兜底与 `try/catch`。

## 诚实/可追溯
- A 臂把随机守恒测试（20,000 组）与边界用例作为「证据」明确列出并给出通过数，可由 lead 复算。

## 不确定项（如实标注）
- 真人有浏览器视觉走查未做（仅 DOM 桩/逻辑复算）。
- 四舍五入 vs 截断、人数 10 万/金额 1 万亿上限为自定阈值，任务书未规定。
