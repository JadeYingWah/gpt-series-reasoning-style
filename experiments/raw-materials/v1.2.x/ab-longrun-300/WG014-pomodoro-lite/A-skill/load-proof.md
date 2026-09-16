# Load Proof — gpt-series-reasoning-style

## Version

1.2.0

## Hard Rule (verbatim)

> 宣布阶段序列不是确认。

## Collaboration Architecture (brief)

- **单 Agent 主干（默认）**：同一模型内部切换规划面 / 执行面 / 审查面；绝大多数任务由此完成。
- **扩展A · 子 Agent 增强**：任务适合并行或隔离且宿主支持子 Agent 时启用；启用前须先确认子 Agent 能力，能力未证实退回主干并标记 `UNVERIFIED`。
- **扩展B · 指挥官多 Agent**：需要协调独立大模型 / Agent 或经用户转交时对该任务启用模式三协议；只影响启用的任务，不改变主干地位。

形态由 AI 按任务自选并在门禁声明一行理由；用户指名优先，可随时切换。可混合搭配：同一任务的不同阶段可用不同形态。

## Files Actually Read

- `<skill安装目录>
- `<skill安装目录>

（references 未读——按需读取；本阶段仅需 SKILL.md + VERSION。）
