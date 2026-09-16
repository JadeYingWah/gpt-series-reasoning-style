# EVIDENCE.md — 无skill条件验证报告

## 产物
- `todo.py`：单文件 CLI 待办工具

## 验证
手动运行以下命令，均正常工作：
- add（含--priority high）
- list（默认pending、--status all）
- done（含重复done提示）
- delete
- done 不存在ID → 退出码1

## 未验证项
- 变异测试
- 边界条件完整覆盖
- 原子写入安全性
- 非法优先级处理
- 空列表行为
