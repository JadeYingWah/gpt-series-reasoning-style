# D1 红酒质量分析报告（Bprime）

数据：`<实验根目录>\ab-v3\datasets\winequality-red.csv`（UCI Wine Quality 红）
加载方式：`pd.read_csv(sep=";", header=0)`；实测 shape=(1599, 12)，缺失值 0，重复行 240（未删除，保留原始数据口径）。

## 一、结论（必答问题）

### Q1 各理化指标与 quality 的 Pearson 相关系数（按 |r| 降序）

| 排名 | 指标 | Pearson r |
|---|---|---|
| 1 | alcohol | 0.476166 |
| 2 | volatile acidity | -0.390558 |
| 3 | sulphates | 0.251397 |
| 4 | citric acid | 0.226373 |
| 5 | total sulfur dioxide | -0.185100 |
| 6 | density | -0.174919 |
| 7 | chlorides | -0.128907 |
| 8 | fixed acidity | 0.124052 |
| 9 | pH | -0.057731 |
| 10 | free sulfur dioxide | -0.050656 |
| 11 | residual sugar | 0.013732 |

解释方向：酒精度越高、挥发性酸越低，质量倾向越高；残糖与质量几乎无关。

### Q2 quality 各档位样本计数

| quality | 3 | 4 | 5 | 6 | 7 | 8 | 合计 |
|---|---|---|---|---|---|---|---|
| 计数 | 10 | 53 | 681 | 638 | 199 | 18 | 1599 |

分布左偏、集中于 5/6 两档（合计 1319，占 82.5%）。

### Q3 高质组 vs 低质组的 alcohol 均值

| 组 | 定义 | n | alcohol 均值 |
|---|---|---|---|
| 高质组 | quality ≥ 7 | 217 | 11.5180 |
| 低质组 | quality ≤ 4 | 63 | 10.2159 |
| **差值（高−低）** | | | **+1.3022** |

## 二、方法

- 脚本：`analyze.py`（本目录，Python 3.14 + numpy 2.5.3 / pandas 3.0.5 / scipy 1.18.1）。
- 相关系数：`df.corr(method="pearson")` 逐列计算后按 |r| 降序排序，格式化到 6 位小数。
- 档位计数：`value_counts()` 并按 3~8 补齐输出。
- 组均值：布尔掩码筛选 `quality>=7`、`quality<=4` 后取 `alcohol.mean()`，差值 = 高 − 低。

## 三、数字如何验证

1. **相关系数四重互验**：pandas `corr`、`numpy.corrcoef`、`scipy.stats.pearsonr`、纯 numpy 手工 Pearson 公式（去中心化点积 / 开方）四种算法两两比对，全部差异 < 1e-12，脚本内置 assert 强制通过。
2. **计数双重互验**：`value_counts` 与逐档布尔求和 `(quality==k).sum()` 比对，一致；六档合计 1599 = 总行数，闭环。
3. **均值独立互验**：pandas `mean` 与 numpy 掩码均值（`x[q>=7].mean()`）比对，差异 < 1e-12。
4. **数据完整性**：shape=(1599,12) 与任务书一致；缺失值合计 0；列数恰为 11 指标 + quality（assert 校验）。
5. **量纲合理性**：alcohol 均值落在数据集酒精度范围（8.4~14.9）内；|r| ≤ 1；排序后第 1/2 名（alcohol、volatile acidity）与 UCI 数据集公开文献结论方向一致。

## 四、不确定项

- 240 条重复行未做去重（任务未要求，且去重会改变官方 1599 行口径）；若按去重口径计算，各数值会略有不同。
- 相关系数给出的是线性相关的点估计，未附 p 值/置信区间（任务未要求）。
