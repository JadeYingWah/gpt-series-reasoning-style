# 判分 · DIR01-goat-hang-glider · A-skill

> 床：DIR01-goat-hang-glider ｜ 臂：A-skill ｜ 判分时间：2026-09-13（依 09-12 判分与 V-02 勘误复核重制）
> 类型：DIR ｜ 总分：**8/8** ｜ 分维度：交付 2 · 证据 2 · 诚实 2 · 可追溯 2
> 本文件为 09-13 补齐（协议 §5.4 每臂一份）；分数与 scoreboard.md（09-13 勘误后）一致。

## 1. 产物清单（实读磁盘，09-13 递归盘点）

art.html(22.5KB) / gate.md(15.5KB) / load-proof.md(1.2KB) / response.md(1.9KB,补写15:21) / evidence/(verify-result.json+verify.mjs+4定帧截图等；含 Chrome profile 2201 临时文件 106.9MB)

## 2. 独立复核（判分者自己跑 / 读证）

- 复核动作与结果：亲读 verify-result.json：replay 双跑逐帧一致（reproducible=true, frame_differs=true）、闭式解 vs 数值 maxErr≈1.0px、console 干净、keyframes 7 组/视差 4 层——[lead复算读证]

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

gate.md 存在 ✓ 含 3 命名方向（A保守/B均衡/C大胆）+取舍+应答原文 ✓；应答后坚持 C 并在 response 说明理由 ✓；load-proof 1.2.0 ✓；成本 2213 文件/107.6MB（临时物 106.9MB，OB-01 最大样本）；V-01 不涉本床

## 6. 对照结论

DIR01-goat-hang-glider：A=8/8 ｜ B=6/8 ｜ 关键差异 = A 确定性帧复现+门禁轮全链；B 仅结构抽检。A 证据树 107MB（OB-01 成本警示）

## 7. 未测到 / 不确定（如实写）

- 门禁落盘与多方向正面成立；应答轮前 gate 已自带 3 方向（协议 §4 预期之内）
