<div align="center">

# GPT-Series Reasoning Style

**把"Agent 说做完了"变成"Agent 证明做完了"。**
**Turn "the agent says it's done" into "the agent proves it's done".**

一个面向 AI Agent 的**交付验收纪律层**（delivery discipline layer）——
执行面彻底放手，审查面把住口，防假完成、防自欺。

[![Version](https://img.shields.io/badge/version-1.4.49-blue)](#versioning--版本)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](#license--许可证)
[![Platforms](https://img.shields.io/badge/platforms-1_supported-blueviolet)](#install--安装)
[![Size](https://img.shields.io/badge/size-~5KB-orange)](#cost--成本)

</div>

> **Process-discipline layer only** — not a reasoning-capability booster and not GPT-specific —
> the name records its origin (distilled from a long series of GPT-series model dialogues).
>
> 本 skill 是**纯交付验收纪律层**：不提升模型推理能力，也不绑定 GPT 系列——名字记录的是它的来源
> （从一系列 GPT 系列大模型的真实对话中打磨提炼）。中文主导。

---

## Quick Start / 快速开始

```bash
# 1. 安装
git clone https://github.com/JadeYingWah/gpt-series-reasoning-style
cd gpt-series-reasoning-style

# 2. 在对话里按名调用
#    使用 gpt-series-reasoning-style 执行本次任务。
```

加载后，AI 在执行任务时会：
- 执行面**彻底忘记**这套纪律，不打断创作流
- 觉得"做完了"时，回来用两道检查（直觉 + 纪律）验收
- 声称完成时必须附上可核对的证据

---

## 目录 / Table of Contents

- [Why / 为什么需要它](#why--为什么需要它)
- [How It Works / 工作原理](#how-it-works--工作原理)
- [Rules / 七条规则](#rules--七条规则)
- [Field Tests & Evidence / 实测与证据](#field-tests--evidence--实测与证据)
- [Cost / 成本](#cost--成本)
- [When To Use / 何时使用](#when-to-use--何时使用)
- [Install / 安装](#install--安装)
- [Versioning / 版本](#versioning--版本)
- [License / 许可证](#license--许可证)

---

## Why / 为什么需要它

AI 协作里最贵的一类失败，不是"模型不够聪明"：

**声称未验证的完成**——"已经修好了 / 测试都过了"，而磁盘上没有可核对的证据，甚至根本没跑过。

一次"假完成"的返工成本（澄清 + AI 重读上下文 + 重做）通常在 2 万–10 万 token。
本 skill 的常驻成本约 1.5k token——**它把防假完成做成第一优先级，正是因为那是 token 账上最贵的一项。**

它带来的改变，一眼可见：

```text
【没有纪律】                    【有本 skill】
用户：帮我做个动画              用户：帮我做个动画
AI  ：好的，写完了。            AI  ：写完了。附验收清单：
      （没真打开看过）              - 真开浏览器渲染截图 ✓
                                   - 抓到 3 个视觉 bug，已修复 ✓
                                   - 未验证：其他浏览器兼容性 ⚠
```

---

## How It Works / 工作原理

### 三道工序

```
规划面（任务开始前）
    ↓
执行面（彻底忘记 skill，专心干活）
    ↓
审查面1（直觉检查——继续忘记 skill，用常识判断）
    ↓
审查面2（纪律检查——重新想起 skill，严格过一遍规则）
```

**执行面彻底忘记 skill**——这是核心设计。
创作是创作，检查是检查，互不干扰。
做完了再回来检查，不打断心流。

### 两道审查

| 审查 | 靠什么 | 抓什么 |
|---|---|---|
| 审查面1 | 直觉 / 常识 | 规则没覆盖到的问题 |
| 审查面2 | 纪律 / 规则 | 规则覆盖到的问题有没有做到 |

---

## Rules / 七条规则

审查面2 严格过这 7 条：

1. **真打开看一眼** —— 产物在真实环境打开、真用一遍，不许只看代码或心算就宣布完成
2. **未验证标注** —— 没验过的结论直接标「未验证」，写明哪步没法验
3. **失败两次换路** —— 同一动作连续失败第2次，禁止同法第3次，别死磕
4. **全绿不算证据** —— 测试全过只证明跑过的没错，故意做一次要防的错误才算验过
5. **关键数字重算** —— 数据类交付的关键数字，用独立方法重算或双源交叉验证
6. **临时物隔离** —— 临时文件不进交付目录、收尾清掉
7. **防死循环** —— 同一动作连续做3次输出相同就换思路

**按风险分级**：轻任务只做前3条；数据/代码/多Agent类重任务做全7条。

---

## Field Tests & Evidence / 实测与证据

### 四个 Test-Bed 的实验结论

| 测试场 | 任务数 | 结论 |
|---|---|---|
| Test-Bed 1 | 6个轻任务 | 轻任务上价值小，但没副作用 |
| Test-Bed 2 | 5个中等任务 | 执行者一致评分 7.5-8分，不提升代码质量，提升交付可信度 |
| Test-Bed 3 | 1个创意任务 | 真打开看一眼抓到5处视觉问题，结构校验抓不到 |
| Test-Bed 4 | 1个复杂创意任务 | 这套纪律学会了就忘不掉，知道了就会自觉用 |

### 核心结论

> **这个 skill 的价值不是"强制你做什么"，而是"让你知道该做什么，然后你自己就会做"。**

一旦知道了：
- 要真打开看一眼
- 要列未验证项
- 要做独立验证

你就再也回不去"我觉得行就交"了。

**不是纪律，是习惯。**

---

## Cost / 成本

| 项目 | 数值 |
|---|---|
| SKILL.md 大小 | ~5KB / 50行 |
| 常驻 token 成本 | ~1.5k |
| 按需加载 | references/ 只有命中才读 |

**对比 v1.2.5 重版本**：38.7KB / 179行 / ~12k token——已被实验证明是错的（规则越多效果越差）。

---

## When To Use / 何时使用

**推荐用：**
- 代码交付
- 数据报告
- 视觉产物
- 多 Agent 协作
- 任何"声称完成就要对产物负责"的场景

**不用：**
- 一句话问答
- 探索性草稿
- 纯聊天
- 无人验收的内部实验

---

## Install / 安装

```bash
git clone https://github.com/JadeYingWah/gpt-series-reasoning-style
```

把 `SKILL.md` 放到你的 skill 加载目录即可。

---

## Versioning / 版本

当前版本：**1.4.49**

版本历史：
- v1.4.x：极简版，50行，三道工序设计
- v1.2.x：重版本，179行，3043个文件——已被实验证明是错的

---

## License / 许可证

MIT
