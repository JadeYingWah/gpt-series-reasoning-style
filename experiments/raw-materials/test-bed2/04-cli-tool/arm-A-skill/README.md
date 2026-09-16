# glit — Git-lite 版本控制工具

一个教学向的 Git 精简实现：内容寻址对象库 + 快照式提交模型 + 轻量分支。
纯 Python 3 标准库实现（零第三方依赖），约 900 行代码 + 80 个测试用例。

## 支持的命令

| 命令 | 说明 |
|------|------|
| `glit init [path]` | 初始化仓库（默认分支 `main`） |
| `glit add <path>...` | 暂存文件/目录（递归；已跟踪文件被删除后再 add 即 stage 删除） |
| `glit commit -m <msg>` | 提交暂存快照（`--author` 可覆盖作者） |
| `glit log [--oneline]` | 沿 parent 链查看历史（新→旧） |
| `glit diff [--staged]` | 默认：工作区 vs 暂存区；`--staged`：暂存区 vs HEAD |
| `glit checkout <branch>` | 切换分支（快照式切换） |
| `glit branch [name] [-d]` | 列出 / 创建 / 删除分支 |

退出码：`0` 成功；`1` 业务错误（或 diff 存在差异）；`2` 参数错误（argparse）。

## 对象存储格式（自定义）

```
header  = b"GLIT"(4B magic) + version(1B=1) + type(1B) + payload_len(4B big-endian)
full    = header + payload
sha     = sha1(full).hexdigest()          # 头部参与哈希 → 同内容不同类型必不同名
stored  = zlib.compress(full, 9)
落盘    = .glit/objects/<sha[:2]>/<sha[2:]>
```

对象类型：`1=blob`（原始字节）、`2=tree`（目录快照 JSON，entries 按 UTF-8 字节序
排序保证跨平台确定性）、`3=commit`（元数据 JSON）。

**完整性保证**：读取时全量校验 magic / 版本 / 长度 / SHA-1，任何损坏立即抛
`ObjectCorrupted`（测试 `test_objects.py` 用篡改注入验证了每一层校验都会触发）。

## 仓库布局

```
<repo>/
  .glit/
    objects/<2位>/<38位>   对象库（内容寻址，相同内容自动去重）
    HEAD                   "ref: refs/heads/main"
    refs/heads/<branch>    分支引用（内容 = commit sha）
    index.json             暂存区 {"version":1,"entries":{path: blob_sha}}
```

## 快速上手

```bash
# 在项目根目录（确保 glit 包在 PYTHONPATH 或当前目录）
python -m glit init
python -m glit add .            # 递归暂存（自动排除 .glit、__pycache__）
python -m glit commit -m "initial"
python -m glit log --oneline
python -m glit diff             # 改动后查看；有差异时退出码 1
python -m glit branch dev
python -m glit checkout dev
```

## 设计决策（有意与 git 不同的部分）

- **checkout 保守安全策略**：跟踪文件有未提交修改/删除、或目标分支会覆盖
  未跟踪文件时，直接拒绝切换（git 会尝试合并，本实现不合并）。提示先 commit。
- **不跟踪空目录**：tree 只记录文件；切换后变空的目录会被清理。
- **不做 detached HEAD / 合并 / 远程**：`parents` 至多 1 个，历史为单链。
- **换行不做转换**：blob 忠实存字节（不做 autocrlf）。
- **路径统一 posix 风格存储**，Windows 磁盘操作时才转换分隔符。

## 运行测试

```bash
python -m unittest discover -s tests -t . -v
```

80 个用例，覆盖：对象 roundtrip 与四种损坏注入、仓库结构、add/commit 正常与
异常路径、树构建确定性、log 格式、diff 双模式与二进制、分支生命周期、checkout
安全策略与分支隔离、`python -m glit` 子进程级端到端与退出码。

测试有效性验证记录（变异测试）：①写路径哈希改用 payload（写读不一致）→
27 红 + 9 错；②禁用 checkout 脏区检查 → 精确命中对应 2 个测试。两处变异
均被套件击杀，还原后全绿。

## 目录结构

```
glit/
  objects.py     对象存储（写/读/哈希/四层校验）
  repo.py        仓库定位、HEAD、refs、分支名校验
  index.py       暂存区读写、路径规范化
  treebuild.py   index → 嵌套 tree；tree/commit → 扁平映射
  commit.py      commit 对象读写
  commands.py    init / add / commit / log / branch
  diff.py        工作区/index/HEAD 两两 diff（unified 格式）
  checkout.py    分支切换（安全检查 + 快照落盘）
  cli.py         argparse 入口与统一错误处理
tests/           7 个测试模块 + 共享 helper
```
