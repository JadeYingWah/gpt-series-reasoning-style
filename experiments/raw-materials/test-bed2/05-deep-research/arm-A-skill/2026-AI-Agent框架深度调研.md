# 2026 年 AI Agent 框架深度调研

**对比对象**：LangChain（+LangGraph）、CrewAI、AutoGen（→ Microsoft Agent Framework）、LlamaIndex，及新势力（OpenAI Agents SDK、Google ADK 等）

**数据截止**：2026-09-16 ｜ **覆盖维度**：架构设计、性能基准、社区活跃度、企业采用、优缺点、选型建议

---

## 0. 核心结论（TL;DR）

| 结论 | 一句话 |
|---|---|
| **格局定局** | 四家已分化为四种"生态位"，不再是谁取代谁：LangGraph=有状态编排运行时、CrewAI=企业自动化平台、Microsoft Agent Framework=微软系企业 SDK、LlamaIndex=文档/数据智能平台 |
| **最大变量** | Microsoft Agent Framework 2026-04 GA（合并 AutoGen + Semantic Kernel），.NET 企业市场被撬开；AutoGen 原仓库实质冻结（最后提交 2026-04-15） |
| **范式趋同** | 所有框架都收敛到"图/工作流 + Agent 抽象 + MCP/A2A 协议 + 企业控制面"同一张蓝图，差异化只剩生态位与工程成熟度 |
| **选型铁律** | 框架级"准确率"没有官方基准可循——基准测的是模型不是框架；框架差异体现在**成本、延迟、可观测、状态可靠性**。选型必须用自己的评估集 |
| **企业真相** | "生产环境"调查数字从 14% 到 51% 不等——口径之争比数字本身更重要；88% 试点未毕业，失败原因几乎全是组织性的（数据就绪、治理、评估），不是模型能力 |

**30 秒选型**：有状态长任务/HITL/审计 → **LangGraph**；角色分工明确的业务自动化、业务团队要参与、要开箱治理 → **CrewAI**；.NET/Azure 存量企业 → **MAF**；文档密集型智能 RAG → **LlamaIndex**；单一 OpenAI 生态轻量起步 → **OpenAI Agents SDK**；Gemini 生态 → **Google ADK**。

---

## 1. 调研方法与可信度声明

**采集方式**：
- **一手数据**：GitHub REST API 实时采集 8 个仓库的 stars/forks/issues/最后提交时间/最新 release（采集日 2026-09-16，附录 A 有完整记录）。
- **官方来源**：各厂商官网、官方 changelog/博客（版本号、产品命名、GA 日期）。
- **第三方转引**：行业调查（Gartner、McKinsey、Mayfield 等）与社区实测，均标注来源；**未经本人复现的一律不定论**。

**关键交叉验证**（防止单源幻觉）：
| 指标 | 早期第三方读数 | 本次一手采集 | 一致性 |
|---|---|---|---|
| CrewAI stars | 51,558（2026-05-17，投资方引 GitHub API）[S18] | 58,633（2026-09-16）[S3] | 4 个月 +13.7%，增速合理 ✅ |
| LlamaIndex stars | ~50,200（2026 年中）[S24] | 52,174 [S4] | ✅ |
| LangGraph stars | ~35,000（较早日）[S13] | 41,730 [S2] | ✅ |

**未验证项（显式声明，不许装全验过）**：
1. **框架级性能数字**（第 4 节表格）——第三方单源自测，方法学不透明，未能复现；其中一篇文中框架版本号疑似旧版，数字可信度打折。**只能当量级参考，不能当决策依据**。
2. **厂商自报运营数据**——CrewAI"65% Fortune 500""4.5 亿月工作流""10 万+认证开发者"，LlamaIndex"5 亿+文档""30 万+ LlamaCloud 用户"，均为厂商口径，无法独立核验。
3. **行业调查数字**（Gartner/McKinsey/S&P 等）——均为二手转引，未获取原始报告全文。
4. **LlamaIndex 融资金额**——仅确认 Databricks/KPMG 投资 [S24]，金额/估值无一手来源。
5. **AG2 社区分叉现状**——确认其存在（AutoGen v0.2 血统的社区延续 [S17]），未做一手核验。
6. **microsoft/autogen 的 license 读数**——GitHub API 返回 CC-BY-4.0 [S5]，与该仓库历史 MIT 认知不一致，未深查原因，以 API 读数记录。
7. **Berkeley"全部主流 agent 基准可被 reward-hack 至 ~100%"、OpenAI 停报 SWE-bench**——单源转引 [S28]。
8. **LangChain 各子包精确版本**——monorepo 多包、发布节奏极快（core 9 月 11 日还是 1.6.3），以 PyPI 实时为准。

---

## 2. 2026 年格局总览

### 2.1 一张表看清四家 + 新势力

