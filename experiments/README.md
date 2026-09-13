# Experiments Archive / 实验归档

本目录归档 gpt-series-reasoning-style skill 从古至今的全部 A/B 实验与验证测试。

## 总览

- **实验总数**: 41 个
- **归档时间**: 2026-09-13
- **总大小**: ~65MB（已清理 node_modules、浏览器 profile、缓存等临时文件）
- **数据构成**: 报告(.md) 1267份、代码(.py/.js/.mjs) 500份、截图(.png) 309份、数据集(.csv) 60份

## 实验分类索引

### 1. 基线对照组（B′ / No-skill）

| 目录 | 说明 |
|------|------|
| `ab-bprime-all-types/` | 全类型 B′ 对照组合集报告 |
| `ab-adventure-bprime/` | 冒险类任务 B′ 对照 |
| `ab-code-bprime/` | 代码类任务 B′ 对照 |
| `ab-creative-bprime/` | 创意类任务 B′ 对照 |
| `ab-data-baseline/` | 数据类任务基线对照 |
| `ab-modeling-bprime/` | 建模类任务 B′ 对照 |
| `ab-research-bprime/` | 研究类任务 B′ 对照 |
| `ab-visual-bprime/` | 视觉类任务 B′ 对照 |

### 2. 单类型 A/B 实验（8 种任务类型）

| 目录 | 任务类型 | 报告 |
|------|---------|------|
| `ab-adventure/` | 冒险类 | REPORT.md |
| `ab-code/` | 代码类 | — |
| `ab-creative/` | 创意类 | REPORT.md |
| `ab-data/` | 数据类 | REPORT.md |
| `ab-modeling/` | 建模类 | REPORT.md |
| `ab-research/` | 研究类 | REPORT.md |
| `ab-visual/` | 视觉类 | REPORT.md |
| `ab-compound/` | 复合任务 | REPORT.md |

### 3. 解耦实验（Decoupled，隔离变量）

| 目录 | 说明 |
|------|------|
| `ab-decoupled-adventure/` | 冒险类解耦 |
| `ab-decoupled-code/` | 代码类解耦（54 files，含完整产物） |
| `ab-decoupled-complex/` | 复杂任务解耦 |
| `ab-decoupled-creative/` | 创意类解耦 |
| `ab-decoupled-modeling/` | 建模类解耦 |
| `ab-decoupled-research/` | 研究类解耦（含 report.md） |
| `ab-decoupled-visual/` | 视觉类解耦 |

### 4. Cycle 系列（多轮迭代 A/B）

| 目录 | 说明 | 关键产物 |
|------|------|---------|
| `ab-cycle2/` | Cycle 2 完整试点（12床×双臂，含判分证据） | _judge/ 判分文件、scoreboard |
| `ab-cycle3-suppression/` | Cycle 3 抑制实验 |
| `ab-cycle4-effectiveness/` | Cycle 4 有效性实验（skill 首次跑赢基线） | order-report.html |
| `cycle5-clean/` | Cycle 5 干净对照（隔离污染） | order-report.html |

### 5. 配置与流程实验

| 目录 | 说明 |
|------|------|
| `ab-medium-config/` | 中档配置实验（含 REPORT.md） |
| `ab-medium-config-v2/` | 中档配置 v2 |
| `ab-modular-selection/` | 模块化选择矩阵实验（含 REPORT.md） |

### 6. 长运行实验

| 目录 | 说明 |
|------|------|
| `ab-longrun-20260912/` | 2026-09-12 长运行测试（35 files） |
| `ab-longrun-300/` | 300 轮长运行实验（877 files，含 README.md） |

### 7. 元认知能力实验

| 目录 | 说明 |
|------|------|
| `ab-metacognition/` | 元认知能力对 skill 效果影响的完整实验（650 files） |
| | 含 E1-E4 能力测试床、T1 任务、v1.2.3 修订验证、能力-效果映射分析 |
| | 关键报告：EXPERIMENT-REPORT.md、V123-VERDICT-REPORT.md |

### 8. Stage 系列（大规模盲评）

| 目录 | 说明 | 关键报告 |
|------|------|---------|
| `ab-v3/` | Stage 1：Phase 0 核验 + A2+ 先锋核验（134 files） | anonymize_report.json、datasets/ |
| `ab-v4/` | Stage 1：13 臂盲评五维评分（332 files） | FINAL-VERIFY-REPORT.md、SYNC-PACK |
| `ab-v5/` | Stage 2：合规性测试（83 files） | FINAL-STAGE2-REPORT.md |

### 9. 验证与强度测试

| 目录 | 说明 |
|------|------|
| `ab-validation-batch65/` | 第 65 批验证 |
| `ab-validation-batch77/` | 第 77 批验证（含 README.md） |
| `ab-verify-strength/` | skill 强度验证 |
| `ab-n3-code/` | N3 代码类测试（30 files） |
| `ab-n3-creative/` | N3 创意类测试 |

## 归档说明

### 已清理的内容
- `node_modules/` — 依赖包，可通过 package.json 重建
- `_chrome-profile*/` — 浏览器运行时 profile（缓存、Cookie、临时文件）
- `__pycache__/` — Python 字节码缓存
- `.git/` — 子仓库 git 目录

### 保留的内容
- 所有实验报告（.md）
- 所有代码产物（.py / .js / .mjs / .html）
- 所有测试脚本与验证证据
- 所有截图证据（.png）
- 所有数据集（.csv / .json）
- 所有配置文件与任务书

### 脱敏状态
- 真实姓名已替换为「总指挥」/「lead」
- 本地路径已替换为 `<实验根目录>` / `<用户目录>`
- 用户名已脱敏

## 相关文档

- `docs/field-tests/` — 精选实验报告归档（与本目录互补）
- `docs/VERSION-TAGS.md` — 版本与 tag 说明
- `INTERNAL-HISTORY.md` — 内部版本迭代历史
- `CHANGELOG.md` — 公开版本变更记录
