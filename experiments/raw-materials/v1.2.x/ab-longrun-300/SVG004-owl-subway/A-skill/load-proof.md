# 加载证明 · gpt-series-reasoning-style

任务：SVG004-owl-subway · 阶段1（仅加载证明，禁止实现）

## 1. 版本号

1.2.0

（来源：`<skill安装目录> 与 SKILL.md 文末 `Current version: 1.2.0` 一致）

## 2. 逐字引用 · Mandatory Pre-Implementation Gate 硬性规则第一条

> 宣布阶段序列不是确认。

## 3. 协作架构简介

主干（默认）· 单 Agent 模式 —— 同一模型内部切换规划面、执行面、审查面；绝大多数任务由此完成。

扩展A · 子 Agent 增强 —— 任务适合并行或隔离且宿主支持子 Agent 时启用；启用前必须先确认子 Agent 能力。

扩展B · 指挥官多 Agent —— 需要协调独立大模型/Agent 时启用模式三协议；只影响启用的任务。

可混合搭配；形态由 AI 按任务事实自选并在门禁声明一行理由，用户指名优先、可随时切换。

## 4. 实际读过的文件

| 文件 | 路径 | 用途 |
|------|------|------|
| SKILL.md | `<skill安装目录> | 主规则全文 |
| VERSION | `<skill安装目录> | 版本号（1.2.0） |
| task.md | `<实验根目录>\ab-longrun-300\SVG004-owl-subway\A-skill\task.md` | 本任务交付与验收清单（工作目录内） |

未读取 references/（按需读取，阶段1 不需要）。

---

阶段1 到此结束。未创建项目目录、未编辑实现文件、未运行实现命令。
