# ab-v4 补测实验（覆盖缺口验证）

- 启动：2026-09-13 15:15 · 执行：判分/验收侧 lead（总指挥授权 spawn 子智能体）
- 目的：验证覆盖缺口分析（`gpt-series-reasoning-style-workspace/docs/coverage-gap-analysis-2026-09-13.md`）中的 D 档零覆盖条款
- 协议基准：credible-ab-v3-protocol（21 项缺陷对策）

## 装置级改进（相对 cycle-2 / Phase 0）

| 改进 | 内容 | 针对缺口 |
|---|---|---|
| 任务类型 | 首次引入 **GUI 交互类任务**（P-A 三床） | D 档 #1 实操闭环正向路径 |
| 强制落盘 | 全部 A2+ 臂要求 evidence/ 强制入盘 | A2+ 卫生瑕疵② |
| 分段落盘 | P-B 中断臂要求分阶段即时落盘 | D 档 #2 中断保护 |
| 分支覆盖 | P-B 含保守度调节**两个分支**（保守 + 全量） | D 档 #13 |
| 归档审计 | 全部执行走 jsonl 归档 | 缺陷⑤⑳ |

## 床位清单

| 床 | 任务 | 臂 | 状态 |
|---|---|---|---|
| G1-calculator | 单页计算器（含 0.1+0.2 精度陷阱） | Bprime / A2 / A2plus | 运行中 |
| G2-formvalidator | 表单校验组件 | Bprime / A2 / A2plus | 运行中 |
| G3-dashboard | 静态数据看板 | Bprime / A2 / A2plus | 运行中 |
| P-B/D3-conservative | 时序异常检测·保守度调节版 | A2+ | 运行中 |
| P-B/D3-noconstraint | 时序异常检测·无保守度对照 | A2+ | 运行中 |
| P-B/D3-fullreport | 时序异常检测·全量报告分支 | A2+ | 运行中 |
| P-B/D3-interrupt | 时序异常检测·中断场景 | A2+ | 运行中 |

## 冻结清单（SHA256）

- skill 快照：SKILL.md `bf57729b90e7af1748756f3de8ac5c826e16450ed7925751890960fd3f6cd40e`，VERSION `d7c5f05b8f509e61cbb54803e95dedf5b328af81cd5456f7554fb2990f91acce`（=1.2.1）
- 13 份预注册任务书：见 `truth/prompts-sha256.txt`
- 数据：复用 ab-v3/datasets（winequality / cafe_sales / nab_machine_temp）

## 未决项（本批不含，待 Stage 1 验收后放量）

- P-C 中等档 + 类型漂移 + 参照系变更（4 执行）
- P-D 五类型 v3 复证（15 执行，建议并入 Phase 1）
- P-E 条款执行率合规审计（纯 jsonl 审计）
