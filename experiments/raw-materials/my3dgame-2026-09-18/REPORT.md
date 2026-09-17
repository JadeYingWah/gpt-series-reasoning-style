# Neon Void（My3DGame）· skill 早期实测证据回收（2026-09-18）

| 项 | 值 |
|---|---|
| 类型 | **单臂** · 从零新建 3D 游戏（skill 质量上限讨论的源头任务） |
| skill | 会话早期为 **v1.5.5 门禁版**（3D 游戏任务）；讨论后演进至 1.5.6 |
| 产物本机 | 桌面 `My3DGame/`（完整工程含 node_modules，**不入仓**） |
| 本目录 | 仅 `artifacts/` 证据层（设计契约 + final-evidence + pass 截图） |

## 证据摘要（artifacts/final-evidence.md）

- 构建：`npm run build` tsc+vite OK；bundle ~619kB JS
- 运行：`npm run dev` → `http://127.0.0.1:5188`
- Playwright：**6 passed**（desktop + mobile；start→move→fire→victory→restart 等）
- Canvas inspector pass-4：桌面/移动 active-play 与 complete 均 nonblank，无 console 错误
- Known limitations（原文）：非 AAA premium；移动端为 Chromium 仿真；音效 pitch 用 Math.random

## 与 skill 讨论的关联（方法论，非 A/B）

本任务触发了本会话后续对 skill 的系统讨论：

1. 「可验收 ≠ 出色」——纪律逼出证据，不逼出手感
2. A 档隐含质量封顶 → 1.5.6 plan-rules「不锁定质量上限」
3. 完成定义 → C1/C2
4. 创意期是否挂 skill → 用法：创意段可不加载，验收再挂

## 完成档位（当时口径）

- 交付物当时未统一使用 C1/C2 字样（1.5.5 阶段）
- 按 1.5.6 口径回看：应标 **C1**；产品档未拉满（玩法/视觉上限待用户）

## 限制

- 完整源码不入 experiments 分支（体积与依赖）；以 Desktop 目录 + 本 artifacts 为准
- 非双臂对照，不作 A/B 结论

*回收：主会话 2026-09-18*
