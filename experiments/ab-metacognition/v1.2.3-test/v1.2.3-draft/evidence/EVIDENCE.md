# 证据报告 — CSV 解析器（v1.2.3-draft / 轻量·验证聚焦版）

日期：2026-09-13 ｜ 环境：Windows 11，Python 3.13.14，零第三方依赖。

## 1. 完成声明与复算说明

csv_parser.py 单文件零依赖 CSV 解析器已交付，任务书 7 项功能与 6 项边界情况全部实现并通过验证（29/29），变异反例测试 4/4 全杀。

**复算说明（第三方在干净环境执行，应得到相同结果）**：
```
cd <实验根目录>\ab-metacognition\v1.2.3-test\v1.2.3-draft\evidence
python -m py_compile ../csv_parser.py verify.py mutate_and_check.py   # 预期无输出
python verify.py                                                      # 预期 29/29 passed, ALL GREEN, exit 0
python mutate_and_check.py                                            # 预期 4/4 KILLED, exit 0
```
不依赖本地环境变量/缓存；CLI 测试 fixture 由 verify.py 动态生成于系统临时目录并自动清理（避免静态文件被行尾转换破坏）。

## 2. 覆盖面枚举（前置）与 ALL GREEN 盲区自查

| 输入域分段 | 触达用例 |
|---|---|
| 正常值 | F1 普通行 / F2 多行 / F3 引号内逗号 / F4 引号内换行 / F5 `""` 转义 / F6 引号内 CRLF / F7 空引号字段 |
| 边界值 | B1 空输入 / B2 `\n` / B3 `\r\n` / B6 `\r` 单行尾文件 / B4 尾行无换行 / B5 尾行有换行 / B7 混合行尾 / B8-B9 BOM / B10 内容间空行 / B11 `,,` 空字段 / B12 尾逗号 / B13 字段空格 |
| 异常值 | E1 引号未闭合 / E2 未闭合跨行（均 ValueError） |
| 任务书点名场景 | BOM+内容、混合行尾、尾行无换行、只有换行符、字段空格、未闭合引号（均被上述用例覆盖） |
| CLI 端到端 | C1 输出形状 / C2 BOM / C3 混合行尾 / C4 未闭合 exit 1+stderr / C5 无参 usage exit 2 / C6 文件缺失 exit 1 / C7 非 ASCII UTF-8 输出 |

**ALL GREEN 盲区声明**：已覆盖任务书全部点名场景。可能未覆盖：①`"a"b` 类字段中部引号（实现为宽松字面拼接，无任务书要求，未锁定行为）；②非法 UTF-8 字节经 CLI 的报错路径已实现（exit 1）但未单测；③超大文件性能未测。认为覆盖足够：任务书清单逐项有专属用例，且变异测试证明套件对 BOM/转义/行尾/尾行四类缺陷有杀伤力。

## 3. 反例（变异）验证结果

| 变异 | 注入错误 | 套件反应 |
|---|---|---|
| M1 | 删除 BOM 跳过逻辑 | KILLED（B8/B9/C2 红） |
| M2 | 破坏 `""` 转义 | KILLED（F5 红） |
| M3 | 破坏 CRLF 合并 | KILLED（B3/B7 等 红） |
| M4 | 丢弃尾行无换行 | KILLED（B4 红） |

杀伤率 4/4；变异锚点缺失时脚本显式报 MUTATOR-BROKEN，不静默假绿。脚本：`evidence/mutate_and_check.py`。

## 4. 关键决策声明

- **字段前后空格**：按 RFC 4180 保留原样（不加引号字段空格是字段一部分），任务书要求「处理」而非「去除」，行为确定并有 B13 锁定。
- **引号未闭合**：parse() 抛 ValueError；CLI 捕获后 stderr 输出、exit 1（C4）。
- **空行/空文件**：空输入→`[]`；单独换行→`[[]]`；行尾逗号→尾空字段保留。

## 5. 简化声明（轻量配置）

跳过：完整资源盘点（标准库即可，零依赖要求排除一切外部库）、任务参照系（见门禁字段4完成标准）、2 轮循环审查（做 1 轮，审查发现 CLI 非 ASCII 输出在 Windows 管道下可能 UnicodeEncodeError，已修复并补 C7 用例回归）、宿主对齐、实操截图闭环（无 GUI；CLI 以 C1-C7 端到端 subprocess 验证替代）。质量影响评估：核心验证与三条底线未减，上列跳过项对本任务产物无实质影响。

## 6. UNVERIFIED 清单

1. 任务类型「代码类」判断未经理网络搜索佐证（harness 禁联网）——按任务书内容判断，风险低。
2. `py_compile`/验证均在 Python 3.13.14 通过；其他 Python 版本未测（代码仅用 3.0+ 基础语法，预期兼容，未验证）。

## 7. 文件清单

```
v1.2.3-draft/
├── csv_parser.py          # 交付物：parse() + CLI（usage/exit 0/1/2）
└── evidence/
    ├── verify.py           # 29 用例：F1-F7/B1-B13/E1-E2/C1-C7，--parser 可指向任意副本
    ├── mutate_and_check.py # 4 变异反例测试，杀伤率 4/4
    └── EVIDENCE.md         # 本报告
```

运行时临时物（pytest 无、临时 fixture、变异副本）均在系统临时目录并自动清理，交付目录无残留。
