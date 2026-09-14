# 文档导航 / Documentation Index

本目录包含项目的历史文档、提案、实验报告与评审记录。

## 文档结构

| 目录/文件 | 性质 | 说明 |
|---|---|---|
| `minimal-discipline.md` | **当前** | 最小纪律摘要（可独立使用的精简版） |
| `VERSION-TAGS.md` | **当前** | 版本与 tag 策略说明 |
| `HANDOVER-REPORT-2026-09-13.md` | **当前** | 2026-09-13 交接报告 |
| `field-tests/` | 历史归档 | 早期 A/B 实验报告（2026-09-08 ~ 2026-09-13） |
| `reviews/` | 历史归档 | 外部评审与内部审计记录 |
| `proposals/` | 历史归档 | 规则修订提案（多数已裁决或合并） |
| `plans/` | 历史归档 | 实验计划草案 |
| `selftest-run/` | 历史归档 | 自测运行判定记录 |

## 重要说明

**历史文档中的数字反映撰写时的版本状态，不代表当前版本。**

例如：
- 2026-09-08 ~ 2026-09-09 的文档中 self-test 条数为 **67**，当前已扩容至 **77** 条并冻结
- 早期文档中的身份数、references 数、SB 检查项数等均可能与当前不同
- 当前权威数字以 `SKILL.md`、`README.md`、`scripts/selfcheck.py` 为准

**最新实验记录**不在本目录，而在仓库根目录的 `experiments/` 下（含 ab-metacognition 系列、ab-cycle2 等）。

## 当前版本权威来源

| 信息 | 权威文件 |
|---|---|
| skill 规则 | `SKILL.md` |
| 版本号 | `VERSION` |
| 项目说明 | `README.md` |
| 变更历史 | `CHANGELOG.md` |
| 静态自检 | `scripts/selfcheck.py`（SB1-SB23） |
| 行为自测 | `references/self-test.md`（77 条冻结） |
