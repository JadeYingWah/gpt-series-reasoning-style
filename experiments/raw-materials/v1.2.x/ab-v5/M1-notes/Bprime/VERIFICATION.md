# M1-notes 验证记录（Bprime 臂）

- 日期：2026-09-13
- 环境：Windows 11 + Python 3.13.14（实测 `python --version`）
- 方式：以下每条命令均在真实终端逐条运行，结论为实际观察到的输出

## 验收标准逐项实测

| # | 验收项 | 命令 | 实际结果 |
|---|--------|------|----------|
| 1 | 空库友好提示 | `python list.py` / `python stats.py`（无 notes.json） | 「（暂无笔记…）」/ 总数 0 +（无），exit=0；notes.json 未被提前创建 |
| 2 | add→list 基础流 | `python add.py "t" "c"` → `python list.py` | 输出「已添加笔记 #1：t」；list 表格可见 #1；notes.json 自动创建，字段 id/title/content/tags/created_at 齐全 |
| 3 | 自增 id | 连续 add 5 条 | id 依次 1→5，无重复 |
| 4 | search 大小写不敏感 | `python search.py hello`；`python search.py FOX` | 均命中 #2「Hello World/The quick brown FOX jumps」；`search.py LINE1` 命中内容小写 "line1" |
| 5 | search 无结果 | `python search.py 不存在的关键词zzz` | 「（未找到…）」，exit=0 |
| 6 | --tag 过滤 | `python list.py --tag demo` / `--tag 生活` / `--tag 不存在的标签` | demo→恰为 #2、#5 共 2 条；生活→恰为 #4 共 1 条；不存在→友好提示 |
| 7 | stats 数字正确 | `python stats.py` | 总数 5 正确；最新 3 条按时间倒序为 #5、#4、#3 正确；最长笔记 #5，57 字（与 `len(content)` 一致） |
| 8 | 空标题边界 | `python add.py "" "c"`；`python add.py "   " "c"` | 均报「错误：标题不能为空。」（stderr），exit=1，不写入数据 |
| 9 | 特殊字符往返 | add 内容含 `"`、`&`、`<tag>`、换行、emoji 🎉、中文 | add 成功（#6）；list 正常显示（换行显示为 `\n`，超长截断）；search「hi」命中；JSON 文件转义正确 |
| 10 | 重复 id 修复 | 手工构造含两个 id=1 的 notes.json 后 `python list.py` | 第二个重复 id 被重编号为 max+1=4，显示唯一，且修复结果自动写回文件（自愈） |
| 11 | 损坏 JSON | 写入 `not json{{{` 后 `python list.py` | stderr 报「notes.json 读取失败…」，exit=2，不静默丢数据 |
| 12 | 独立运行/数据落点 | 在 <实验根目录> 下调用 `python ab-v5/M1-notes/Bprime/add.py …` | 正常写入脚本同目录 notes.json；CWD 未产生多余 json 文件 |
| 13 | 表格对齐 | 中文/英文混排全量列表 | 按 East Asian Width（中文 2 列）对齐，列整齐 |

## 边界说明

- 退出码约定：0 成功；1 用法错误（如空标题）；2 数据文件损坏。
- `--tag` 为精确匹配（区分大小写），已在 README 说明。
- 个别 emoji 在终端的实际渲染宽度可能与计算的 2 列有偏差（对齐按 Unicode 官方宽度计算），属已知限制，不影响功能。

## 最终交付状态

- 交付文件：add.py、list.py、search.py、stats.py、storage.py、README.md、VERIFICATION.md、notes.json（运行时自动生成，含 7 条演示数据）
- 以上所有验证均在上述环境真实执行通过；无 UNVERIFIED 项。
