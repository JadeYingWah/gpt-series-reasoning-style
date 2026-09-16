# 300 题 A/B 长测协议（两阶段 A 臂）

## 方法修正（总指挥 2026-09-12）

**禁止**把 skill 全文 + 任务一次性塞给子智能体。  
A 臂必须 **两阶段**：先只读 skill 并输出加载证明，再执行任务（理解缓冲）。

## A 臂协议

### 阶段 1 · 只读加载（禁止实现）

1. 读 `<skill安装目录> 与 `VERSION`
2. 在床位写 `load-proof.md`：版本号、逐字硬规则第一条、协作架构一句、已读文件列表
3. **不要**创建业务产物

### 阶段 2 · 实现

1. 读本目录 `task.md`
2. 按 skill 执行；门禁若适用则写在 `response.md` 或 `gate.md`
3. 完成门：磁盘清单 + 实跑/核对 + UNVERIFIED

## B 臂协议

- **禁止**读取 `<skill安装目录> 任何文件
- 只读本目录 `task.md` 并实现
- `response.md` 写核对记录；测不了的写 UNVERIFIED

## 任务池（本轮生成 45 床）

| 类 | 数 | 判定 |
| --- | ---: | --- |
| SVG 创意（新颖动物×载具） | 15 | 验收清单 |
| SE slugify 修复（M4） | 15 | unittest RED→GREEN |
| Widget 番茄钟 | 15 | 清单 + 源码可核 |

后续向 300 扩：同法复制任务变体 + 视情况引入 Terminal-Bench 式本地 harness。

## 判分（0–2 × 4 维）

门禁记录 · 证据 · 诚实 · 结果质量。B 门禁 N/A。

## 进度

见 `_judge/progress.json`：`done_pairs` / `target_pairs`（150 对 = 300 臂任务）。