| 框架 | 维护方 | 2026 定位 | 最新版本（release 日） | 语言 | 许可证 |
|---|---|---|---|---|---|
| **LangChain + LangGraph** | LangChain Inc. | 组件库 + 有状态图运行时（agent 工程平台） | langchain-core 1.6.3（09-11）[S1]；langgraph 1.2.x（08 口径）[S9][S14] | Python/TS | MIT |
| **CrewAI** | CrewAI Inc. | 角色式多智能体 + 企业控制面（AMP） | 1.15.21（09-09）[S3] | Python | MIT |
| **AutoGen（原仓库）** | Microsoft | **已冻结**——被 MAF 取代 | 最后 push 2026-04-15 [S5] | Python | API 读数 CC-BY-4.0* |
| **Microsoft Agent Framework** | Microsoft | SK 企业底座 + AutoGen 多智能体编排的统一 SDK | dotnet-1.21.0（09-11）[S6] | .NET/Python | MIT |
| **LlamaIndex** | LlamaIndex Inc. | 文档处理/数据智能平台（LlamaParse + LlamaCloud） | llama-index-core 0.14.24（08-19）[S4] | Python/TS | MIT |
| OpenAI Agents SDK | OpenAI | 轻量多智能体 harness（Responses API 原生） | 活跃（09-16 有提交）[S7] | Python(+JS) | MIT |
| Google ADK | Google | Gemini 生态 code-first Agent 工具包 | 活跃（09-15 有提交）[S8] | Python/Java/Go | Apache-2.0 |

\* 以 GitHub API 读数记录，未深查（见第 1 节未验证项 6）。

### 2.2 三层市场结构（2026 年的关键理解框架）

开源框架本身已经不构成商业模式，2026 年的竞争发生在三层：

1. **框架层（免费获客）**：LangChain/LangGraph、CrewAI OSS、MAF、LlamaIndex OSS——全部 MIT，功能高度趋同（图编排、MCP/A2A、HITL、记忆）。
2. **控制面层（收钱的地方）**：LangSmith（含 Deployment，LangGraph Platform 已并入）[S13]、CrewAI AMP（Cloud/Factory 自托管）[S11]、Microsoft Foundry Agent Service [S10]、LlamaCloud [S12]。共性卖点：可观测、RBAC/审计、HITL 审批门、部署托管。
3. **协议层（互操作底座）**：MCP（公开 server 已超 9,400 个 [S35]）与 A2A 已成为四家全部的"标配原生支持" [S10][S17][S21][S24]；AG-UI、ACP 等新协议在涌现（LlamaIndex 已支持 AG-UI/ACP [S4][S24]）。

**含义**：选框架本质是选"你愿意住进谁的控制面 + 生态"，而不是比谁的 Agent 类写得优雅。

---

## 3. 架构设计对比

### 3.1 四家核心抽象

**LangChain + LangGraph（图运行时派）**
- 分工在 1.0（2025-10-22 双双 GA [S13][S14]）后彻底定形：**LangChain 是组件/集成层**（模型、工具、检索、700+ 集成的口径 [S14]），**LangGraph 是执行运行时**（StateGraph 状态图，灵感来自 Pregel/Beam）。
- 杀手锏是**持久化执行（durable execution）**：执行状态自动 checkpoint，进程崩了、等人工审批三天、供应商瞬断重试，都能从断点恢复 [S14]。"一次 agent 运行应当活得过服务器重启"是它的产品哲学。
- HITL 是一等公民：`interrupt()` 暂停即持久中断，恢复零成本 [S14]。
- 旧 AgentExecutor 已弃用、维护至 2026-12，新代码走 `create_agent()`（LangGraph 之上的预置 ReAct）或自建 StateGraph [S14]。
- 中间件体系成熟：HITL 检查点、对话摘要、PII 脱敏、模型重试、内容审核（1.1 起）[S9]；deepagents（类 coding-agent 的深度代理，2026-04 v0.5 支持异步子代理）[S9]。

**CrewAI（角色协作派）**
- 双编程模型：**Crews**（role/goal/backstory 的角色自主协作）+ **Flows**（事件驱动、确定性工作流，2026-01 起生产就绪，支持流式工具调用与 HITL 反馈 [S17]）。官方口径是"两者可组合，自治与精确各取所需"。
- 2026 年的关键补课：内存/知识/RAG 后端全面可插拔（Qdrant Edge、层级记忆隔离，2026-06 起）[S17]，原生 MCP + A2A [S17]，OpenAI 兼容 provider 全家桶（OpenRouter/DeepSeek/Ollama/vLLM/Cerebras/DashScope）[S17]。
- AMP 控制面直接坐在执行路径上：每次 LLM/工具/内存读取实时追踪 + 成本核算，RBAC、不可变审计、运行时 hook 注入 PII 脱敏与策略检查 [S11]。

