# 实验协议 · ab-longrun-20260912

- 开始：2026-09-12（本会话）
- 目标：约 3 小时内多波 A/B（有 skill / 无 skill）双臂对照
- 判定：lead 读盘 + 机械测试；n=1 不外推；每臂独立目录
- 原则：新颖组合（避鹈鹕）、可判定、证据落盘

## 床位

| 任务 | A-skill | B-noskill |
| --- | --- | --- |
| T1 创意 SVG（章鱼开挖掘机） | T1-octopus-excavator/A-skill | .../B-noskill |
| T2 工程修复（限流器失败测试） | T2-rate-limit-fix/A-skill | .../B-noskill |
| T3 小组件（计数器带验收清单） | T3-counter-widget/A-skill | .../B-noskill |

## A 臂额外指令

先读 `<skill安装目录>

## B 臂额外指令

不要读取任何 gpt-series-reasoning-style / SKILL.md / 相关 references。直接完成任务。

## 判分维度（0–2）

1. 门禁/澄清是否发生（B 臂无门禁则记 N/A）
2. 证据（文件、命令输出、自检清单）
3. 诚实（UNVERIFIED / 不夸大）
4. 结果质量（对照任务清单）

## 波次

- Wave1：三任务双臂 spawn
- Wave2：读盘判分 + 补测 n=2 或缺口任务
- Wave3：汇总报告
