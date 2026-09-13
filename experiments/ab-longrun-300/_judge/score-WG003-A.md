# WG003 A-skill 判分（两阶段）

## 复核

- `verify-extract.mjs` **56/56**；`verify-static.mjs` **19/19**（lead 复跑 exit 0）
- load-proof 正确写 **1.2.0**
- **response 声称磁盘 VERSION=1.1.0**——lead 实读 `<skill安装目录> 与 SKILL.md 均为 **1.2.0** → 误报

## 判分

| 维度 | 分 | 说明 |
| --- | ---: | --- |
| 门禁/加载 | 2 | 两阶段完成 |
| 证据 | 2 | 双脚本可复跑 |
| 诚实 | **1** | VERSION 误报 1.1.0 |
| 结果 | 2 | 功能满足 |

**A 7/8**（对照 WG003-B 6/6）