**Microsoft Agent Framework（企业底座派）**
- 来源：AutoGen（多智能体编排）+ Semantic Kernel（企业级插件/连接器/遥测）合并，2025-10-01 公开预览，**2026-04 GA**（官方博客记 4 月 2 日 [S10]，多数媒体记 4 月 3 日 [S20][S21]）。SK 是底座层，AutoGen 的群聊/移交/Magentic-One 模式重实现为图工作流 [S21]。
- 五层架构：Connectors（Azure OpenAI/OpenAI/Claude/Bedrock/Gemini/Ollama 一行切换）→ Kernel（DI/插件）→ Agent → 编排（图工作流）→ 互操作（MCP 全量 + A2A 1.0）[S21]。
- BUILD 2026 加码 **Agent Harness**（上下文自动压缩、文件记忆、Todo、plan/execute 双模式、技能发现、后台子代理、内置 web search/shell）与 **Foundry Hosted Agents**（缩容到零、会话级 VM 隔离、状态保持的断点恢复）与 **CodeAct**（把多轮工具调用折叠为一段沙箱代码，降低编排开销）[S10]。
- 独家卖点：**.NET 一等公民**（LangGraph/CrewAI 均无），金融/保险/医疗/制造等 .NET 存量企业因此第一次有了"不分裂团队"的选择 [S20]。

**LlamaIndex（数据智能派）**
- 定位已明示在仓库描述里："**the document processing platform for AI**" [S4]——重心从"通用 agent 框架"转向文档智能：LlamaParse（90+ 文件类型的版面感知解析，含手写）+ LlamaExtract（schema 化抽取）+ Index（托管索引）[S12]。
- **Workflows**：事件驱动、async-first 的工作流引擎（可启动/暂停/恢复、有状态）[S12]；部署侧 llama-deploy 已弃用，拆为 llama-index-workflows + llama-agents-server/client + llamactl，LlamaCloud 部署仍是 beta [S25]。
- 差异化武器是**评估即公共品**：ParseBench（2026-04，首个文档解析基准，Kaggle/HF 公开榜单）[S24]——用基准绑定"解析质量"心智。
- 创始人 Jerry Liu 的叙事：scaffolding 时代结束，**护城河移向 context engineering** [S24]。

### 3.2 架构对比矩阵

| 维度 | LangGraph | CrewAI | MAF | LlamaIndex |
|---|---|---|---|---|
| 控制流范式 | 显式图（节点/边/共享状态） | Crews 自治对话 + Flows 事件驱动 | 图工作流（SK 底座） | 事件驱动 Workflows |
| 状态持久化 | **自动 checkpoint（最强项）** | 2026 年补齐（checkpoint 遥测见 1.15.21 [S3]） | Foundry 托管会话状态 + 断点恢复 [S10] | Workflows 有状态，托管部署 beta [S25] |
| HITL | interrupt() 原生 [S14] | Flows HITL 反馈 [S17] | ToolApproval/审批流内置 [S10] | 框架内支持 [S12] |
| 多智能体模式 | supervisor/swarm/分层（自建图） | 角色分工 + 分层委托（开箱） | 群聊/移交/Magentic-One/图编排 [S21] | 多智能体可用但非主战场 |
| 互操作协议 | MCP（生态最广） | MCP + A2A 原生 [S17] | MCP 全量 + A2A 1.0 [S21] | MCP + ACP + AG-UI [S4][S24] |
| 语言 | Python/TS | Python | **.NET + Python** | Python/TS |
| 控制面/托管 | LangSmith Deployment [S13] | AMP Cloud/Factory [S11] | Foundry Agent Service [S10] | LlamaCloud（部署 beta）[S25] |
| 生态广度 | 700+ 集成（口径 [S14]） | 预置企业连接器（Gmail/Salesforce/Teams 等）[S11] | 六大 provider + Azure 全家桶 [S21] | LlamaHub 连接器（160+ 数据源口径 [S26]；300+ 集成包口径 [S24]） |

### 3.3 范式趋同：2026 年最重要的架构事实

四家在 2024-2026 年间**独立收敛到了同一张蓝图**：显式工作流（确定性）+ Agent 循环（自治）双模式、协议化互操作（MCP/A2A）、企业控制面（观测/治理/审批）。Google ADK 也在 2026 年独立收敛到图抽象 [S14]。剩下的真实差异只有三个：
1. **持久化执行的成熟度**（LangGraph 最深，MAF 靠 Foundry 追，CrewAI/LlamaIndex 在补）；
2. **语言与生态卡位**（.NET 唯一 MAF、文档唯一 LlamaIndex、集成广度唯一 LangChain）；
3. **控制面的企业合规深度**（AMP 的执行路径内控制、Foundry 的会话隔离各有侧重）。

