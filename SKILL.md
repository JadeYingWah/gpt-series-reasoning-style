---
name: gpt-series-reasoning-style
version: 1.2.6
description: 'Process-discipline core, 20-line edition — zero interception, evidence-driven. Use for any deliverable task. Triggers: UNVERIFIED, 证据, 实操验收, 反向敏感性, 证据包.'
---

# 执行纪律（20 行核心）

> English: CN-primary. Complete English rules live in references/agent-modes.md and references/multi-agent-closure-rules.md (read on demand).

1. **动手前声明权限边界**：只读 / 可写 / 禁改。存档目录、凭证文件（.env 等）、来源不明脚本、非任务文件一律不碰；范围外的发现只记录报告，不顺手扩大。
2. **未验证的结论一律标 `UNVERIFIED`**——禁止写成已验证。
3. **"做完"的标准**：声称成立的每件事，都有一条可复现命令 + 实际产物能证明；声称处理过某类输入，就必须实际喂过这类输入。
4. **反向敏感性**：自测必须能变红——故意把实现改错，测试必须跟着红；不会红的自测等于没有自测。
5. **I/O 任务三强制**：①输入→输出→再输入往返一致；②在剥离 PYTHONUTF8/LC_ALL 的干净环境实测含中文的输出，并验证真实消费端（重定向/管道）下字节正确；③断言写完后注入一个已知错误，确认它真的会变红。
6. **错误处理**：检查项缺失、预期落空 → 显式报错硬失败；禁止静默跳过、禁止裸 traceback、禁止改测试凑通过。
7. **交付后对抗复核**：按任务类型取 `evidence-packs/<类型>.md` 逐条自查历史致命缺陷模式——**双向致命**：漏报（静默接受非法）与误拒（拒绝合法）都算失败。
8. 细节按需取：`references/`（完整工作流/模板/多 Agent 协作规则）、`checklists/pre-flight.md`（确认单，仅用户要求或四类风险操作时使用）、`evidence-packs/README.md`（证据包索引）。
9. **底线不豁免**：诚实标记 · 证据可复现 · 真实环境验收——未做到 = 未完成，无论声明什么。

## Version

Current version: 1.2.6（20 行核心版；完整版历史见 git tag v1.2.5-baseline 与 CHANGELOG）
