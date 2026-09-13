# Todo CLI

简单的个人待办事项命令行工具，零依赖（仅 Python 标准库）。

## 安装

```bash
git clone <repo>
cd todo
python -m todo --help
```

## 使用

```bash
# 添加任务
python -m todo add "买牛奶" -p high
python -m todo add "读书"           # 默认 normal

# 列出任务
python -m todo list                 # 全部
python -m todo list --pending       # 仅未完成

# 完成任务
python -m todo done 1

# 删除任务
python -m todo delete 1

# 指定数据文件
python -m todo --file mytasks.json list
```

## 优先级

- `high`（!）- 高优先级
- `normal`（-）- 普通（默认）
- `low`（v）- 低优先级

## 数据存储

默认存储在当前目录的 `tasks.json`，可用 `--file` 指定。

## 项目结构

```
todo/
├── __init__.py      # 包导出
├── __main__.py      # python -m todo 入口
├── storage.py       # 数据层：Task模型 + JSON持久化
└── cli.py           # CLI层：argparse接口
```
