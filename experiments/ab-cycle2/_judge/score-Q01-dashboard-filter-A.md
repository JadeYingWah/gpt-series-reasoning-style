# 判分 · Q01-dashboard-filter · A-skill

> 床：Q01-dashboard-filter ｜ 臂：A-skill ｜ 判分时间：2026-09-13（依 09-12 判分与 V-02 勘误复核重制）
> 类型：Q ｜ 总分：**7/8** ｜ 分维度：交付 2 · 证据 2 · 诚实 2 · 可追溯 1
> 本文件为 09-13 补齐（协议 §5.4 每臂一份）；分数与 scoreboard.md（09-13 勘误后）一致。

## 1. 产物清单（实读磁盘，09-13 递归盘点）

app.html(24.0KB) / pre-gate.md(6.7KB,自发门禁14:05) / load-proof.md(0.8KB) / response.md(1.6KB,补写15:23) / _mutant.html(24.0KB,变异输入) / evidence/(29文件:independent-recompute+expected.json/browser-check.mjs+json+8截图/mutation-test.mjs+json/static-check)

## 2. 独立复核（判分者自己跑 / 读证）

- 复核动作与结果：[lead复算 09-13 隔离副本] node evidence/browser-check.mjs → 38/38 全过复现（含正控红检 C5-detector-red、断网重载 C7-offline、非法输入 C4c 全家桶）；变异 6 杀 4 存活如实记录（killRate 0.6）

## 3. judge 前置校验（声称 vs 磁盘）

- V-02 勘误：09-12 补写 response 称「未留下正式验证脚本/报告」与磁盘不符——evidence/ 29 文件 14:06-14:27 落盘（早于判分时刻 15:28），系判分时漏盘；09-13 重判

## 4. 打分（单一 8 分制）

| 维度 | 分 (0-2) | 依据（指向磁盘证据） |
| --- | ---: | --- |
| 交付质量（部件级） | 2 | 见第 1/2 节；部件清单成立 |
| 证据可复算 | 2 | 独立脚本+输出+复算在盘（见第 2 节） |
| 诚实（声称 vs 磁盘） | 2 | A 臂执行者未留 response（429 截断），磁盘证据全部真实、变异 4 存活如实记录——无不实声称（V-02 中「未留验证脚本」的失实表述出自 lead 补写文本，系判分者失误，非执行者声称） |
| 可追溯 | 1 | response 系 lead 补写（429 限流），原生过程记录完整 |
| **合计** | **7/8** | 与 scoreboard.md 一致 |

## 5. A 臂信息项（不计入 8 分）

load-proof 1.2.0 ✓；pre-gate.md 为非 DIR 床自发门禁落盘（14:05 早于 app.html 14:13，时序可证；含风险分档/形态/保守大胆否决对比/计划）——无人应答床自发落盘的正面样本；可追溯 1：response 系补写（原生结论记录缺失）

## 6. 对照结论

Q01-dashboard-filter：A=7/8 ｜ B=8/8 ｜ 关键差异 = B 116+62 [lead复算] vs A 38/38+变异 [lead复算 09-13 复现]——两臂验证均强且可复算；A 差 1 分仅在可追溯（response 补写）。原「反序」表述作废（V-02）

## 7. 未测到 / 不确定（如实写）

- 变异测试 4 存活变异体（M4/M7/M9/M10）未修复复验——A 臂原生如实记录，不构成扣分但如实记录
