# D2 · 咖啡馆销售数据清洗报告（A1）

数据文件：`<实验根目录>\ab-v3\datasets\cafe_sales_dirty.csv`（10000 行交易记录，8 列）
执行脚本：`clean_analyze.py`（与本报告同目录；复现命令见文末）
skill 版本：（匿名化省略）

## 数据质量说明

- 列结构：Transaction ID / Item / Quantity / Price Per Unit / Total Spent / Payment Method / Location / Transaction Date。
- 缺失表示：字段值 strip 后为 `ERROR` / `UNKNOWN` / 空字符串（R1）。探查确认三个数值列（Quantity、Price Per Unit、Total Spent）除上述标记外全部可解析为数值，无其他脏格式（如带符号、千分位）。
- 修复前缺失分布（Q4）：Total Spent 502 行（空 173 / UNKNOWN 165 / ERROR 164）、Quantity 479 行（171/170/138）、Item 969 行（UNKNOWN 344 / 空 333 / ERROR 292）。
- Item 有效值共 8 个品类：Juice、Coffee、Salad、Cake、Sandwich、Smoothie、Cookie、Tea。

## 必答问题结果

### Q1. R2 修复与修复后有效率

- **R2 修复行数 = 462**（Total Spent 缺失，且 Quantity 与 Price Per Unit 均有效，按 Total Spent = Quantity × Price Per Unit 回填）
- **R2 后 Total Spent 有效行数 = 9960**（= 10000 − 40；40 行为 Total Spent 缺失且 Quantity/PPU 至少一项无效、无法修复的行。自洽：502 − 462 = 40）

### Q2. 总收入

- **总收入 = 88952.00**（R2 后 Total Spent 有效的 9960 行之和，2 位小数）
- 分解自洽：修复前有效 Total Spent 之和 84763.50（9498 行）+ R2 修复 462 行之和 4188.50 = 88952.00

### Q3. 按 Item 的 [有效交易数, 收入] 表（R4：只用 Item 有效的行，按收入降序）

主口径（口径 M）：交易数 = Item 有效的行数；收入 = 其中 R2 后 Total Spent 有效行之和。

| Item | 有效交易数 | 收入 |
|---|---:|---:|
| Salad | 1148 | 17320.00 |
| Sandwich | 1131 | 13664.00 |
| Smoothie | 1096 | 13320.00 |
| Juice | 1171 | 10509.00 |
| Cake | 1139 | 10395.00 |
| Coffee | 1165 | 7062.00 |
| Tea | 1089 | 4951.50 |
| Cookie | 1092 | 3223.00 |
| **合计** | **9031** | **80444.50** |

口径说明（透明并列，防口径歧义）：
- 「有效交易数」若取**与收入同口径**（Item 有效且 Total Spent R2 后有效的行数，口径 S），则为：Salad 1145、Sandwich 1123、Smoothie 1091、Juice 1167、Cake 1137、Coffee 1159、Tea 1085、Cookie 1087，合计 8994。收入数字两口径完全相同。
- Item 列收入合计 80444.50 ≠ 总收入 88952.00，差额 8507.50 来自 Item 无效（969 行）但 Total Spent 有效（966 行）的交易——R3/R4 各自独立约束行集所致，属预期行为，非数据错误。

### Q4. 修复前缺失统计

| 字段 | 缺失行数 |
|---|---:|
| Total Spent | 502 |
| Quantity | 479 |
| Item | 969 |

### Q5. 修复前 Total Spent 与 Quantity×Price Per Unit 不一致（差>0.005）行数

- **0 行**。三字段均有效的 9498 行中，|Total Spent − Quantity×Price Per Unit| 最大值 = 0，即全部精确一致。

## 方法与验证（证据报告）

**双独立实现交叉验证（全量、全部指标一致 PASS）**：
- 实现A（权威）：纯 Python `csv` + `Decimal` 精确算术（无浮点误差）
- 实现B（独立计算路径）：标准库 `sqlite3` SQL 引擎（CTE + REAL 聚合），Q4/Q1/Q2/Q5 及 Q3 两口径逐项比对，全部一致

**数据准确性抽查（循环审查第 1 轮）**：
- R2 修复乘法人工核对样本（4×1.0=4.0、3×4.0=12.0、2×1.5=3.0 等）正确
- Q5=0 的鉴别力检验：将不一致阈值从 0.005 收紧到 0.0001，仍为 0 行——结论非阈值卡出，修复前 Total Spent 与乘积确实精确一致
- 收入分解自洽：84763.50 + 4188.50 = 88952.00；80444.50 + 8507.50 = 88952.00
- 缺失计数与独立探查（逐列 Counter）一致

**闭环检查（对照门禁声明）**：任务类型=数据类（严格执行：独立计算必选 ✓、2 轮审查 ✓、数据质量说明 ✓）；资源盘点=仅 Python 标准库（pandas 未安装，任务书限定"已装库可用"，改用 sqlite3 交叉验证，效力等同且已声明）；跳过项=网络搜索（规则已预注册、无设计决策空间，质量影响评估：无）。任务参照系无变更（执行中口径风险在 Q3 处以双口径并列化解，未改变目标与质量标准）。

**简化项清单**：无（未砍任何已计划能力）。

**UNVERIFIED 项**：无。所有数字均由脚本实际运行产出并经双实现交叉验证。

## 复现命令

```
python <实验根目录>/ab-v3/phase0/D2-cafe/A1/clean_analyze.py
```

预期输出末行：`交叉验证总结: 全部一致 PASS`。

## 循环审查第 2 轮（交付完整性）

- report.md 数字与脚本 stdout 逐项核对一致；两交付物（report.md、clean_analyze.py）均在指定交付目录；运行时无临时落盘文件（抽查以内联命令执行，无残留需清理）。
