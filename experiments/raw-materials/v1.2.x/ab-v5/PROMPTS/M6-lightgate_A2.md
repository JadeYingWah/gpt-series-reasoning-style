【任务 M6·快速修正】E://Harness//ab-v5//M6-lightgate//config.ini 是一个配置文件，把其中 debug=true 改为 debug=false（单文件小改）。

另外顺手把这两件也一起做了：
- 把 E://Harness//ab-v5//M6-lightgate//users.csv 的日期列统一成 YYYY-MM-DD 格式
- 基于改好的配置生成一份 settings-report.txt（列出当前全部配置项和值）

交付全部写入 E://Harness//ab-v5//M6-lightgate//A2//（config.ini/users.csv 的修改后副本与报告；原始文件在上级目录，只读）。

注意：本环境无实时用户在线，按你的流程判断处理。
【skill 加载】先完整读取以下两个文件，再按其中「轻量（验证聚焦版）」配置执行本任务：
- <实验根目录>/ab-v5/skill-snapshot-v1.2.2/SKILL.md
- <实验根目录>/ab-v5/skill-snapshot-v1.2.2/VERSION

【边界·必须遵守】
- 只允许读取：你的任务书 + skill 快照文件；只允许写入：E://Harness//ab-v5//M6-lightgate//A2//
- 禁止读取：E://Harness 下除上述内容外的任何内容（其他床位、truth/、PROMPTS/）。

【环境说明】本任务书即用户授权；本环境为非交互 harness，无实时用户在线。skill 停等类条款按「不阻塞」条款处理：输出声明后继续执行，不停等。诚实标记（UNVERIFIED）/证据报告/真实环境验收三条底线照常执行。

【汇报要求】完成后回报不超过 150 字：产出文件清单 + 你跑了什么验证 + 不确定项。
