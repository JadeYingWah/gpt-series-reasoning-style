# 项目结构

```
GPT-series-reasoning-style-Local GitHub repository/
├── gpt-series-reasoning-style/     # 主仓库（main分支）—— skill本体
│   ├── SKILL.md                    # 门禁文件（很薄，只加载入口和共存规则）
│   ├── DISCIPLINE.md               # 交付纪律全文（五阶段+C1/C2+加载规则）
│   ├── VERSION                     # 当前版本号
│   ├── CHANGELOG.md                # 版本变更记录
│   ├── REFERENCE.md                # 完整说明书（中文版）
│   ├── README.md                   # GitHub首页（中英文双语）
│   ├── LICENSE                     # MIT许可证
│   ├── AGENTS.md                   # 全局代理配置
│   ├── SECURITY.md                 # 安全政策
│   ├── assets/                     # 静态资源（social-preview.svg/png等）
│   ├── references/                 # 分阶段规则文件
│   │   ├── plan-rules.md           # 阶段2：规划规则
│   │   ├── review-rules.md         # 阶段5：验收规则
│   │   └── multi-agent.md          # 多智能体协作规则
│   ├── scripts/                    # 验证脚本
│   ├── templates/                  # 模板文件
│   ├── docs/                       # 文档
│   └── .github/                    # GitHub Actions配置
│
├── experiments/                    # 实验分支 —— 双臂对照实验与测试床
│   ├── README.md                   # 实验总览
│   ├── raw-materials/              # 原始实验素材
│   │   ├── furuan-fried-rice-2026-09-18/   # 弗糯糯炒饭双臂对照
│   │   └── ...
│   ├── test-bed1-light-tasks/      # 轻量任务测试床
│   ├── test-bed2-medium-tasks/     # 中等任务测试床
│   ├── test-bed3-creative-task/    # 创意任务测试床
│   ├── test-bed4-creative-complex-task/  # 复杂创意任务测试床
│   ├── historical-v1.2.x/          # 历史版本存档
│   ├── docs/                       # 实验文档
│   ├── assets/                     # 实验素材
│   └── stats-experiments.py        # 统计脚本
│
└── gpt-series-reasoning-style-workspace/   # 工作区 —— 迭代过程中的草稿与提案
    ├── proposals/                  # 新功能提案
    ├── test-beds/                  # 临时测试床
    ├── backups/                    # 备份
    ├── releases/                   # 发布草稿
    ├── peers/                      # 竞品对比
    ├── docs/                       # 工作文档
    └── HANDOFF-2026-09-10-给新任AI.md  # 交接文档
```

## 三个目录的分工

| 目录 | 用途 | 对应分支 |
|------|------|----------|
| `gpt-series-reasoning-style/` | 正式发布的skill本体，面向用户 | main |
| `experiments/` | 双臂对照实验、测试床、历史版本存档 | experiments |
| `gpt-series-reasoning-style-workspace/` | 迭代过程中的草稿、提案、临时文件，不对外 | （本地工作区，不提交） |

---

## 上架平台投递记录

### 已上架/已提交

| 平台 | 链接 | 状态 | 提交时间 | 备注 |
|------|------|------|----------|------|
| GitHub | https://github.com/JadeYingWah/gpt-series-reasoning-style | ✅ 已发布 v1.6.0 | 2026-09-19 | 主仓库，Release已打tag |
| Skillstore | https://skillstore.io/zh-hans/skills/jadeyingwah-gpt-series-reasoning-style | ✅ 已上架 | 2026-09-18 | 90分精选💎 |
| Cursor Marketplace | https://cursor.com/marketplace/publish | ⏳ 审核中 | 2026-09-19 | 已提交申请表单 |
| SkillHub（腾讯云） | https://skillhub.cn/ | ⏳ 安全审核中 | 2026-09-19 | 已上传v3版本zip |
| ComposioHQ/awesome-claude-skills | PR #1935 | ⏳ PR审核中 | 2026-09-19 | 26k+ stars的awesome列表 |

### 计划提交/未提交

| 平台 | 状态 | 原因 |
|------|------|------|
| anthropics/skills | ❌ 不提交 | 官方仓库894个PR排队，通过率极低，中文skill不匹配 |
| Claude Plugin Marketplace | ❌ 不提交 | 需要Team/Enterprise组织权限，个人用户提交不了 |
| ClawHub | ⏸️ 暂缓 | OpenClaw生态匹配度一般 |
| skills.sh (Vercel) | ✅ 自动收录 | 基于GitHub仓库和npm下载量，不用手动提交 |
| claudemarketplaces.com | ✅ 自动收录 | 自动从GitHub抓取，不用手动提交 |
