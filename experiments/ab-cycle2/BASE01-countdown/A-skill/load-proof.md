# 加载证明（A 臂 · 阶段 1 只读加载）

## ① 版本号

1.2.0

## ② 硬性规则第一条（逐字抄自 SKILL.md「Mandatory Pre-Implementation Gate」下「硬性规则」）

宣布阶段序列不是确认。

## ③ 协作架构（一句话概括）

单 Agent 主干（默认，同一模型内切换规划面/执行面/审查面）＋两个按需扩展：扩展A「子 Agent 增强」（适合并行或隔离且宿主支持子 Agent 时）、扩展B「指挥官多 Agent」（需协调独立大模型/Agent 或用户转交时），形态由 AI 按任务事实自选并在门禁声明一行理由、用户指名优先、可随时切换，可混合搭配。

## ④ 已读文件完整路径清单

- `<实验根目录>\ab-cycle2\skill-snapshot\SKILL.md`
- `<实验根目录>\ab-cycle2\skill-snapshot\VERSION`

本阶段未读取机器上任何其他 skill 安装目录；未创建任何业务产物。
