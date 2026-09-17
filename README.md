# experiments · 实验数据分支

本分支只存放 **gpt-series-reasoning-style** 的实验数据与产物。skill 本体在 [main 分支](https://github.com/JadeYingWah/gpt-series-reasoning-style)——本分支不含 skill 代码。

## 目录

- `raw-materials/desktop-beds-2026-09-17/` — **2026-09-17 全天八组实验素材**（本分支最新收录）
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

## 关键结果速览（2026-09-17）

| 对照 | A（带 skill） | B（无 skill） |
|------|--------------|--------------|
| 4399 四游戏 | 选题查证+确认+主角实现；验证近乎满分 | 静默丢弃任务核心词；**声称“实测可玩”未经过程背书** |
| 三游戏（exe 化） | **3/3 双击直启**（环境依赖消灭在交付里） | bat 依赖用户环境，**2/3 无法启动** |
| 问答双臂 | 平手 | 平手（→问答条款撤销） |

- 完整分组定义与回访口供见 `raw-materials/desktop-beds-2026-09-17/GROUPS.md`。

## 说明

- 本分支素材已脱敏（用户名 → `<username>`）；主仓库 main 只含 skill 本体，clone main 不拉实验数据
- 原始桌面目录均保留在实验机本地
