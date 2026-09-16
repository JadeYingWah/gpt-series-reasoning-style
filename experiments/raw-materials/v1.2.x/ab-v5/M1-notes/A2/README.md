# 命令行笔记工具集（M1-notes）

四个命令共享同一 JSON 存储文件 `notes.json`（位于本目录，首次添加时自动创建，无需手工建立）。

## 安装

- 依赖：Python 3.8+（仅用标准库，无需 pip 安装任何东西）
- 无需安装步骤：直接运行本目录下的脚本即可；从其他目录运行也可以（存储文件始终固定在本目录）。

## 用法

```text
python add.py    "标题" "内容" [--tag 标签]...
python list.py   [--tag 标签]
python search.py 关键词
python stats.py
```

| 命令 | 行为 |
|---|---|
| `add.py` | 新增笔记：自动记录创建时间、自增 id；`--tag` 可重复使用，为一条笔记打多个标签 |
| `list.py` | 表格对齐列出全部笔记；`--tag 标签` 只列出带该标签的笔记 |
| `search.py` | 对标题+内容做模糊搜索，大小写不敏感 |
| `stats.py` | 统计输出：总笔记数、最新 3 条（按 id 倒序）、最长笔记（按内容字符数） |

## 示例

```text
python add.py "买菜" "周一买鸡蛋和牛奶" --tag 生活 --tag 待办
python add.py "TODO" "Finish the Report" --tag 工作
python list.py              # 全部笔记
python list.py --tag 工作   # 只看带“工作”标签的笔记
python search.py todo       # 大小写不敏感，命中 “TODO”
python stats.py             # 总数 / 最新 3 条 / 最长笔记
```

## 存储格式

`notes.json` 为 UTF-8 JSON 数组，每条记录形如：

```json
{"id": 1, "title": "买菜", "content": "周一买鸡蛋和牛奶", "tags": ["生活", "待办"], "created_at": "2026-09-13 10:00:00"}
```

## 边界行为

- 空标题（或纯空白）拒绝添加，退出码 1
- `notes.json` 损坏/不可读时报错退出（退出码 1），不做任何写入，防止覆盖用户数据
- id 始终取现有最大 id + 1：即使文件被手工编辑出重复 id，新笔记也不会撞号
- 特殊字符（引号、反斜杠、换行、emoji、中文）经 JSON 往返无损
- 缺少必需参数时显示用法提示并以退出码 2 退出
- `list.py` 内容列超过 20 字符时截断显示（不影响存储内容）

## 文件结构

```text
add.py      新增命令
list.py     列表命令
search.py   搜索命令
stats.py    统计命令
storage.py  共享读写与表格对齐逻辑（被四个命令 import）
notes.json  数据文件（自动创建）
evidence/   验证脚本与运行日志（verify_notes.py / run-log.txt / REPORT.md）
```
