# EVIDENCE.md — todo.py 验证证据报告

## 1. 产物清单
- `todo.py`：单文件 CLI 待办工具，零外部依赖（仅标准库 argparse/json/os/sys/tempfile/datetime）
- `test_todo.py`：功能 + 边界自动化测试
- `mutation_test.py`：变异测试脚本

## 2. 功能测试（7 项基础功能）
执行命令：`python test_todo.py`

| # | 测试项 | 结果 |
|---|--------|------|
| 1 | add 创建多条 + 自增 ID | PASS |
| 2 | add 默认 priority=normal | PASS |
| 3 | add --priority high 生效 | PASS |
| 4 | list 默认只显示 pending + 排序（未完成→优先级→创建时间） | PASS |
| 5 | list --status all 含 done 项且 pending 先于 done | PASS |
| 6 | done 标记状态为 done | PASS |
| 7 | delete 移除指定条目 | PASS |
| 8 | --help 正常输出（退出码 0） | PASS |
| 9 | 原子写入无残留 .tmp 文件 | PASS |
| 10 | list pending 中 high 先于 normal、normal 先于 low | PASS |

## 3. 边界测试
| # | 测试项 | 结果 |
|---|--------|------|
| 1 | 空列表友好提示 | PASS |
| 2 | done 不存在 ID → 退出码 1 | PASS |
| 3 | delete 不存在 ID → 退出码 1 | PASS |
| 4 | 重复 done → 友好提示（不报错、不重复写入） | PASS |
| 5 | 非法优先级 --priority urgent → argparse 拒绝（退出码非 0） | PASS |

## 4. 变异测试
执行命令：`python mutation_test.py`

共 10 个变异，覆盖排序、ID、原子写入、退出码、过滤、默认值、状态修改、删除、重复提示等核心逻辑。

| 变异 | 描述 | 结果 |
|------|------|------|
| M01 | 优先级排序权重 high 0→1 | KILLED |
| M02 | next_id 起始 1→0 | KILLED |
| M03 | 删除 os.replace 原子重命名 | KILLED |
| M04 | done 不存在退出码 1→0 | KILLED |
| M05 | list pending 过滤改为 done | KILLED |
| M06 | 默认优先级 normal→high | KILLED |
| M07 | done 不修改状态 | KILLED |
| M08 | delete 不删除 | KILLED |
| M09 | 排序状态权重反转 | KILLED |
| M10 | 移除重复 done 友好提示分支 | KILLED |

**杀伤率：10/10 = 100%**（要求 ≥80%，达标）

## 5. 实操闭环（真实用户操作）
在隔离目录中以真实命令行方式依次执行：
`--help` → `add high` → `add normal` → `add low` → `list` → `done 1` → `done 1`（重复）→ `list --status all` → `delete 2` → `delete 999`（退出码 1）→ `add --priority urgent`（退出码 2）→ `list`

全部行为符合预期：排序正确、状态标记正确、错误退出码正确、重复标记友好提示、JSON 数据持久化正常。

## 6. 代码质量检查
- **无硬编码路径**：DATA_FILE 基于 `os.path.dirname(os.path.abspath(__file__))` 动态计算
- **原子写入正确**：`tempfile.mkstemp` 写临时文件 → `os.replace` 原子重命名；异常时清理临时文件
- **错误退出码正确**：ID 不存在 → `sys.exit(1)`；无命令 → `sys.exit(1)`；argparse 参数错误 → 默认退出码 2
- **load/save 支持 path 参数覆盖**：便于测试隔离，默认回退到 DATA_FILE

## 7. 可复现验证命令
```bash
cd <实验根目录>\ab-metacognition\E1\weak-skill
python test_todo.py        # 功能+边界测试，期望 exit 0
python mutation_test.py    # 变异测试，期望杀伤率 ≥80%
```

## 8. 未验证项
无。所有功能、边界、变异、实操均已验证。