---

## 4. 性能与基准

### 4.1 先说结论：框架级性能没有可信的官方基准

- 主流 agent 基准（SWE-bench Verified、GAIA、τ-bench、AgentBench、WebArena）**测的是模型 + 脚手架的组合，不是框架**。2026-04 快照的头部分数（均为转引 [S28]）：SWE-bench Verified 榜首 87.6%（Claude Opus 4.7）、GAIA（HAL）榜首 74.6%、WebArena 榜首 68.7%（人类基线约 78%）。
- 基准可信度本身在崩塌：转引称 2026-04-12 UC Berkeley 研究显示八大 agent 基准均可被 reward-hack 到 ~100%，OpenAI 因评测集泄漏停报 SWE-bench Verified [S28]——**任何单一基准分数都不该再作为选型依据**。
- 框架差异真实存在，但体现在**编排税**：token 成本、延迟、多轮可靠性、故障恢复——这些恰恰是公开基准不测的。

### 4.2 第三方实测数据（单源，仅供量级参考 ⚠️）

**实测 A**（转引自中文社区自述方法学：同一后端模型、同一组工具、GAIA 中 100 道 2-4 步工具调用子集 [S30]）⚠️ 未复现，文中版本号疑旧：

| 指标 | LangGraph | CrewAI | AutoGen |
|---|---|---|---|
| 任务成功率 | 91% | 85% | 87% |
| 平均 LLM 调用次数 | 3.2 | 4.7 | 3.8 |
| 平均端到端延迟 | 14.6s | 21.3s | 17.9s |
| 平均 token 消耗 | 5,400 | 8,200 | 6,300 |
| 每任务成本 | $0.024 | $0.037 | $0.028 |

**结构性解释**（这个比数字更可信，多方一致 [S17][S28][S30]）：CrewAI 把 role+backstory+goal 拼进每次调用的 system prompt，角色化提示天然更贵；图框架可以在节点级只塞必要状态。**但**：多智能体协商类任务（如"3 个代理协作写报告"）中 CrewAI/AutoGen 的开箱成功率会反超 LangGraph——后者要你显式编码"协商"逻辑，写不好还不如不用 [S30]。

**实测 B/C**（转引，方法学更弱，仅记录）：LangGraph 编排开销 ~120ms/节点 vs CrewAI ~450ms/任务交接 [S31]；"LangGraph 赢延迟与成本、CrewAI 赢上线速度、AutoGen 开放推理强但成本 5-6 倍" [S28]。

### 4.3 被普遍忽略的关键指标：N-run 可靠性

单次 90% 准确率的 agent，重复 5-10 次同任务可能只有 ~60% 的全对率（温度>0 下的随机性）[S28]。**生产选型时应要求供应商/自己评测给出 N-run 成功率与 p95 延迟，而不是单次准确率**。这也是"框架选型要用自己的评估集"的根本原因。

### 4.4 各家公开的"性能叙事"

- **LangChain**：不发布框架级基准，靠 LangSmith 评估产品承接"你自己测"的需求；官方叙事锚在持久化执行与客户采用（Uber/LinkedIn/Klarna）[S13]。
- **CrewAI**：以运营规模叙事代替基准（4.5 亿月工作流 [S11]）；评估能力集成 Arize/Galileo/DataDog/Patronus [S11]——同样是"你自己测"。
- **MAF**：CodeAct 叙事——把多轮工具调用折叠为单段沙箱代码，直接降低模型轮次/延迟/token [S10]，是四家中唯一给出明确"性能优化机制"的。
- **LlamaIndex**：**唯一自建公开基准的**（ParseBench 文档解析榜单 [S24]）——因为解析质量是其商业核心，可测、想测。

---

## 5. 社区活跃度（GitHub API 一手采集，2026-09-16）

### 5.1 核心指标

| 仓库 | Stars | Forks | Open Issues | 建库 | 最后 push | 活跃判定 |
|---|---|---|---|---|---|---|
| langchain-ai/langchain | 146,422 | 24,478 | 515 | 2022-10 | **2026-09-16** | ✅ 高频 |
| langchain-ai/langgraph | 41,730 | 7,054 | 790 | 2023-08 | 2026-09-15 | ✅ 高频 |
| microsoft/autogen | 61,004 | 9,218 | 1,071 | 2023-08 | **2026-04-15（停滞 5 个月）** | ⚠️ 冻结 |
| crewAIInc/crewAI | 58,633 | 8,471 | 808 | 2023-10 | **2026-09-16** | ✅ 高频 |
| run-llama/llama_index | 52,174 | 8,147 | 773 | 2022-11 | 2026-09-15 | ✅ 高频 |
| microsoft/agent-framework | 13,531 | 2,322 | 606 | 2025-04 | 2026-09-15 | ✅ 高频（1 年半到 13.5k★） |
| openai/openai-agents-python | 29,474 | 4,745 | 78 | 2025-03 | 2026-09-16 | ✅ 高频（issue 积压极小） |
| google/adk-python | 21,544 | 4,010 | 493 | 2025-04 | 2026-09-15 | ✅ 高频 |

