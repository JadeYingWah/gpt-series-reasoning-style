# G1-A2plus 证据报告（轻量+ 验证深度增强版）

产物：`../index.html`（单文件计算器，双击即用，零外部依赖，约 8.5KB）
生成时间：2026-09-13 ｜ skill 版本：1.2.1 ｜ 配置：轻量+（A2+）

## 一、完成声明与可复现验证命令

完成声明：任务书全部验收条款满足，三条独立验证路径全绿。
复现命令（本目录下）：

```bash
bash run-all.sh          # 一键复现（oracle → 核心电池+变异 → 浏览器 E2E）
# 或分步：
python oracle.py         # 生成 vectors.json（26 向量，Python 精确分数期望值）
node test-core.mjs       # 路径2+3：核心电池 27 用例 + 变异测试 5/5
node test-browser.mjs    # 路径1：Chrome headless CDP 实操（26 向量点击 + 可信键盘事件 + 截图）
```

## 二、多路径交叉验证矩阵（A2+ 条款①）

| 结论 | 路径1 浏览器 E2E（真实 DOM） | 路径2 Node 核心 vs Python 精确分数 oracle | 路径3 变异测试（鉴别力） |
|---|---|---|---|
| 四则运算正确（含优先级/左结合） | 26/26 向量通过 | 27/27 用例通过 | M1/M5 杀死 |
| 小数运算正确（含浮点噪声清理 0.1+0.2→0.3） | 通过 | 通过 | M3/M4 杀死 |
| 全按钮可点击、状态正确切换 | 18 按钮可见且全向量覆盖、逐状态断言 | — | — |
| 键盘与鼠标行为一致 | Input.dispatchKeyEvent 可信事件，chain 序列逐字符一致 | — | — |
| 控制台 0 报错 | console.error=0、页面异常=0、window.onerror=0、warning=0 | — | — |
| 除零→"错误"且可恢复 | div_zero / error_recover 向量通过 | 通过 | M2 杀死 |
| 退格/C/重复小数点/前导零/结果续算 | 专用向量通过 | 通过 | — |

三条路径对全部结论一致，**无单路径独有发现**（无候选/待确认附录项）。

## 三、变异测试明细（通过率→鉴别力证明）

回答"把要防的错误做一次，它会不会红？"——5 类典型缺陷逐一注入核心逻辑：

| 变异体 | 缺陷类别 | 杀死用例（示例） | 结果 |
|---|---|---|---|
| M1-precedence-broken | 优先级破坏 | precedence#eq1（2+3×4：期望 14，变异后 20） | 杀死 |
| M2-div0-unguarded | 除零守卫移除 | div_zero#eq1（5÷0：期望 ERR(DIV0)，变异后 Infinity） | 杀死 |
| M3-decimal-stripped | 小数点剥离 | float_add#eq1（0.1+0.2：期望 0.3，变异后 3） | 杀死 |
| M4-clean-removed | 显示清理移除 | float_add#eq1（变异后 0.30000000000000004） | 杀死 |
| M5-sub-to-add | 减法变加法 | left_assoc_sub#eq1（9−4−3：期望 2，变异后 16） | 杀死 |

杀伤率 **5/5**。结果文件：`results/core-battery.json`、`results/browser-results.json`。

## 四、任务书验收条款逐项对照

1. 「所有按钮可点击且状态正确切换，无控制台报错」→ 18 按钮全部可见（getBoundingClientRect + offsetParent）、26 向量逐点击断言状态、四通道错误收集全零。✔
2. 「四则运算结果正确，含小数运算」→ 浏览器路径 + Python 精确分数 oracle 双路径一致（含 0.1+0.2=0.3、9.9×9=89.1、1÷3=0.333333333333 12 位有效数字清理）。✔
3. 「键盘输入与鼠标点击行为一致」→ CDP 可信键盘事件（Input.dispatchKeyEvent）与鼠标点击同序列逐字符一致；另验证 x→×、Enter/=、Backspace、Escape/Delete/C 映射与 .pressed 视觉反馈（出现并 150ms 后移除）。✔

## 五、闭环检查（对照门禁声明逐项）

| 门禁声明 | 实际执行 |
|---|---|
| 可检查完成标准 5 条 | ①小数正确且 0.1+0.2 显示 0.3 ✔ ②全按钮可点击状态正确 ✔ ③键盘/鼠标逐字符一致 ✔ ④控制台 0 报错 ✔ ⑤除零显示"错误"可恢复 ✔ |
| 任务类型=代码类（搜索佐证） | 执行中未发生类型变化；浮点清理方案（toPrecision(12)）取自搜索佐证（Stack Overflow 主流方案） |
| 风险分档=轻 | 无新增破坏性/外部副作用，分档维持成立 |
| 资源盘点：chrome-cdp-frontend-verify 用于实操验证 | 已按计划使用（本机 Chrome + Node22 内置 WebSocket，零安装） |
| Python 独立 oracle | 已按计划使用（fractions 精确求值，与 JS float 路线独立） |
| agent-browser 弃用理由 | 维持：避免 Chromium 下载风险，裸 CDP 已全覆盖 |
| A2+ 保守度调节 | 三路径全一致，主报告即保守结论；无未确认候选项 |
| 精简声明（宿主对齐跳过、循环审查 2→1 轮） | 按声明执行；第 1 轮审查含验证，无新发现 |
| 临时物隔离与自清理 | Chrome user-data-dir 在系统 Temp 独立目录，任务后已删除（已核实）；无全局 taskkill（仅按 PID 树清理自启进程） |

## 六、简化项清单

无。计划能力全部交付（未砍任何已计划功能）。

## 七、UNVERIFIED 项（诚实标记）

1. **真实（非 headless）浏览器人工目测**：UNVERIFIED——本环境无交互 GUI，验证以 headless Chrome 真实 DOM + 截图替代；截图 5 张已逐张人工查验内容正确（初始/表达式/结果/错误/键盘态）。用户自验：双击 index.html 即可。
2. **超大量级数值（|x|>1e21 科学计数法显示）**：已做守卫（结果续算禁用、无崩溃、无报错）但未入验收向量域，行为正确性 UNVERIFIED。
3. **跨浏览器兼容（Firefox/Safari）**：仅 Chrome 136 headless 实测；所用 API（dataset、classList、KeyboardEvent）为广泛支持标准，但未实测，UNVERIFIED。

## 八、任务参照系变更历史

初始参照系＝门禁声明（目标/类型/分档/资源/完成标准）。执行中更新次数：**0**——任务类型（代码类）、风险档（轻）、范围与完成标准均未变化，未发生参照系修订。

## 九、文件结构

```
A2plus/
├── index.html                  # 交付物：单文件计算器
└── evidence/
    ├── run-all.sh              # 一键复现
    ├── oracle.py               # Python 精确分数 oracle + UI 序列模拟器
    ├── vectors.json            # 26 向量期望值（oracle 生成）
    ├── test-core.mjs           # 路径2 核心电池 + 路径3 变异测试
    ├── test-browser.mjs        # 路径1 Chrome headless CDP 实操验证
    ├── results/
    │   ├── core-battery.json   # 27/27 + 变异 5/5 明细
    │   └── browser-results.json# 26/26 点击 + 键盘一致性 + 控制台零错误明细
    ├── screenshots/            # 5 阶段截图（已逐张人工查验）
    └── report.md               # 本报告
```

## 十、观察项（不影响验收）

- 默认 800×600 视口下页面出现滚动条（内容高度略超 600px）；真实桌面窗口尺寸下无此现象。保留滚动而非隐藏 overflow，避免小窗口下按钮不可达。
