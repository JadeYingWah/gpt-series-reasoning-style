# 红酒质量分析报告（D1 · A2+ 臂）

> **可检查完成标准**：11 项 Pearson 相关系数（6 位小数、按 |r| 排序）、quality 3~8 档位计数、alcohol 高低质组均值（4 位小数）及差值，全部由 3 条独立计算路径交叉验证一致，且验证脚本与结果均入 evidence/ 目录。

## 一、数据概况

- 数据集：`winequality-red.csv`（UCI Wine Quality，分号分隔、带引号表头）
- 行数：1599，列数：12（11 理化指标 + quality）
- 数据完整性：无 NaN、无 Inf；quality 取值范围 [3, 8]

## 二、必答问题结果

### 1. 各理化指标与 quality 的 Pearson 相关系数

按绝对值从大到小排序，保留 6 位小数：

| 排名 | 指标 | Pearson r | 变异测试确认 |
|---:|---|---:|:---:|
| 1 | alcohol | +0.476166 | ✅ |
| 2 | volatile acidity | -0.390558 | ✅ |
| 3 | sulphates | +0.251397 | ✅ |
| 4 | citric acid | +0.226373 | ✅ |
| 5 | total sulfur dioxide | -0.185100 | ✅ |
| 6 | density | -0.174919 | ✅ |
| 7 | chlorides | -0.128907 | ✅ |
| 8 | fixed acidity | +0.124052 | ✅ |
| 9 | pH | -0.057731 | ⚠️ 候选 |
| 10 | free sulfur dioxide | -0.050656 | ⚠️ 候选 |
| 11 | residual sugar | +0.013732 | ⚠️ 候选 |

**保守度裁决**：前 8 项经 1000 次置换变异测试确认（真实 |r| > 置换最大 |r|），为主报告结论；后 3 项（pH、free sulfur dioxide、residual sugar）的真实相关系数未超过随机置换的最大绝对值，统计上不显著，列入附录候选，不纳入主报告的"显著相关"结论。

### 2. quality 各档位样本计数

| quality | 3 | 4 | 5 | 6 | 7 | 8 | 合计 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 样本数 | 10 | 53 | 681 | 638 | 199 | 18 | 1599 |

### 3. 高质组与低质组的 alcohol 均值

| 组别 | 条件 | 样本数 | alcohol 均值 |
|---|---|---:|---:|
| 高质组 | quality ≥ 7 | 217 | 11.5180 |
| 低质组 | quality ≤ 4 | 63 | 10.2159 |
| **差值** | 高质 − 低质 | — | **1.3022** |

Bootstrap 95% 置信区间（10000 次重采样）：[1.0378, 1.5619]，点估计 1.3022 落在区间内，差值稳健。

## 三、方法与验证

### 三条独立计算路径

| 运行 | 方法 | 读取方式 | 相关系数计算 |
|---|---|---|---|
| Run 1 | numpy 主实现 | `np.genfromtxt` | `np.corrcoef` |
| Run 2 | 纯 Python 公式推导 | `csv` 模块 | 手动公式 r = Σ(x-x̄)(y-ȳ) / √(Σ(x-x̄)²·Σ(y-ȳ)²) |
| Run 3 | numpy 中心化点积 + 变异测试 + Bootstrap | `np.genfromtxt` | 中心化后点积 `xc·yc / (‖xc‖·‖yc‖)` |

### 交叉验证结果

- **数据形状**：3 路径一致（1599×12）✅
- **11 项相关系数**：3 路径在 6 位小数精度下完全一致 ✅
- **6 档 quality 计数**：3 路径完全一致，合计 1599 ✅
- **alcohol 均值/差值/样本数**：3 路径在 4 位小数精度下完全一致 ✅
- **总体一致性**：PASS

### 变异测试（Permutation Test）

将 quality 标签随机打乱 1000 次，重新计算各指标的相关系数：
- 前 8 项指标的真实 |r| 均大于 1000 次置换中的最大 |r| → 相关非随机
- pH（真实 |r|=0.0577 < 置换最大 0.0786）、free sulfur dioxide（0.0507 < 0.0837）、residual sugar（0.0137 < 0.0779）→ 无法排除随机可能

## 四、附录：候选/待确认项

以下指标的 Pearson 相关系数由 3 条计算路径一致得出，但未通过变异测试的统计显著性确认，列为候选：

| 指标 | Pearson r | 置换最大 |r| | 状态 |
|---|---:|---:|---|
| pH | -0.057731 | 0.078611 | 候选，不显著 |
| free sulfur dioxide | -0.050656 | 0.083659 | 候选，不显著 |
| residual sugar | +0.013732 | 0.077914 | 候选，不显著 |

## 五、交付文件清单

```
A2plus/
├── report.md                          ← 本报告
├── run1_numpy_analysis.py             ← Run1 脚本（numpy corrcoef）
├── run2_purepython_analysis.py        ← Run2 脚本（纯Python公式）
├── run3_mutation_bootstrap.py         ← Run3 脚本（中心化点积+变异+Bootstrap）
└── evidence/
    ├── run1_results.json              ← Run1 结果
    ├── run2_results.json              ← Run2 结果
    ├── run3_results.json              ← Run3 结果（含完整性、变异、Bootstrap）
    ├── run3_mutation_log.txt          ← 变异测试详细日志
    ├── cross_validate.py              ← 交叉验证比对脚本
    ├── cross_validation_report.json   ← 交叉验证结构化报告
    └── cross_validation_log.txt       ← 交叉验证可读日志
```

## 六、不确定项

1. pH / free sulfur dioxide / residual sugar 三项的弱相关在统计上不显著（变异测试未通过），主报告已保守排除，仅列附录。
2. alcohol 差值的 Bootstrap CI 为 [1.04, 1.56]，点估计 1.30 稳健，但未做正态性检验（样本量充足时 CLT 可近似）。
3. 本分析仅基于 Pearson 线性相关，未探索非线性关系；如需可进一步计算 Spearman 秩相关。
