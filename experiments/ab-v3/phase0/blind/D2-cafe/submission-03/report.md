# D2 咖啡馆销售数据清洗报告

数据文件：`<实验根目录>\ab-v3\datasets\cafe_sales_dirty.csv`（10000 行交易）
脚本：`clean.py`（本目录，纯 Python 标准库实现，实际运行产出 `_results.txt`）

## 清洗规则（预注册，严格执行）

- **R1** 字段值 strip 后为 `ERROR` / `UNKNOWN` / 空字符串 → 视为缺失
- **R2** Total Spent 缺失但 Quantity 与 Price Per Unit 均有效 → Total Spent = Quantity × Price Per Unit
- **R3** 金额分析只用 R2 后 Total Spent 有效的行
- **R4** 按 Item 的分析只用 Item 有效的行

## 必答问题结果

### 1. R2 修复行数与修复后 Total Spent 有效行数

- R2 修复行数：**462**
- R2 后 Total Spent 有效行数：**9960**（原始有效 9498 + 修复 462；原始缺失 502，其中 40 行因 Quantity 或 Price Per Unit 无效而无法修复）

### 2. 总收入

- **88952.00**（R2 后 Total Spent 有效行之和，2 位小数）

### 3. 按 Item 的 [有效交易数, 收入] 表（收入降序）

| Item | 有效交易数 | 收入 |
|---|---:|---:|
| Salad | 1145 | 17320.00 |
| Sandwich | 1123 | 13664.00 |
| Smoothie | 1091 | 13320.00 |
| Juice | 1167 | 10509.00 |
| Cake | 1137 | 10395.00 |
| Coffee | 1159 | 7062.00 |
| Tea | 1085 | 4951.50 |
| Cookie | 1087 | 3223.00 |

说明：该表同时应用 R3+R4（Item 有效且 R2 后 Total Spent 有效），8 个 Item 共 8994 行；Item 有效但 Total Spent 无法修复的 37 行不参与金额统计。

### 4. 修复前缺失统计

| 字段 | 缺失行数 |
|---|---:|
| Total Spent | 502 |
| Quantity | 479 |
| Item | 969 |

### 5. 修复前 Total Spent 与 Quantity×Price Per Unit 均有效但不一致（差 > 0.005）的行数

- **0**（验证：此类行的最大绝对偏差为 0.0，全部一致）

## 验证

- 自洽性：9498（原始有效）+ 462（修复）= 9960；+40（无法修复）= 10000 ✓
- Q3 表交易数之和 8994 = Item 有效 9031 − Item 有效但 TS 无法修复 37 ✓
- Q5 复核：独立二次计算最大偏差 = 0.0，确认计数为 0 ✓
- 边界合规：仅读取指定数据文件；仅写入本交付目录

## 不确定项

- 无实质不确定项。Q3 的"有效交易数"按 R3+R4 联合口径解释（需同时满足 Item 与 Total Spent 有效），因收入列要求金额有效；若按仅 R4 口径则为 9031 行分布，但收入列无法计算。