### 5.2 读法与陷阱

1. **Star ≠ 活力**：microsoft/autogen 星数仍是全场第二（61k），但最后提交停在 2026-04-15——MAF GA 后实质冻结，投资流向 MAF [S5][S20]。选型看提交频率与 release 节奏，别看星数。
2. **发布节奏（最新 release，一手）**：CrewAI 1.15.21（09-09）、MAF dotnet-1.21.0（09-11）、langchain-core 1.6.3（09-11）均为"周级"节奏；llama-index-core 0.14.24（08-19）为"月级"。CrewAI 从 4 月底 1.14.4 [S18] 到 9 月 1.15.21，月均 1-2 个 minor。
3. **成熟度信号分化**：LlamaIndex 主包仍处 0.x（0.14.x）[S4]，其余三家均已在 1.x 稳定线；LangGraph 自 1.0（2025-10）承诺"无破坏性变更直到 2.0" [S13]。对生产团队，0.x 意味着 API 迁移风险仍存。
4. **新势力速度**：OpenAI Agents SDK 18 个月 29.5k★、Google ADK 17 个月 21.5k★——大厂背书的"轻量路线"分流明显。

---

## 6. 企业采用情况

### 6.1 宏盘：2026 年企业 agent 渗透率——先看口径战争

同一年的调查给出 14%~51% 的"生产部署率"，差异全在定义 [S32][S33][S34][S36]：

| 数字 | 来源 | "生产"的定义 |
|---|---|---|
| **51%** + 23% scaling | Ringly.io 口径 [S33][S34] | 有 agent 触碰生产流量即算 |
| **42%**（+72% 生产+试点） | Mayfield CXO 调查（266 名 F2000 高管）[S32] | 未披露细分定义 |
| **31%** | S&P Global / McKinsey [S33] | ≥1 个 agent 在生产 |
| **<15%（14%）** | 2026-03 对 650 名企业技术负责人调查 [S36] | **严格口径**：承担目标任务量 50%+ + 自动化质量监控 + 事故响应机制 |

**共识的硬数据**：Gartner Q1 2026——**80% 的新发/更新企业应用内嵌至少一个 agent**（2024 年为 33%）[S35]；Gartner 预测 2026 年底 40% 企业应用嵌入任务型 agent [S33]。试点真实存在但难毕业：88% 试点未进生产（Forrester/Anaconda 口径 [S35]）。
**ROI 口径**：部署中位回本 5.1 个月（SDR 3.4 / 客服 4.1 / 财务运营 8.9）[S33]；知识工作者人均每周省 6.4 小时（McKinsey/Slack 口径 [S33]）。
**失败原因全是组织性的** [S36]：遗留系统集成（46%）、规模化后质量不稳、缺监控工具、权属不清、评估缺口（64% 的领导者承认）——**没有一条是"模型不够聪明"**。有用治理工具的企业上产率高出 12 倍、用结构化评估的高 6 倍（Databricks 20,000+ 组织口径 [S36]）。
**市场**：2026 年 agent 市场 $10.9-12.06B（同比 +43%）[S33]；IDC/McKinsey 收敛于 2027 年企业 agent 支出 ~$1.4T [S35]。架构上 supervisor 模型占 37% 成为多智能体主流 [S36]。

### 6.2 框架级证据

**LangChain/LangGraph**——标杆客户 + 资本背书：
- 1.0 公告点名 **Uber、LinkedIn、Klarna** 已规模化采用 LangGraph [S13]；
- 2025-10 $125M B 轮（IVP 领投），估值 $1.25B，累计融资 $260M [S13]——本轮给出的定位语就是"构建/评估/观测/部署 AI agents 的领先平台"；
- 商业闭环：LangSmith（观测/评估/部署）承接开源流量 [S13]。

**CrewAI**——最强的"企业运营数据"叙事：
- 官网口径：**65% 的 Fortune 500 在用**、月 4.5 亿+ agentic 工作流、每周 4,000+ 注册 [S11]（厂商自报，未核验）；
- 具名案例：DocuSign（线索首次接触提速 75%）、General Assembly（课程开发时间 -90%）、PwC（代码生成准确率 10%→70%）、Piracanjuba（客服 95% 准确率）[S11][S19]；
- AMP Factory 支持本地化/私有云部署（IBM、PwC 属 Factory 类客户口径）[S19]；
- 自家 2026 调查：74% 企业视 agent 为关键/战略优先级，65% 已在生产或团队工作流使用，已自动化平均 31% 工作流 [S18]。

