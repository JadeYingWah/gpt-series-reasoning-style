<div align="center">

# GPT-Series Reasoning Style

**把"AI说做完了"变成"AI证明做完了"。**

<img src="assets/social-preview.svg" alt="GPT-Series Reasoning Style · 交付纪律层" width="100%">

![Version](https://img.shields.io/badge/version-1.6.0-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![CI](https://github.com/JadeYingWah/gpt-series-reasoning-style/actions/workflows/ci.yml/badge.svg)

</div>

## 三个卖点

|  |  |
|---|---|
| 🎯 **专治假完成** | AI没跑测试就说"全过了"？没打开页面就说"没问题"？这个skill逼它真的打开、真的跑一遍，没验过的地方主动标出来。 |
| 🧊 **执行期零干扰** | 规则只在规划和验收时加载，写代码/做设计/写文章时完全不存在——心流不被打断，不用付"纪律常驻"的代价。 |
| 🤝 **跟其他skill不打架** | 只管"怎么算做完"，不管"怎么做对"。前端设计、图像生成、表格处理……其他该装的skill照装，各管各的。 |

## 它治的是什么病

AI交付最贵的失败从来不是"不会做"，而是**没验过就说做完了**：

- 测试没真跑，宣布"全部通过"
- HTML没在浏览器里打开过，宣布"页面没问题"
- 关键数字没重算，照抄第一遍的结果
- 说明写了功能A，产物里根本没有A

这个skill只干一件事：**把"我觉得行"变成"验过了，证据在这儿"。**

## 装上之后交付长什么样

**没装的时候：**
> 做完了。功能都实现了，测试也全过了。

**装上之后：**
> **做了什么**：重写导出功能，新增3个边界用例。
> **怎么验的**：浏览器实测渲染（截图见附件）；pytest tests/test_export.py -q → 12 passed。
> **哪些没验**：① Safari兼容性——本机无Safari，建议你打开自验；② 十万行以上大数据量性能——没有现成数据集。

差别不在格式好看——是你**一眼就知道哪些话能信、哪些还得自己再验**。

## 它怎么工作

五个阶段，规则只在两头出现，中间完全放开：

| 阶段 | 做什么 | 规则在场吗 |
|------|--------|-----------|
| 1 构想 | 想清楚要做什么 | ❌ 不在 |
| 2 规划 | 对齐方向、定范围 | ✅ 读规则 |
| 3 执行 | 专心干活 | ❌ 不在 |
| 4 直觉检查 | 凭感觉快速扫一遍 | ❌ 不在 |
| 5 验收 | 严格逐条过 | ✅ 读规则 |

**核心逻辑**：创作时没纪律打扰，验收时一条不缺。

## 安装

### 方式一：放进skills目录（推荐）

**Claude Code / WorkBuddy / Cursor 等：**

`ash
git clone https://github.com/JadeYingWah/gpt-series-reasoning-style
cp -r gpt-series-reasoning-style ~/.claude/skills/
# WorkBuddy改成 ~/.workbuddy/skills/，Cursor改成 ~/.cursor/skills/
`

**Windows PowerShell：**

`powershell
git clone https://github.com/JadeYingWah/gpt-series-reasoning-style
Copy-Item -Recurse -Force gpt-series-reasoning-style "C:\Users\yutia\.claude\skills\"
`

### 方式二：AGENTS.md（不支持skill自动发现的客户端）

`ash
git clone https://github.com/JadeYingWah/gpt-series-reasoning-style
cd gpt-series-reasoning-style
`

装完新开一个会话就生效。一句话问答、小改不用管它，它自己会判断要不要上。

## 详细文档

完整说明书（适用场景、八条纪律、多智能体协作、实测证据、成本）见 [REFERENCE.md](REFERENCE.md)。

---

**MIT License** · v1.6.0