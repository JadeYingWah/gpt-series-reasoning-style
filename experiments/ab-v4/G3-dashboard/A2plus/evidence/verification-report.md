# G3-dashboard A2plus 验证证据报告

- 产物：`index.html`（单文件静态数据看板，双击即开，无服务器/无外部依赖）
- skill 配置：轻量+（验证深度增强版 A2+），skill v1.2.1
- 报告日期：2026-09-13
- 一句话完成标准（门禁声明）：**5 个筛选态下指标卡三值与图表柱数/逐柱数值均等于由内联数据独立复算的期望值，且真实 headless 渲染无异常、无外部依赖** —— 达成。

## 1. 可复现验证命令

```powershell
powershell -ExecutionPolicy Bypass -File evidence\run_all.ps1
# 分步等价：
node evidence\compute_node.mjs        # 路径1：Node 独立复算
python evidence\compute_python.py     # 路径2：Python 独立复算 + WCAG 对比度
node evidence\check_cross.mjs         # 路径1≡路径2 交叉比对
node --check evidence\page_script_extracted.js   # 页面脚本语法检查
node evidence\dom_shim_test.mjs       # 路径3：DOM 仿真交互（点击/URL参数/乱序/边界）
node evidence\browser_check.mjs       # 路径4：Edge headless 真实渲染 5 态
node evidence\mutation_test.mjs       # 变异测试：验证体系鉴别力证明
```

最终端到端执行：`run_all.ps1` 7/7 步全绿（exit 0）。

## 2. 多路径交叉验证矩阵

| 核心结论 | ①Node复算 | ②Python复算 | ③DOM仿真点击 | ④Edge headless渲染 | 判定 |
|---|---|---|---|---|---|
| 5 态指标卡三值 = 独立复算值 | ✓ | ✓ | ✓ 16/16 | ✓ 5/5 | **4 路径一致** |
| 5 态图表柱数/逐柱数值 = 内联数据 | ✓ | ✓ | ✓ | ✓（data-v 序列逐柱核对） | **4 路径一致** |
| 筛选切换全展示区同步更新 | — | — | ✓（点击+乱序迁移） | ✓（?scope 直达态） | **2 路径一致** |
| 页面脚本无运行时异常 | 语法 ✓ | — | ✓ 0 异常 | ✓ 渲染完整（致命错误会停留在占位符"–"，已排除） | 2 路径一致 |
| 文本对比度 ≥ 4.5:1（WCAG AA） | — | ✓ 8/8 对 | — | — | 领域标准计算 |
| 无外部依赖（禁 CDN） | 源码扫描：无 `<link>`/外链 script/img/@import/url()；唯一 http 字符串为 SVG 命名空间常量（非网络请求） | | | | ✓ |

## 3. 独立复算基线（双语言一致，可直接人工复算）

单位：万元。内联数据：1月128, 2月96, 3月145, 4月132, 5月158, 6月176, 7月143, 8月151, 9月189, 10月205, 11月234, 12月218。

| 筛选态 | 月份数 | 总额 | 月均值(1位小数) | 峰值月 |
|---|---|---|---|---|
| 全年 | 12 | 1,975 | 164.6 | 11月（234） |
| 第一季度 | 3 | 369 | 123.0 | 3月（145） |
| 第二季度 | 3 | 466 | 155.3 | 6月（176） |
| 第三季度 | 3 | 483 | 161.0 | 9月（189） |
| 第四季度 | 3 | 657 | 219.0 | 11月（234） |

真实渲染快照存档：`evidence/out_render/scope-*.html`（5 份，含 active 按钮、aria-pressed、bar-peak 高亮与动态 aria-label）。

## 4. 变异测试（「通过率不是鉴别力」应对）

向临时副本注入 3 个真实缺陷，验证体系全部转红（`out_mutation.json`）：

| 注入缺陷 | 预期检出的检查 | 结果 |
|---|---|---|
| M1 峰值卡显示第一个月而非最大月 | dom_shim / browser | 捕获 |
| M2 setScope 改为 no-op（筛选同步失效） | dom_shim | 捕获 |
| M3 总额硬编码 9999（显示与数据脱钩） | browser / dom_shim | 捕获 |

