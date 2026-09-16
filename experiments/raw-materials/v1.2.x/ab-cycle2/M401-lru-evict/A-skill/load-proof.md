# 加载证明（阶段 1 · 只读加载）

- 床号：M401-lru-evict（A 臂 · 带 skill）
- 阶段：阶段 1 · 只读加载（未实现任何业务产物）

## ① 版本号（逐字抄自 `VERSION`）

```
1.2.0
```

## ② 硬性规则第一条（逐字抄自 `SKILL.md` · Mandatory Pre-Implementation Gate → 硬性规则）

```
宣布阶段序列不是确认。
```

## ③ 协作架构（一句话）

默认单 Agent 主干（同一模型内切换规划/执行/审查面），按需扩展为「子 Agent 增强」或「指挥官多 Agent」，形态由 AI 按任务事实自选并在门禁声明一行理由，用户指名优先。

## ④ 已读文件完整路径清单

1. `<实验根目录>\ab-cycle2\M401-lru-evict\spawn-A.md`（仅读「阶段 1 · 只读加载」部分）
2. `<实验根目录>\ab-cycle2\skill-snapshot\SKILL.md`
3. `<实验根目录>\ab-cycle2\skill-snapshot\VERSION`

未读取机器上任何其他 skill 安装目录；未读取 `B-noskill` 目录；未读取本床 `task.md`（留待阶段 2）。
