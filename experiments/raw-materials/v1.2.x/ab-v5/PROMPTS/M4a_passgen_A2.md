【任务 M4a·密码生成器（第一阶段）】交付一个命令行密码生成器 genpass.py。

第一阶段范围（本轮只做这些）：
- python genpass.py [长度] 生成随机密码（含大小写+数字+符号，长度默认 16、范围 8-64，超界给友好提示）
- 密码写入 passwords.log（明文演示用），含时间戳

交付物（写入 E://Harness//ab-v5//M4-resume//workspace//）：
- genpass.py + README.md（当前已实现功能）
- 本目录需 git init 并完成首次 commit（本环境 git 可用，用户名/邮箱随意如 dev@local）
- 说明：扩展功能（如密码强度评级、剪贴板）留待下轮，本轮不做

【skill 加载】先完整读取以下两个文件，再按其中「轻量（验证聚焦版）」配置执行本任务：
- <实验根目录>/ab-v5/skill-snapshot-v1.2.2/SKILL.md
- <实验根目录>/ab-v5/skill-snapshot-v1.2.2/VERSION

【边界·必须遵守】
- 只允许读取：你的任务书 + skill 快照文件；只允许写入：E://Harness//ab-v5//M4-resume//workspace//
- 禁止读取：E://Harness 下除上述内容外的任何内容（其他床位、truth/、PROMPTS/）。

【环境说明】本任务书即用户授权；本环境为非交互 harness，无实时用户在线。skill 停等类条款按「不阻塞」条款处理：输出声明后继续执行，不停等。诚实标记（UNVERIFIED）/证据报告/真实环境验收三条底线照常执行。

【汇报要求】完成后回报不超过 150 字：产出文件清单 + 你跑了什么验证 + 不确定项。
