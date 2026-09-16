# GitLite

一个用 Python 实现的迷你版本控制系统（Git 的教学级简化版），拥有**自己的内容寻址对象存储格式**，无需任何第三方依赖。

```
python -m gitlite init / add / commit / log / diff / checkout / branch
```

## 功能总览

| 命令 | 说明 |
|------|------|
| `gitlite init [dir]` | 创建空仓库（幂等），默认分支 `main` |
| `gitlite add <path>...` | 暂存文件/目录（`.` 为全部；已跟踪文件的删除也会被暂存） |
| `gitlite commit -m <msg>` | 把暂存区记录为一次提交（parent 链；空提交被拒绝） |
| `gitlite log [branch\|hash]` | 沿 parent 链倒序查看历史 |
| `gitlite diff` | 工作区 vs 暂存区（untracked 文件不显示，同 git） |
| `gitlite diff --staged` | 暂存区 vs HEAD |
| `gitlite checkout <branch>` | 切换分支（同步工作区 + index） |
| `gitlite checkout <hash>` | 检出提交（分离 HEAD，支持 ≥4 位哈希前缀） |
| `gitlite checkout -- <path>...` | 从暂存区恢复工作区文件 |
| `gitlite branch` | 列出分支（`*` 标记当前分支） |
| `gitlite branch <name>` | 创建分支 |
| `gitlite branch -d <name>` | 删除分支（要求已完全合并，即目标是当前 HEAD 的祖先） |
| `gitlite branch -D <name>` | 强制删除分支 |

作者身份从环境变量读取：`GITLITE_AUTHOR_NAME` / `GITLITE_AUTHOR_EMAIL`（缺省 `GitLite User <gitlite@example.com>`）。

## 对象存储格式（自有设计，灵感来自 Git）

每个对象 = `头部 + 载荷`：

```
<type> <payload-size>\n<payload>
```

- **oid** = `sha256(完整对象字节)`，内容寻址：内容相同 ⇒ oid 相同 ⇒ 自动去重，读取时哈希强校验（可发现损坏）。
- **落盘**：zlib 压缩后写 `<repo>/.gitlite/objects/<oid前2位>/<oid其余>`（与 Git 相同的两级分桶，但哈希是 SHA-256 而非 SHA-1）。
- **blob**：文件内容原样字节（二进制安全，全链路 bytes，不做换行转换）。
- **tree**：目录快照，每行 `<mode> <oid> <name>\n`，按名称字典序（确定性 ⇒ 同内容树同 oid）。`100644`=文件，`40000`=子目录，嵌套构建。
- **commit**：`tree` / `parent`(0..n) / `author` / `committer` 头 + 空行 + message。author 形如 `Name <email> <unix-ts> <+0800>`。
- **index（暂存区）**：`<repo>/.gitlite/index`，JSON：`{version, entries: {posix相对路径: {oid, mode}}}`。
- **HEAD**：`ref: refs/heads/main`（符号引用）或裸 commit oid（分离 HEAD）。

## 架构

```
gitlite/
├── objects.py     对象序列化/反序列化、ObjectStore（落盘/读取/前缀查询）、tree/commit 编解码
├── index.py       暂存区（JSON 持久化，原子写）
├── repository.py  仓库定位（向上找 .gitlite）、init、HEAD/refs、tree 展开、
│                  按扁平路径映射构建嵌套 tree、祖先判定、检出同步（checkout_sync）
├── diff.py        手写 Myers O(ND) diff（无 difflib）+ unified hunk 生成
├── commands.py    七个命令的业务实现
└── cli.py         argparse 入口与统一错误处理（业务错误 -> stderr + 退出码 1）
```

**diff 算法**：先裁剪公共前后缀，再对核心部分跑 Myers 最短编辑脚本，回溯出完整路径点列后转 opcodes，最后按 3 行上下文合并生成 `@@` hunk（行号语义与 GNU diff 一致，含 `\ No newline at end of file` 标记；含 NUL 字节的文件输出 `Binary files ... differ`）。

## checkout 的安全规则（保守策略）

与 git 相比刻意更严格——任一条件不满足即拒绝切换：

1. 工作区存在未暂存修改（工作区 ≠ index）→ 拒绝；
2. 存在已暂存未提交的变更（index ≠ HEAD 快照）→ 拒绝（避免暂存内容被静默丢弃）；
3. 目标快照要新建的文件与工作区 untracked 文件内容冲突 → 拒绝。

切换时：删除目标快照中不存在的已跟踪文件（并清理空目录）、写回差异文件、index 重置为目标快照、更新 HEAD。

## 与真实 Git 的主要差异

- 无 merge / rebase / stash / tag / remote；commit 无 merge commit（单 parent）。
- 分支切换不允许携带任何未提交状态（git 容忍与切换无关的局部修改）。
- 无 .gitignore；`add .` 会暂存所有文件（.gitlite 自身除外）。
- 文本 diff 假定 UTF-8（无法解码的字节以替换符显示）。

## 安装与运行

需要 Python ≥ 3.9，零依赖：

```bash
# 直接运行
python -m gitlite --help

# 或安装为命令行工具
pip install .
gitlite init
```

## 运行测试

```bash
# 在项目根目录
python -m unittest discover -s . -p "test_*.py" -v
```

测试共 76 个，覆盖：

- **对象层**：序列化往返、分桶落盘、内容去重、前缀查询、损坏检测（哈希不匹配）、tree/commit 编解码与确定性；
- **diff 层**：opcodes 性质校验（无缝衔接/坐标覆盖/等段内容一致）、前后缀裁剪、hunk 头行号语义（新增/删除文件的 `-0,0`/`+0,0` 间隙规则）、无换行符标记、多 hunk 分裂；
- **命令层**：add（递归/删除暂存/越界拒绝）、commit（空提交拒绝/parent 链/分离 HEAD 提交警告）、log（顺序/指定分支/空仓库）、diff（工作区/暂存/删除/二进制不适用场景）、branch（创建/列表/合并检查删除）、checkout（分支往返文件状态/安全规则三条/文件恢复/分离 HEAD）、嵌套目录 tree 往返；
- **CLI 端到端**：子进程跑真实命令行，覆盖完整工作流、退出码、参数错误、仓库子目录内运行。
