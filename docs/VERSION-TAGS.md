# 版本Tag说明 / Version Tags Documentation

> 本文档说明 v1.0.0 / v1.1.0 / v1.2.0 三个版本tag的状态、脱敏情况和历史背景。

## Tag清单

| Tag | 指向Commit | VERSION文件 | 状态 | 说明 |
|-----|-----------|-------------|------|------|
| `v1.0.0` | `55af76c` | 1.1.0 | ⚠️ 参照Tag | 源代码已丢失，指向v1.1.0作为最接近的参照 |
| `v1.1.0` | `55af76c` | 1.1.0 | ✅ 正式发布 | 第一个可追溯的公开版本快照 |
| `v1.2.0` | `ffb09d5` | 1.2.0 | ✅ 正式发布 | 第二个公开大版本 |

## 脱敏说明 / Sanitization Status

三个版本的代码均已完成脱敏，不含以下私有信息：
- 私有项目名称 / Private project names
- 个人真实姓名 / Real personal names
- 本地路径（如 `<实验根目录>`、`<用户目录>`）/ Local paths
- 内部案例编号 / Internal case numbers
- 可定位的代码文件名 / Locatable code filenames

**脱敏验证记录**：
- `55af76c`（v1.1.0）：提交信息明确标注 "private project name / code filenames / case numbers / internal file names sanitized across all surfaces"；CHANGELOG记录了"私有项目名脱敏（历史档案保留、身份信息剥离）"批次
- `ffb09d5`（v1.2.0）：全量敏感信息扫描（真实姓名/用户名/本地路径/邮箱/手机号/地名/项目名）零命中
- `v1.0.0`：源代码已丢失，无法直接扫描；但其变更记录在 `INTERNAL-HISTORY.md` 中已脱敏

## v1.0.0 源代码丢失说明

### 事故经过

2026-09-09，仓库发生 **对象存储损坏事故（object-store corruption incident）**：
- `objects/` 目录丢失
- 工作树（working tree）和仓库外的备份包（out-of-repo bundle）幸存
- 零内容丢失（zero content loss）——所有代码内容都在工作树中

### 重建方式

事故后以 **单快照发布链（single-snapshot release chain）** 重建仓库，即 commit `55af76c` "release 1.1.x"。该commit包含了截至当时的全部累积状态，但**丢失了1.0.0及更早版本的独立commit历史**。

### v1.0.0的变更内容（来自INTERNAL-HISTORY.md）

v1.0.0（2026-08-07）的变更记录完整保存在 `INTERNAL-HISTORY.md` 第643-655行：

```
## 1.0.0 - 2026-08-07

- Initial public release.
- Added three internal role faces: planning, execution, and review.
- Role faces are thinking modes, not identity replacement or external personas.
- Before closing any stage, the model must switch to the review face and verify
  actual output through research, divergence, convergence, and evidence.
```

中文：
```
- 正式公开发布。
- 新增三个内部角色面：规划面、执行面、审查面。
- 角色面是思考模式，不是身份替换，也不是外部人格。
- 关闭任意阶段前，模型必须切换到审查面，并通过调研、发散、收敛和证据核验实际产出。
```

### v1.0.0 → v1.1.0 的主要差异

v1.1.0（2026-08-08）相比v1.0.0新增了：
1. **三种执行模式**：单Agent模式、子Agent模式、指挥官多Agent模式
2. **真实环境验收**：Web必须打开、应用必须启动、CLI必须运行等
3. **指挥官模式**：通用总指挥模式，不要求子Agent工具
4. **身份文件体系**：内置身份 + 用户自定义身份
5. **信任层级**：T1调研/T2产物/T3命令

完整差异见 `INTERNAL-HISTORY.md` 第613-641行。

## 版本演进时间线

### 内部迭代（预发布，已归档在INTERNAL-HISTORY.md）

| 版本 | 日期 | 关键事件 |
|------|------|---------|
| 0.0.1.0 | 2026-08-06 | 初始"指挥官"工作流，从GPT-5.6 Sol对话中蒸馏而来 |
| 0.1.1.0-internal | 2026-08-06 | 移除项目特定内容，平台中立化 |
| 0.1.2.x ~ 0.1.10.0 | 2026-08-08 | 多Agent协作规则、身份库、信任层级 |
| 0.2.0.0 ~ 0.2.9.1 | 2026-09-04~08 | 变更管理、指挥权接管、规则蒸馏 |
| **0.3.0.0** | 2026-09-08 | **改名**：`gpt-5-6-sol-multi-agent-style` → `gpt-series-reasoning-style` |
| 0.3.0.1 ~ 0.3.2.2 | 2026-09-08 | 最后内部迭代 |

### 公开版本（git历史）

| 版本 | 日期 | Commit | 说明 |
|------|------|--------|------|
| **1.0.0** | 2026-08-07 | （已丢失） | 正式公开发布，三个内部角色面 |
| **1.1.0** | 2026-08-08 | `55af76c` | 三种执行模式，仓库重建后的最早快照 |
| 1.1.x Unreleased | 2026-08~09 | 多个commit | 规则增强、工具链、六轮全仓审查修复、A/B基线实测 |
| **1.2.0** | 2026-09-12 | `ffb09d5` | README重构、版本表面对齐、社交预览图翻新 |
| 1.2.1 | 2026-09-13 | `a95001a` | 中间增量版本（不打tag） |
| 1.2.2 | 2026-09-13 | `b016a39` | A2+第五增强点（覆盖面枚举强制前置） |

## 项目原名说明

项目原名为 **`gpt-5-6-sol-multi-agent-style`**（GPT-5.6 Sol Multi-Agent Style），源自对GPT-5.6 Sol推理风格的蒸馏。

2026-09-08（内部版本3.0.0）改名为 **`gpt-series-reasoning-style`**（GPT系列推理风格），原因：
> 旧名锁死具体型号；系列名可穿越型号更替。

改名记录见 `INTERNAL-HISTORY.md` 第70-90行。

## 相关文件

- `INTERNAL-HISTORY.md`：完整内部迭代历史（0.0.1.x ~ 0.3.3.x）
- `CHANGELOG.md`：公开版本变更记录（1.1.0 ~ 1.2.2）
- `VERSION`：当前版本号
