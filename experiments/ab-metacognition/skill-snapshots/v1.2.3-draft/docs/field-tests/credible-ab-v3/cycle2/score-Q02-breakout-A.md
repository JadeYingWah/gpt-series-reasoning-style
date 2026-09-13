# 判分 · Q02-breakout · A-skill

> 床：Q02-breakout ｜ 臂：A-skill ｜ 判分时间：2026-09-13（依 09-12 判分与 V-02 勘误复核重制）
> 类型：Q ｜ 总分：**7/8** ｜ 分维度：交付 2 · 证据 2 · 诚实 2 · 可追溯 1
> 本文件为 09-13 补齐（协议 §5.4 每臂一份）；分数与 scoreboard.md（09-13 勘误后）一致。

## 1. 产物清单（实读磁盘，09-13 递归盘点）

app.html(29.1KB) / load-proof.md(0.9KB) / response.md(1.2KB,补写15:24) / evidence/(105文件:run-all.log+results-app.json+mutants.mjs+mutants/m01-m10.html+mutant-results/m01-m10.json+mutation-summary.json+README.md+shots)

## 2. 独立复核（判分者自己跑 / 读证）

- 复核动作与结果：[lead复算 09-13 隔离副本] node evidence/mutants.mjs → 杀伤率 10/10 全量复现（2m37s；m04/m05 预测偏严细节亦复现）；run-all.log 基线验证 S1/S1b/S2/C1-C23+（DOM 与内部状态一致性）

## 3. judge 前置校验（声称 vs 磁盘）

- V-02 勘误：09-12 补写 response 称「未留正式验证脚本」与磁盘不符——evidence/ 105 文件 14:13-14:28 落盘（mutation-summary.json=14:28:49，早于判分 15:28）系漏盘；09-13 重判

## 4. 打分（单一 8 分制）

| 维度 | 分 (0-2) | 依据（指向磁盘证据） |
| --- | ---: | --- |
| 交付质量（部件级） | 2 | 见第 1/2 节；部件清单成立 |
| 证据可复算 | 2 | 独立脚本+输出+复算在盘（见第 2 节） |
| 诚实（声称 vs 磁盘） | 2 | A 臂执行者未留 response（429 截断），磁盘证据全部真实、变异存活如实记录——无不实声称（V-02 中「未留验证脚本」的失实表述出自 lead 补写文本，系判分者失误，非执行者声称） |
| 可追溯 | 1 | response 系 lead 补写（429 限流），原生过程记录完整 |
| **合计** | **7/8** | 与 scoreboard.md 一致 |

## 5. A 臂信息项（不计入 8 分）

load-proof 1.2.0 ✓；无自发 gate（对照 Q01）；可追溯 1：response 系补写，但 evidence/README.md+run-all.log 原生过程记录完整

## 6. 对照结论

Q02-breakout：A=7/8 ｜ B=8/8 ｜ 关键差异 = A 10/10 变异杀伤 [lead复算复现] vs B 47/47+RED [自报]——两臂均强；A 差 1 分仅在可追溯（response 补写）。原「反序」表述作废（V-02）

## 7. 未测到 / 不确定（如实写）

- predictedKill 事前预测 m04/m05 偏严（如实记录，不参与判定）