3/3 捕获 —— 全绿结论具备鉴别力，非恒真断言。临时副本均在系统临时目录运行并自清理。

## 5. 保守度调节（A2+ 条款）：主报告只取最保守路径结果

**主报告（保守确认）**：上表判定列中标注"4 路径一致 / 2 路径一致"的结论全部成立，其中浏览器路径（④）为最保守方法，其结果与所有其他路径无冲突。

**候选/待确认（附录，不污染主报告）**：
- [候选·UNVERIFIED(直接观测)] "无控制台报错"为**间接验证**：本环境无 CDP 客户端库（按任务边界不安装新依赖），无法直接读取真实浏览器 console 对象。已用两层间接证据覆盖：①DOM 仿真完整执行页面脚本 16 项状态断言 0 异常；②真实 Edge headless 渲染 5 态内容完整（若脚本存在致命错误，指标卡会停留在占位符"–"，该情形已被 ④ 排除）。人工复核步骤：双击打开 index.html，按 F12 查看 Console 应无红色报错（预计 10 秒）。
- [候选·已部分证实] aria-pressed 与 active 的同步：q3 真实快照中已见 `aria-pressed="true"` 正确落位；其余 4 态由 DOM 仿真确认（仿真与真实渲染在 q3 态行为一致，无冲突迹象）。

## 6. 闭环检查（对照门禁声明）

| 门禁声明 | 实际应用情况 |
|---|---|
| 完成标准（5 态一致+真实渲染+无外部依赖） | 逐项达成，见 §2 |
| 任务类型：代码+数据+视觉复合类（取严） | 数据类→Python 独立计算 ✓；代码类→语法+边界（非法 scope 回退、URLSearchParams 缺失回退、千分位/尾零格式化）✓；视觉类→对比度计算 ✓；执行中类型未变化 |
| 风险分档：中档、事前声明不停等、事后证据报告 | 本报告即事后证据 |
| 资源盘点：Node/Python/Edge/Chrome | 全部实际使用（Chrome 未用到，Edge 命中）；WebSearch 佐证的设计实践已应用（KPI 卡置顶、筛选器固定顶部、克制配色+低对比网格线、≥4.5:1 对比度、SVG 直接标注数值+aria、千分位、响应式单断点） |
| 简化声明（跳过完整参照系/2轮审查/子Agent） | 按声明执行；质量补偿=A2+ 四增强点全部落地（多路径交叉 ✓、证据入 evidence/ ✓、可检查完成标准 ✓、保守度调节 ✓） |
| 简化项清单（交付能力层面） | 无——未砍任何已计划能力 |
| 参照系变更记录 | 0 次（初始参照系=门禁一句话目标声明，执行中无变更） |
| 数据性质诚实声明 | 12 个月数据为演示用虚构数值（页面副标题已注明"演示数据（虚构编制）"），与展示一致可复算 |

## 7. 证据文件清单

```
A2plus/
├── index.html                      # 交付产物（单文件看板）
└── evidence/
    ├── run_all.ps1                 # 一键复现全电池（7 步）
    ├── compute_node.mjs            # 路径1：Node 独立复算
    ├── compute_python.py           # 路径2：Python 独立复算 + WCAG 对比度
    ├── check_cross.mjs             # 双语言交叉比对
    ├── dom_shim_test.mjs           # 路径3：DOM 仿真交互（16 项断言）
    ├── browser_check.mjs           # 路径4：Edge headless 真实渲染
    ├── mutation_test.mjs           # 变异测试（鉴别力证明）
    ├── page_script_extracted.js    # 被测页面脚本存档（node --check 对象）
    ├── out_node.json / out_python.json / out_contrast.json
    ├── out_shim.json / out_browser.json / out_mutation.json
    └── out_render/scope-{all,q1,q2,q3,q4}.html   # 真实渲染 DOM 快照
```
