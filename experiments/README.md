# experiments · 实验数据分支

<img src="assets/social-preview.svg" alt="GPT-Series Reasoning Style · 交付纪律层 v1.6.0" width="100%">

本分支只存放 **gpt-series-reasoning-style** 的实验数据与产物。skill 本体在 [main 分支](https://github.com/JadeYingWah/gpt-series-reasoning-style)——本分支不含 skill 代码。

横幅图与 main 同步至 **v1.6.0**（门禁动作化 · 执行面无规则 · 交付标 C1/C2 · GPT行为蒸馏总览）。

## 目录

- `raw-materials/ww-dmg-table-2026-09-18/` — **鸣潮伤害验算表 · v1.5.6 单臂**（C1；变异+Python 交叉；候选池 W1）
- `raw-materials/minigame-starcatch-2026-09-18/` — **星光接取 · v1.5.6 实测**（A档方向卡；逻辑 24/24；C1）
- `raw-materials/fishing-3d-2026-09-18/` — **3D 钓鱼 · 口供级回收**（C1；**产物本体未在本机检出**，仅 REPORT）
- `raw-materials/my3dgame-2026-09-18/` — **Neon Void 证据层**（My3DGame artifacts；质量上限讨论源头）
- `raw-materials/desktop-beds-2026-09-17/` — **2026-09-17 全天八组实验素材**
  - `abab-feibi-a/` — 菲比啾比钓鱼（带 skill v1.5.2 · A 臂）
  - `amns-three-games-b/` — 三游戏（无 skill · B 臂：bat 启动器，2/3 无法启动的对照臂）
  - `heji-three-games-a/` — 三游戏 exe 直启版（带 skill v1.5.1 · A 臂）
  - `4399-ab-skill/` — 4399 四游戏（带 skill v1.5.3 · A 臂：贪吃蛇/打地鼠/2048/小鸟）
  - `4399-b-noskill/` — 4399 四游戏 + 大厅（无 skill · B 臂：含 WebAudio 音效）
  - `form2-morph2-pomodoro/` — 番茄钟（形态二 · 子智能体首测）
  - `finreport-morph3/` — 个人财务月度套件（形态三 · 大型项目首测：数据源+仪表盘+报告+验证脚本）
  - `duotai-morph3-txt/` — 三 txt 算式（形态三真跑：任务疑点拦截首例）
  - `GROUPS.md` — **实验分组总表**（A/B 定义、证据位置、结果、回访口供索引）与**单案例候选池**（两案例立法制）
- `historical-v1.2.x/` — v1.2.x 时代对照实验报告
- `test-bed1~4/` — 早期测试场数据
- `assets/` — 分支横幅图（svg/png）

## 关键结果速览

| 对照 | A（带 skill） | B（无 skill） |
|------|--------------|--------------|
| **2026-09-18 · v1.5.6 单臂包** | 鸣潮验算表：21/21+交叉+变异，**C1**；星光接取：24/24+C1；钓鱼/Neon Void：口供或证据层 **C1** | —（本日无双臂） |
| 4399 四游戏 | 选题查证+确认+主角实现；验证近乎满分 | 静默丢弃任务核心词；**声称"实测可玩"未经过程背书** |
| 三游戏（exe 化） | **3/3 双击直启** | bat 依赖环境，**2/3 无法启动** |
| 问答双臂 | 平手 | 平手（→问答条款撤销） |

- 2026-09-17 分组与口供：`raw-materials/desktop-beds-2026-09-17/GROUPS.md`
- 2026-09-18 回收包：各目录 `REPORT.md`；**钓鱼产物缺盘**已在 fishing REPORT 如实记录

## Skillstore / 分发状态（维护备忘）

| 项 | 值（查阅 skillstore.io 时） |
|---|---|
| 商店页 | https://skillstore.io/zh-hans/skills/jadeyingwah-gpt-series-reasoning-style |
| 商店所载作者版本 | **v1.6.0**（内容修订 r6；90分精选） |
| GitHub 本体 | main 已是 **v1.6.0**（门禁动作化 + C1/C2 + GPT行为蒸馏总览） |
| 含义 | 商店已同步至 v1.6.0；后续更新需重新提交仓库URL触发审核 |

## 说明

- 本分支素材脱敏惯例：用户名 → `<username>`；公开前再扫绝对路径
- 主仓库 main 只含 skill 本体；clone main 不拉实验数据
- 原始桌面目录保留在实验机本地
