# 加载证明 · gpt-series-reasoning-style

## 版本号

`1.2.0`（来源：`<skill安装目录>

## 硬性规则第一条（逐字引用）

> 宣布阶段序列不是确认。

（出处：SKILL.md → `## Mandatory Pre-Implementation Gate` → 硬性规则第一条）

## 协作架构简介

- 主干（默认）：单 Agent —— 同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。
- 扩展A（按需）：子 Agent 增强 —— 任务适合并行或隔离且宿主支持子 Agent 时启用；启用前须确认子 Agent 能力，能力未证实退回主干并标 `UNVERIFIED`。
- 扩展B（按需）：指挥官多 Agent —— 需协调独立大模型/Agent 或经用户转交时，对该任务启用模式三协议。
- 形态由 AI 按任务自选并在门禁声明一行理由；用户指名优先、可随时切换；启用扩展须先说明理由并各过各的确认门禁。可混合搭配（同一任务不同阶段可用不同形态）。

## 实际读过的文件

| 文件 | 用途 |
|------|------|
| `<skill安装目录> | skill 本体（核心风格、加载证明、门禁、工作流） |
| `<skill安装目录> | 版本号 `1.2.0` |
| `<实验根目录>\ab-longrun-300\SE014-slugify\A-skill\task.md` | 任务上下文（仅读取，本阶段未改） |

未读取 references/（按 SKILL.md「加载证明」约定：加载证明只需 `SKILL.md` + `VERSION`，references 按需读取）。

## 本阶段范围声明

- 阶段1 only：完成加载证明后停止。
- 未修改 `slugify.py`。
- 未创建 `test_slugify.py` / `response.md`（属后续阶段）。
