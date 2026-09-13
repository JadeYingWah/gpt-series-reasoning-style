# DIR01 · A 臂 · response.md（由 lead 在限流后据磁盘证据补写）

> 说明：本文件由 lead 在 429 限流导致执行者子智能体收尾中断后，依据磁盘上 A 臂自有产物
> （`art.html` / `evidence/` / `gate.md` / `load-proof.md`）及 lead 独立复算补写，非原执行者所写。
> 交付物本身由原 A 臂产出，变量控制未受影响。

## 磁盘清单
- `art.html`（约 17.3 KB，SVG/CSS/JS 内联，含 `xmlns` 命名空间，无外部依赖）
- `gate.md`（门禁应答轮产物，含 ≥3 个命名方向 + 监督者应答原文）
- `load-proof.md`（版本 1.2.0 逐字、硬规则首条逐字）
- `evidence/`（验证证据树：verify.mjs、逐帧 transform 快照、PNG 定帧、CDP 日志）

## 方向选择（门禁轮后）
- 推荐并接受方向 **C（大胆·可验算的滑翔动力学）**：在分层美术之上把「山羊摆腿→翼面俯仰→伪升力→滑翔机高度」做成闭合因果链，视差层速度反向绑定飞行高度，使任意帧高度/俯仰/摆腿相位可反算、可被逐帧证伪。
- `gate.md` 中已并列 A 保守 / B 均衡 / C 大胆 三方向及各自取舍，并按监督者应答要求补 2 个真实不同方向。

## 验证（lead 独立复算）
- 运行 `evidence/verify.mjs`：`reproducible = true`、`frame_differs = true`、控制台异常 **0**；
  即任意帧的 transform 可由参数确定重放，且不同帧差异可机械核对 → **确定性帧可复现，鉴别力成立**。
- `art.html` 结构性抽检：DOCTYPE 1、`http` 仅 `xmlns` 命名空间、无 `<script src>`。

## 不确定项（如实标注）
- 视觉观感（动画流畅度、配色辨识度）仅以无头 Chrome 截帧核验，未做人眼走查。
- 方向 B/A 仅作对照陈述，未实现，故其实际可交付性未经验证。
- 验证依赖 Chrome/CDP 实跑，跨臂并发时存在端口/Profile 占用风险（见 OB-02）。
