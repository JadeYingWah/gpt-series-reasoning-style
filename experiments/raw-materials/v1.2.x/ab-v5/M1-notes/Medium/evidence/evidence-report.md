# 证据报告（M1-notes · Medium 臂 · skill 1.2.2 中等档）

环境：Windows 11 / Git Bash / Python 3.13.14（实测）。全部验证为交付目录内 python 逐命令真实运行。

## 一、完成声明与可复现验证命令

四命令全部可独立运行且行为与任务书一致。复现（在交付目录执行，`D` 为本目录）：

```bash
python add.py "t" "c" && python list.py          # 验收链路 → evidence/01
python add.py "会议纪要" "讨论 Q3 计划" --tag 工作 --tag 计划   # → evidence/02
python list.py --tag 工作                         # 过滤正确 → evidence/03
python search.py todo && python search.py TODO    # 大小写不敏感 → evidence/04
python stats.py                                   # 总数/最新3条/最长 → evidence/05
python add.py "" "x"                              # 期望 exit=1 → evidence/06
python list.py --help                             # → evidence/09
```

关键数字核算：stats 输出"总数 4 / 最新 3 条 id 4,3,2 / 最长 21 字"，与手工核算一致；变异恢复后复验"最长 14 字"亦一致。

## 二、闭环检查（对照门禁声明逐项）

| 门禁声明 | 实际应用情况 |
|---|---|
| 中等档必选：任务类型判断 | 已做，1 次网络搜索依据，判定代码类（流程最严） |
| 分阶段执行+每阶段审查 | 5 阶段执行；阶段 2/3 完成后均有对照参照系审查（见对话流） |
| 循环审查 2 轮 | 已做（evidence/review-log.md），第 1 轮发现 --help 覆盖缺口并补测，第 2 轮无新问题 |
| 证据报告 | 即本文件，证据统一在 evidence/ |
| 代码类：实操验证必选 | 已做：四命令逐条 python 实测 |
| 代码类：边界用例覆盖必选 | 已做：evidence/06/07 |
| 精简声明：网络搜索减为 1 次 | 已按中等档执行（1 次） |
| 精简声明：无 GUI 实操闭环 | 以逐命令真实运行替代（CLI 即交互面）；跨终端渲染标 UNVERIFIED |
| add.py --tag 为最小必要设计 | 已实现并在 README 声明理由（list --tag 过滤需写入端） |
| 交付前清理 notes.json 由脚本重建 | 已执行（见下"清理"节） |

## 三、覆盖面枚举与 ALL GREEN 声明

输入域分段及触达情况：

- **add.py**：正常（中/英文）✓；带多标签 ✓；空内容 ✓；空标题（拒）✓；全空白标题（拒）✓；特殊字符（引号/HTML/ñ/emoji/换行/tab）✓；缺参数（exit 2）✓
- **list.py**：全部 ✓；--tag 精确命中 ✓；--tag 无命中 ✓；空库 ✓；损坏文件（exit 1）✓；多行标题压平 ✓
- **search.py**：命中标题 ✓（"计划"初测命中 #2 内容，标题命中逻辑同路径）；命中内容 ✓；大小写变体 todo/TODO ✓；无命中 ✓；空关键词（拒）✓
- **stats.py**：多条 ✓；空库 ✓；重建后小库 ✓
- **storage**：id 自增序列 1→6 连续 ✓；损坏 JSON 保护且不覆盖 ✓；缺失自动重建 ✓；原子写入为代码路径审查（os.replace），未做并发实测

**可能未覆盖段**：多进程并发写入、Python <3.7 / 非 Windows 平台、East Asian Ambiguous 字符在各终端的渲染差异。理由：任务书未要求并发；本环境仅单平台单版本可实测。以上按 UNVERIFIED 处理，README「已知边界与限制」已如实记载。

## 四、诚实标记（UNVERIFIED 清单）

1. 跨终端/字体下表格对齐渲染效果（仅实测本环境 Git Bash + Read 工具核验字符级对齐）。
2. 多进程并发写场景（未测）。
3. Python 3.7~3.12 及 macOS/Linux 兼容（仅实测 Python 3.13.14 / Windows；代码未用 3.8+ 专属语法，reconfigure 已 try/except 兜底）。
4. `search.py` "命中标题"分支与"命中内容"分支共用同一表达式路径，标题命中仅由 todo/TODO 用例间接触达（内容命中），未单独构造纯标题命中用例。

## 五、变异抽查（通过率鉴别力）

移除 casefold（模拟回归缺陷）→ `search todo` 变红（evidence/08）；恢复后变绿。证明验证电池对"大小写不敏感"这一验收点具有鉴别力，非恒通过式断言。

## 六、清理

- `__pycache__/` 已删除（运行时残留）。
- `notes.json` 已删除：任务书定义"由脚本自动创建"，实测已证明缺失时任一命令自动重建（evidence/07）。
- 无 `.notes-*.tmp` 临时文件残留（原子写入的临时文件经 os.replace/unlink 均已消解）。

## 七、参照系变更历史

初始 v1（代码类/中等档/质量标准=任务书验收三条）→ 执行中无变更（0 次更新：任务类型、范围、质量标准全程未漂移）。

## 八、简化项清单

无。未砍掉任何已计划能力；add.py 的 --tag 为新增最小设计而非简化，已在 README 声明。
