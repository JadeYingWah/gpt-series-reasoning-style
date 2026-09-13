# Load Proof — gpt-series-reasoning-style

## Version

**1.2.0**

## Mandatory Pre-Implementation Gate — hard rule #1 (verbatim)

> 宣布阶段序列不是确认。

## Collaboration architecture (brief)

- **主干（默认）· 单 Agent**：同一模型内部切换规划面 / 执行面 / 审查面；绝大多数任务由此完成。
- **扩展A · 子 Agent 增强**：任务适合并行或隔离且宿主支持子 Agent 时启用；启用前须先确认子 Agent 能力，未证实则退回主干并标 `UNVERIFIED`。
- **扩展B · 指挥官多 Agent**：需协调独立大模型 / Agent 时启用模式三协议；只影响启用的任务，不改变主干地位。
- 形态由 AI 按任务自选，并在门禁中声明一行理由；用户指名优先、可随时切换。
- 可混合：同一任务的不同阶段可用不同形态。

## Files actually read

| Path | Role |
|------|------|
| `<skill安装目录> | skill body / rules |
| `<skill安装目录> | version pin (1.2.0) |

References were **not** read (not required for load proof; on-demand only).

## Scope of this phase

- 阶段1 = 加载证明 only.
- No pre-implementation gate, no resource survey, no implementation, no files created outside this `load-proof.md`.
- Stop here as instructed.
