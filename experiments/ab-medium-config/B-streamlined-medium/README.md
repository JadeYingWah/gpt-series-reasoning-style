# Todo CLI

零依赖待办事项命令行工具。

```bash
python -m todo add "买牛奶" -p high   # 添加
python -m todo list                    # 列出
python -m todo list --pending          # 仅未完成
python -m todo done 1                  # 完成
python -m todo delete 1                # 删除
python -m todo --file my.json list     # 指定数据文件
```

优先级：high(!) / normal(-) / low(v)。数据存 JSON，默认 `tasks.json`。