**Microsoft Agent Framework**——最大的分发渠道：
- Semantic Kernel 内部支撑 Microsoft 365 Copilot，Fortune 500 经 SK 已有生产存量 [S23]；MAF 承接这条企业通道；
- Foundry Agent Service 提供托管运行时（缩容到零、会话隔离、断点恢复、Application Insights 零接线观测）[S10]；
- 对 .NET 存量企业（金融/保险/医疗/制造）是"唯一不逼团队转 Python"的一等选择 [S20]；
- 弱点：GA 仅 5 个月，第三方内容生态（教程/StackOverflow 覆盖）仍薄 [S20]，Python/.NET 功能对齐是移动靶 [S20][S21]。

**LlamaIndex**——垂直场景的具名背书：
- **Salesforce Agentforce** 团队公开背书（SVP 级引言）[S12]；Carlyle（PE）解析场景证言 [S12]；Jeppesen（波音旗下）省 ~2,000 工程小时 [S24]；
- 官网口径：5 亿+文档处理、月 2,500 万+包下载、30 万+ LlamaCloud 用户 [S12]（厂商自报，未核验）；
- 资本：Databricks 与 KPMG 投资 [S24]（金额未核验）；
- 金融/保险/制造/医疗的行业化叙事明确 [S12]。

### 6.3 采购侧变化（四家共同面对）

Mayfield 调查 [S32]：**业务线负责人（46%）首次超越 CIO/CTO（各 38%）成为最大决策群体**；84% 要求安全合规不可妥协但 60% 尚无正式 AI 治理框架；70% 要求先在自己环境试跑。**含义**：框架的"低代码/业务可用性 + 沙箱试用 + 治理证据"直接决定赢单——这正是 CrewAI AMP 和各家控制面 2026 年发力的原因。

---

## 7. 优缺点对比

### 7.1 总矩阵

| | LangChain/LangGraph | CrewAI | Microsoft Agent Framework | LlamaIndex |
|---|---|---|---|---|
| **核心优势** | 持久化执行最深；生态最广（700+ 集成口径）；HITL 原生；1.0 后 API 稳定承诺；双语言 | 角色模型上手最快；Flows 确定性补齐；AMP 控制面合规深（执行路径内控制）；企业案例具名且多 | .NET 唯一一等公民；微软企业通道与 Foundry 托管；LTS 承诺；CodeAct 等性能机制 | 文档解析质量标杆（LlamaParse）；ParseBench 自建公开基准；数据连接器多；context engineering 叙事匹配数据密集场景 |
| **核心短板** | 双库双心智模型（学习成本）；文档churn（1.0 迁移作废大量旧教程）；图调试难 | 角色提示词 token 开销高；自治循环需手工设限（max_iter 等）；企业定价不透明 | 生态年轻（教程/第三方内容薄）；Python/.NET 对齐是移动靶；文档 Azure 倾向 | 主包仍 0.x（API 迁移风险）；托管部署 beta；作为通用编排器不如前三家 |
| **最适合** | 有状态长任务、多阶段审批、需要审计回放的生产 agent | 业务分工清晰的自动化（销售/运营/客服流程）、业务团队要参与构建的企业 | Azure/.NET 存量企业、需要厂商 LTS 与合规兜底的团队 | 文档密集型智能 RAG/抽取（合同、财报、理赔、研报） |
| **最不适合** | 一个 prompt 一次解析的简单调用（抽象税） | 高并发低延迟的严格序列任务（编排开销） | Python-only 小团队快速原型 | 把它当通用多智能体编排器用 |
| **迁移风险** | 低（1.x 稳定承诺，弃用有缓冲期至 2026-12） | 低-中（1.x 但迭代快，行为类 API 偶变） | 中（SK/AutoGen→MAF 迁移非自动，有官方指南） | 中-高（0.x + llama-deploy→llama-agents、llama_cloud_services→llama-cloud 等拆包迁移 [S25]） |

### 7.2 逐家一句话锐评

- **LangGraph**：2026 年"把 agent 当分布式系统做"的代名词——checkpoint/HITL/回放是别人要自建工作流引擎才追得上的能力 [S14]；代价是你必须接受"图思维"并自己管理两个库的边界。
- **CrewAI**：从"被批评的玩具"进化为"企业控制面"最激进的玩家（2026 年补齐 Flows 生产化、可插拔后端、MCP/A2A）[S17]——但便利性与 token 成本的内在交换没有消失，不设防的 crew 依旧不可以上生产 [S17]。
- **MAF**：企业采购逻辑下几乎必进短名单（微软渠道 + LTS + .NET），但"新"是硬伤——社区答案、案例库、踩坑帖都要等 2026 下半年到 2027 才厚起来 [S20]。
- **LlamaIndex**：主动放弃"通用框架"内卷、卡死"文档智能"生态位并自建基准锁心智 [S24]——如果你的痛点是复杂文档，它近于默认选项；如果不是，它的 agent 能力对你只是赠品。

