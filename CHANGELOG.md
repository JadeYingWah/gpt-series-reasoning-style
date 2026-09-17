# Changelog

本项目的重要变更按版本记录。格式参考 [Keep a Changelog](https://keepachangelog.com/)，版本号遵循 [Semantic Versioning](https://semver.org/)。

## [1.5.1] - 2026-09-17

### Added
- 阶段1（自由构想）构想要点实质化：显式列出构想要点，计划阶段逐条回应并核验。
- CI：GitHub Actions 在每次推送时运行 `scripts/selfcheck.py`（24 项静态检查）。
- `CHANGELOG.md`、`assets/` 目录（预览图迁入）。

### Changed
- 模糊条款四条修补：
  - 阶段4（直觉检查）发现疑点当场确认或修掉，不带进阶段5。
  - "真打开看一眼"类型扩展：游戏、报告、SVG 动画等视觉产物纳入真打开范围。
  - "全绿不算证据"对非代码任务给出降级路径：查证记录本身即等价于"断言变红"。
  - 调研设上界：陌生概念至多 5 分钟 / 3 次搜索，不无限查下去。
- "小且可逆"补可操作判定标准（从零新建、创意交付物不算小且可逆）；调研改由"陌生度"触发（不认识的概念/名字先问用户或搜索，不编造设定）。
- 补全 SKILL.md frontmatter：`license`、`compatibility`、`metadata.author`。

## [1.5.0] - 2026-09-16

### 重构
- **物理隔离版**：规则从常驻 `SKILL.md` 拆到外部文件（`references/plan-rules.md`、`references/review-rules.md`、`references/multi-agent.md`），执行期规则文件完全不在上下文中。
- 五阶段时序：①自由构想 → ②规则规划 → ③执行 → ④直觉检查 → ⑤纪律检查。
- 任务交付后，模型从上下文中遗忘三个规则文件的具体内容，仅保留"五阶段"骨架。
- 配套 `scripts/selfcheck.py`（24 项静态自检）。

### Removed
- v1.2.x 重型版本的 77 条自检、硬指标化规则（经 A/B 实验证伪：规则越多评分反而越低）。

## [1.2.5] 及更早

实验期版本，未单独维护 changelog。演进过程与实验证据见 `REFERENCE.md` 与 GitHub Release。
