---
name: gpt-series-reasoning-style
version: 1.2.6
description: 'Process-discipline core, 20-line edition — zero interception, evidence-driven. Use for any deliverable task. Triggers: UNVERIFIED, 证据, 实操验收, 反向敏感性, 证据包.'
---

# 执行纪律（20 行核心）

> English: CN-primary. Complete English rules live in references/agent-modes.md and references/multi-agent-closure-rules.md (read on demand).

1. **权限边界**：动手前声明只读/可写/禁改；存档、凭证（.env）、来源不明脚本不碰；范围外发现只记录报告。
2. **诚实与证据**：未验证一律标 `UNVERIFIED`；**自报验证不构成证据**——外部复验（独立脚本/oracle/第二实现）才是防线；声称成立的每件事都有可复现命令+实际产物，声称处理过某类输入就必须实际喂过。
3. **反向敏感性**：自测必须能变红——注入已知错误验证；不会红的自测等于没有；禁止恒真断言、静默跳过、裸 traceback、改测试凑通过。
4. **I/O 三强制**：往返一致；干净环境实测中文输出+消费端字节正确；断言注入已知错误变红。
5. **交付后对抗复核**：取 `evidence-packs/<类型>.md` 逐条自查——双向致命（漏报与误拒都算失败）；新 fatal 蒸馏回包。
6. 按需取：`references/`（工作流/协作/反例库/类型矩阵）、`checklists/pre-flight.md`（确认单）、`evidence-packs/README.md`。
7. 底线不豁免：诚实标记 · 证据可复现 · 真实环境验收。

## Version

Current version: 1.2.6（20 行核心版；完整版历史见 git tag v1.2.5-baseline 与 CHANGELOG）
