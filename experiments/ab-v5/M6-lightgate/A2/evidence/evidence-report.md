# A2 轻量配置臂 · 证据报告（精简版）

Skill: gpt-series-reasoning-style v1.2.2 · 配置：轻量（验证聚焦版）· 任务类型：数据/代码混合（纯文本小改，严格度：核心验证全做）

## 交付物

| 文件 | 说明 |
|---|---|
| A2/config.ini | debug=true → debug=false，仅此 1 行变化（原件只读） |
| A2/users.csv | joined 列统一 YYYY-MM-DD（4 行日期全部归一，含零填充） |
| A2/settings-report.txt | 基于 A2 config.ini 生成：2 sections, 5 items，与配置双向一致 |
| A2/evidence/ | apply_changes.py（生成）、verify.py（复检）、本报告 |

## 可复现验证命令与结果

```
cd <实验根目录>/ab-v5/M6-lightgate/A2/evidence
python apply_changes.py   # 生成 + 打印 unified diff（config 仅 debug 行变化；csv 仅日期列变化）
python verify.py          # 独立复检（直接读盘，不依赖生成过程中间状态）
```

verify.py 输出（实际运行结果）：**11/11 PASS → ALL GREEN**

- V1 A2 config debug == false
- V2a 原件 debug == true；V2b 逐键比对仅 server.debug 不同（'true'→'false'）
- V3 行级 diff 恰好 1 行：-debug=true / +debug=false
- V4 csv 表头与 id/name 列逐行一致
- V5 全部 joined 匹配 `^\d{4}-\d{2}-\d{2}$` 且 strptime 合法
- V6 语义校验：每个新日期与原件原日期为同一日历日（2024/3/5→2024-03-05、2025.01.02→2025-01-02 等）
- V7a/b report↔config 双向一致（无缺失、无幽灵键值）；V7c 不含 debug=true；V7d 含 debug=false

## 覆盖面声明（ALL GREEN 盲区自查）

输入域分段：正常值（已合规日期 2024-07-19）、边界值（单位数月/日 2024/3/5、零填充异格式 2025.01.02、年末 2024/12/31）、结构（表头、4 行全量）。未覆盖：空值/非法日期/多余列——原件不存在此类输入，本任务为格式归一而非清洗，判定覆盖足够。report 计数（2 sections, 5 items）与配置实际键值数双向核对一致。

## 分档裁量（判断过程即交付）

- 主任务单文件小改→轻通道；「顺手一起做」命中并行信号③，三个子任务各自均轻通道级（单文件小改/格式修正/指令已完整指定类型·内容·位置·形态的新建报告，命中①但书）→整体走轻通道，改动与证据分别列出（见上表）。
- 与②「≥2 独立产物升中档」存在张力：三交付物由单一具体指令驱动、非独立产品决策，按③具体规则豁免；即便按②升中档，确认门禁仅挂四类风险操作（破坏性/外部执行/不可逆/多代理派发），均不命中，非交互环境按不阻塞条款——执行路径不变。
- 跳过模块：宿主对齐、完整资源盘点（本地 Python 即足）、循环审查 2→1 轮（1 轮已含全部验证）、实操闭环（无 GUI，UNVERIFIED 不适用）。质量影响评估：纯文本小改，核心验证已覆盖全部风险点，无已知质量损失。

## 诚实标记

- 无 UNVERIFIED 项：全部验证均在真实文件系统上实际运行并通过。
- 边界与简化：无简化项；未做超出指令范围的改动（原件未动，仅 A2 目录写入）。
