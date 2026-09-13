# ab-metacognition — 元认知能力与skill效果关系实验（2026-09-13）

## 目录结构

```
ab-metacognition/
├── README.md                          # 本文件
├── CAPABILITY-EFFECT-MAPPING.md       # 8维度能力-效果映射分析（核心结论）
├── v1.2.3-REVISION-DRAFT.md           # v1.2.3修订草案（6项，3高+3中）
├── V123-VERDICT-REPORT.md             # v1.2.3验证实验终报（暂缓实施）
├── HANDOFF-v1.2.3-EXPERIMENT.md       # v1.2.3实验交接文档
├── EXPERIMENT-REPORT.md               # 元认知能力E1实验报告
├── metacognition-self-assessment.md   # 元认知自评估条款草案
├── TASK.md                            # v1.2.3实验任务书（CSV解析器）
├── E1/                                # E1实验：weak-skill组三条件对比
├── E2/ E3/ E4/                        # 空目录（计划未执行）
├── P1-1/                              # P1实验设计（原则引导vs硬指标）
├── capability-tests/                  # T1/T2/T3能力对照实验
│   ├── T1/                            # 指令遵循测试（第一版，太简单）
│   ├── T1-redesign/                   # T1重设计（待办Web应用，别问直接做）
│   └── ...
├── skill-snapshots/                   # skill版本快照
│   ├── v1.2.2-full/                   # v1.2.2完整快照
│   └── v1.2.3-draft/                  # v1.2.3-draft快照（已应用3项高优修订）
└── v1.2.3-test/                       # v1.2.3验证实验产物
    ├── v1.2.2/                        # 对照组（96/96测试，6/6变异捕获）
    ├── v1.2.2-rerun/                  # 重跑组（同执行者，验证执行者方差）
    └── v1.2.3-draft/                  # 实验组（34.5分，反最低）
```

## 核心结论

1. **能力-效果映射**：批判性自我怀疑/指令遵循弥补最强(⭐5)，自我校准最弱(⭐3)
2. **v1.2.3暂缓实施**：硬指标化在强模型上边际效益为负，draft反最低分
3. **执行者方差铁律**：同v1.2.2两执行者差7.5分 > 版本差，实验必须同执行者双组重跑
4. **可复算性范式**：以reference形式吸收（非硬指标），4模式+4常见错误
5. **无skill对照缺失**：v1.2.3实验缺无skill基线，已交给另一个AI补测

## 已归档到仓库

- `docs/field-tests/ab-v123-revision-validation/`（commit 58e0e2a）
- `references/verification-reproducibility-patterns.md`（commit e691313）
- v1.2.3-draft快照：`...-workspace/proposals/v1.2.3-draft-snapshot/`

## 待push提交

1. `b016a39` — v1.2.2发布
2. `e691313` — 可复算性范式+CHANGELOG
3. `58e0e2a` — v1.2.3实验归档