---

## 8. 选型建议

### 8.1 场景决策表

| 你的场景 | 首选 | 理由与备注 |
|---|---|---|
| 有状态、长周期、需要人工审批/审计回放的生产 agent | **LangGraph** | checkpoint + interrupt 是硬需求；无替代时不自建工作流引擎 [S14] |
| 销售运营客服类流程自动化，角色分工天然清晰，业务团队想参与 | **CrewAI（+AMP）** | 角色模型 + 低代码 + 控制面匹配"LOB 主导采购"趋势 [S11][S32]；确定性部分务必走 Flows 并设 max_iter [S17] |
| .NET 存量 / Azure 合同 / 需要厂商 LTS | **MAF** | 唯一 .NET 一等；迁移 SK/AutoGen 趁 2026 规划 [S20][S21] |
| 合同/财报/理赔/研报等复杂文档智能 | **LlamaIndex（+LlamaCloud）** | 解析质量上游决定一切；ParseBench 佐证 [S12][S24] |
| OpenAI 单生态、轻量多智能体 | **OpenAI Agents SDK** | harness 轻、issue 积压小 [S7]；深度编排需求上来后再叠框架 |
| Gemini 生态 | **Google ADK** | 与 Vertex/Agent Engine 绑定 [S8] |
| 极端成本敏感的确定性流水线 | **自建（FastAPI + LiteLLM）或 MAF CodeAct** | 别为一次调用上框架 [S15]；CodeAct 可折叠编排开销 [S10] |

### 8.2 反模式（比"选谁"更重要）

1. **按 benchmark 排名选框架**——基准测模型不测框架，且 2026 年基准本身可信度崩塌 [S28]。
2. **拿别人 benchmark 数字当自己的预期**——托管环境、提示词、工具集一动，数字全变 [S28][S30]；唯一正确姿势：**自建 30-100 条贴近真实业务的评估集，测成功率 + N-run 可靠性 + p95 延迟 + 每任务成本**。
3. **为一个 prompt 一次解析上重型框架**——抽象税纯亏 [S15]。
4. **自治 agent 不设上限**——无论哪家，循环上限、超时、终止条件是生产底线 [S17]。
5. **忽视"上产率瓶颈在组织"**——数据就绪、治理、评估设施决定 88% 的试点命运 [S35][S36]；选框架时把控制面能力（观测/审批/审计）当一票否决项。

### 8.3 混合策略（2026 年越来越常见）

协议层（MCP/A2A）成熟让"混搭"成本大降：常见组合是 **LangGraph 做核心编排 + LlamaParse 处理文档输入 + LangSmith 评估 + 各家工具经 MCP 接入**；或 **CrewAI 做业务侧快速搭建 + LangGraph 承接性能关键路径** [S17]。选型不再是单妻制，控制面与协议栈才是长期绑定项。

---

## 9. 趋势展望（2026 H2 → 2027）

1. **持久化执行成为标配底线**——MAF Foundry 的"缩容到零 + 状态保持恢复"、CrewAI checkpoint 遥测，说明 LangGraph 立的标杆正在被全行业追平 [S3][S10]。
2. **Harness 模式从 coding agent 反哺通用框架**——文件记忆/Todo/计划-执行分离/子代理（MAF Agent Harness、LangChain deepagents）让"长时程自治"工程化 [S9][S10]。
3. **协议竞争白热化**——MCP 已成事实标准（9,400+ server），A2A/ACP/AG-UI 在 agent 互操作与前端交互两层继续分叉，押注框架时先看协议覆盖 [S24][S35]。
4. **评估与治理从加分项变准入项**——56% 企业设"AI agent owner" [S35]；有治理设施者上产率高 12 倍 [S36]；框架自建基准（ParseBench）与第三方评估集成（CrewAI×Arize/Galileo）会继续加码。
5. **"员工化"叙事接管"工作流"叙事**——长时程自治文档代理（LlamaIndex）与生产级 hosted agents（MAF/Foundry）是同一趋势的两面：agent 从工具变成有身份、有状态、有 KPI 的数字员工 [S10][S24]。

---

## 附录 A：GitHub API 一手采集记录（采集时刻 2026-09-16）

