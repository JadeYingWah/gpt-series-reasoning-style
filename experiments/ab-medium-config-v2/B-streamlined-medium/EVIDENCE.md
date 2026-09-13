# 证据报告 — 个人待办事项 CLI 工具

## 产物
- `todo.py`：单文件 CLI 工具，约 200 行，零第三方依赖。

## 验证命令与结果

| # | 命令 | 预期 | 实际 | 结果 |
|---|------|------|------|------|
| 1 | `add "完成项目文档" --priority high` | 创建 ID=1，优先级 high | 已添加任务 #1，优先级：高 | ✅ |
| 2 | `add "购买生活用品" --priority low` | 创建 ID=2，优先级 low | 已添加任务 #2，优先级：低 | ✅ |
| 3 | `add "复习英语单词"` | 创建 ID=3，默认 normal | 已添加任务 #3，优先级：中 | ✅ |
| 4 | `list` | 3 条任务，按优先级排序（高→中→低） | 顺序 1(高)→3(中)→2(低) | ✅ |
| 5 | `done 2` | 标记任务 2 完成 | 已标记任务 #2 为完成 | ✅ |
| 6 | `delete 3` | 删除任务 3 | 已删除任务 #3 | ✅ |
| 7 | `list`（操作后） | 剩 2 条，未完成在前 | 1(○高) → 2(✓低) | ✅ |
| 8 | `list --status pending` | 仅显示未完成 | 仅任务 #1 | ✅ |
| 9 | `list --status done` | 仅显示已完成 | 仅任务 #2 | ✅ |
| 10 | `done 2`（重复完成） | 提示已是完成状态 | 任务 #2 已经是完成状态 | ✅ |
| 11 | `done 999`（不存在 ID） | 退出码 1，报错 | 错误：未找到任务 #999，exit 1 | ✅ |
| 12 | `delete 999`（不存在 ID） | 退出码 1，报错 | 错误：未找到任务 #999，exit 1 | ✅ |
| 13 | JSON 文件内容检查 | 字段完整：id/title/priority/done/created_at/completed_at | 全部字段正确，completed_at 在完成时写入 | ✅ |
| 14 | `--help` | 显示子命令与用法 | 正常输出 add/done/delete/list | ✅ |

## 1 轮审查发现

- **排序逻辑正确**：未完成优先 → 优先级（high→normal→low）→ 创建时间，符合直觉。
- **幂等性**：重复 `done` 不会重复写入 completed_at，有友好提示。
- **错误处理**：不存在 ID 时退出码为 1 并输出 stderr，适合脚本集成。
- **原子写入**：使用临时文件 + `os.replace`，避免写入中断导致数据损坏。
- **零依赖确认**：仅 import argparse / json / os / sys / datetime，全部标准库。
- **未发现 bug**，全部 14 项验证通过。

## 使用示例

```bash
python todo.py add "写周报" --priority high
python todo.py list
python todo.py done 1
python todo.py delete 1
python todo.py list --status pending
```
