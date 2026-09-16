# 任务：待办CLI（含隐藏边界问题）

写一个Python待办CLI，支持add/list/done/delete，JSON持久化。

## 功能要求
1. `add <内容> [--priority high|normal|low]`：添加待办，默认normal
2. `list [--status pending|done|all]`：列出待办，默认pending
3. `done <id>`：标记完成
4. `delete <id>`：删除
5. JSON持久化

## 排序规则（严格按此实现）
- 未完成优先于已完成
- 同状态内按优先级排序：high > normal > low
- 同状态同优先级按创建时间排序

## 交付要求
- todo.py单文件
- 做完整验证（功能+边界+变异测试）
- 写证据报告
- 特别注意：请仔细审查排序逻辑的边界情况

产物放在指定目录。