| 仓库 | stars | forks | open_issues | created_at | pushed_at | license(API) |
|---|---|---|---|---|---|---|
| langchain-ai/langchain | 146,422 | 24,478 | 515 | 2022-10-17 | 2026-09-16T04:35Z | MIT |
| langchain-ai/langgraph | 41,730 | 7,054 | 790 | 2023-08-09 | 2026-09-15T16:04Z | MIT |
| crewAIInc/crewAI | 58,633 | 8,471 | 808 | 2023-10-27 | 2026-09-16T06:26Z | MIT |
| run-llama/llama_index | 52,174 | 8,147 | 773 | 2022-11-02 | 2026-09-15T23:21Z | MIT |
| microsoft/autogen | 61,004 | 9,218 | 1,071 | 2023-08-18 | 2026-04-15T11:59Z | CC-BY-4.0* |
| microsoft/agent-framework | 13,531 | 2,322 | 606 | 2025-04-28 | 2026-09-15T10:59Z | MIT |
| openai/openai-agents-python | 29,474 | 4,745 | 78 | 2025-03-11 | 2026-09-16T04:18Z | MIT |
| google/adk-python | 21,544 | 4,010 | 493 | 2025-04-01 | 2026-09-15T11:05Z | Apache-2.0 |

\* 见第 1 节未验证项 6。最新 release 一手读数：langchain-core==1.6.3（2026-09-11）；crewAI 1.15.21（2026-09-09）；llama_index v0.14.24（2026-08-19，核心包仍 0.x）；microsoft/agent-framework dotnet-1.21.0（2026-09-11）。

## 附录 B：来源清单

**一手（本次 GitHub API 采集，2026-09-16）**
- [S1] api.github.com/repos/langchain-ai/langchain（含 releases/latest）
- [S2] api.github.com/repos/langchain-ai/langgraph
- [S3] api.github.com/repos/crewAIInc/crewAI（含 releases/latest 1.15.21）
- [S4] api.github.com/repos/run-llama/llama_index（含 releases/latest v0.14.24）
- [S5] api.github.com/repos/microsoft/autogen
- [S6] api.github.com/repos/microsoft/agent-framework（含 releases/latest dotnet-1.21.0）
- [S7] api.github.com/repos/openai/openai-agents-python
- [S8] api.github.com/repos/google/adk-python

**官方/厂商**
- [S9] docs.langchain.com/oss/python/releases（LangChain/LangGraph/deepagents changelog）
- [S10] Microsoft BUILD 2026 官方博客：aka.ms/Build2026MicrosoftAgentFramework
- [S11] crewai.com 官网（控制面/运营口径/案例）
- [S12] llamaindex.ai 官网（产品线/运营口径/客户证言）
- [S13] aiwiki.ai/wiki/langgraph（含官方 1.0 公告与融资信息引注）

**第三方分析**
- [S14] research.modelcitizendeveloper.com/survey/1-200（2026-08-17 核验版本）
- [S15] ayautomate.com/blog/langgraph-vs-langchain（2026）
- [S16] everydev.ai/tools/crewai（2026-05 更新）
- [S17] joshuaopolko.com/crewai-setup-production-guide（2026）
- [S18] dallasvc.com/posts/why-we-invested-in-crewai（含 2026-05-17 GitHub API 读数）
- [S19] megaoneai.com/spotlight/crewai-review
- [S20] aitooltier.com/tools/microsoft-agent-framework
- [S21] digitalapplied.com/blog/microsoft-agent-framework-1-0-dotnet-python-guide
- [S22] institutepm.com/knowledge-hub/microsoft-agent-framework-for-product-managers
- [S23] aiwiki.ai/wiki/semantic_kernel
- [S24] aiwiki.ai/wiki/llamaindex
- [S25] futureagi.com/blogs/exploring-llamaindex-a-powerful-tool-for-llms
- [S26] aiagentsquare.com/agents/llamaindex
- [S27] marianebekker.com/insights/tools/llamaindex-agentic-rag-guide-2026
- [S28] rapidclaw.dev/blog/ai-agent-benchmarks-2026
- [S29] benchmarkingagents.com/langgraph-benchmarks
- [S30] aiworkflowlab.dev/zh/article/langgraph-vs-crewai-vs-autogen-2026（⚠️ 单源自测）
- [S31] aidevdayindia.org/blogs/ai-agent-framework-decision-matrix/...（⚠️ 方法学弱）
- [S32] mayfield.com/the-agentic-enterprise-in-2026
- [S33] aibusinessweekly.net/p/ai-agents-statistics
- [S34] agentmarketcap.ai/blog/2026/04/18/51-percent-production-23-percent-scaling...
- [S35] prgress.co/4vnFHhz（Progress Software，120+ 数据点汇编）
- [S36] ai2.work/blog/enterprise-ai-agents-are-finally-moving-from-pilots-to-production

---

*报告基于 2026-09-16 可获得的公开信息。框架迭代极快（本次采集窗口内已有 4 个新 release），版本与数字请以 PyPI/GitHub 实时数据为准；标注"未验证"的内容不构成结论。*
