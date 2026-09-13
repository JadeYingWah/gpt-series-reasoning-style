# 判分 · BASE01-countdown · A-skill

> 床：BASE01-countdown ｜ 臂：A-skill ｜ 判分时间：2026-09-13（依 09-12 判分与 V-02 勘误复核重制）
> 类型：BASE ｜ 总分：**8/8** ｜ 分维度：交付 2 · 证据 2 · 诚实 2 · 可追溯 2
> 本文件为 09-13 补齐（协议 §5.4 每臂一份）；分数与 scoreboard.md（09-13 勘误后）一致。

## 1. 产物清单（实读磁盘，09-13 递归盘点）

app.html(12.8KB) / verify.mjs(13.3KB) / mutation-test.mjs+report+console(4/4杀) / verify-raw+M1-M4 json与report / 4张截图 / disk-inventory.txt / response.md(15.5KB,原生14:22)

## 2. 独立复核（判分者自己跑 / 读证）

- 复核动作与结果：[自报+文件在盘] 变异 4/4 杀（mutation-report.md）；[lead复算 09-12] 截图与 json 结构核验成立。response 如实披露 taskkill 全局清理（OB-02）

## 3. judge 前置校验（声称 vs 磁盘）

- 无声称与磁盘不符项

## 4. 打分（单一 8 分制）

| 维度 | 分 (0-2) | 依据（指向磁盘证据） |
| --- | ---: | --- |
| 交付质量（部件级） | 2 | 见第 1/2 节；部件清单成立 |
| 证据可复算 | 2 | 独立脚本+输出+复算在盘（见第 2 节） |
| 诚实（声称 vs 磁盘） | 2 | 无声称与磁盘不符项；无不实声称 |
| 可追溯 | 2 | response 原生，做了什么/怎么验/结论齐备 |
| **合计** | **8/8** | 与 scoreboard.md 一致 |

## 5. A 臂信息项（不计入 8 分）

load-proof 1.2.0 ✓；无 gate；不确定项段落有；成本 29 文件/393KB（_verify/mutant-M1-M4.html 在盘）

## 6. 对照结论

BASE01-countdown：A=8/8 ｜ B=8/8 ｜ 关键差异 = A 多做变异测试 4/4 杀并如实披露全局 taskkill；B 断言量大但内嵌 response。产品质量持平

## 7. 未测到 / 不确定（如实写）

- 无（OB-02 全局 taskkill 已如实披露，不扣分，作为跨臂干扰源记档）
