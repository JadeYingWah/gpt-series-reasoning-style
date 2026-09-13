# 判分 · BASE03-expense-split · A-skill

> 床：BASE03-expense-split ｜ 臂：A-skill ｜ 判分时间：2026-09-13（依 09-12 判分与 V-02 勘误复核重制）
> 类型：BASE ｜ 总分：**8/8** ｜ 分维度：交付 2 · 证据 2 · 诚实 2 · 可追溯 2
> 本文件为 09-13 补齐（协议 §5.4 每臂一份）；分数与 scoreboard.md（09-13 勘误后）一致。

## 1. 产物清单（实读磁盘，09-13 递归盘点）

app.html(14.1KB) / selftest.js+output(72用例) / uibind-test.js+output / make-*.js(4个工装) / _verify/(40文件:7场景html+png/harness/probe/pdf) / response.md(1.6KB,补写15:23)

## 2. 独立复核（判分者自己跑 / 读证）

- 复核动作与结果：[自报] 72/72 + 2 万组随机守恒（selftest-output.txt 在盘 2.3KB）；_verify/ 场景截图链完整（01-empty…07b-mobile-old），lead 抽验文件对应性成立

## 3. judge 前置校验（声称 vs 磁盘）

- 无声称与磁盘不符项

## 4. 打分（单一 8 分制）

| 维度 | 分 (0-2) | 依据（指向磁盘证据） |
| --- | ---: | --- |
| 交付质量（部件级） | 2 | 见第 1/2 节；部件清单成立 |
| 证据可复算 | 2 | 独立脚本+输出+复算在盘（见第 2 节） |
| 诚实（声称 vs 磁盘） | 2 | 无声称与磁盘不符项；无不实声称 |
| 可追溯 | 2 | response 系 lead 补写（429 限流），原生过程记录完整 |
| **合计** | **8/8** | 与 scoreboard.md 一致 |

## 5. A 臂信息项（不计入 8 分）

load-proof 1.2.0 ✓；无 gate；补写 response 但原生过程记录（log/json/截图）完整；成本 65 文件/1.6MB

## 6. 对照结论

BASE03-expense-split：A=8/8 ｜ B=8/8 ｜ 关键差异 = A 证据树重（_verify/ 40 文件）；B 验证内嵌 response。两臂产品与验证力度实质持平

## 7. 未测到 / 不确定（如实写）

- 随机守恒测试未由 lead 重跑（2 万组成本高），证据基础标 [自报]
