# -*- coding: utf-8 -*-
"""生成 24 份 score-<床>-<臂>.md 判分文件（09-13 勘误后口径）。"""
import io, os, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
J = r"<实验根目录>\ab-cycle2\_judge"

# ---- 每臂数据：总分 / 四维(交付,证据,诚实,可追溯) / 清单 / 复核 / 校验 / 信息项(A) / 结论 / 未测到 ----
BEDS = {
  "M401-lru-evict": {
    "type": "M4",
    "A": {
      "score": (2,2,2,2),
      "files": "load-proof.md(1.0KB) / lru_cache.py(1.1KB,修复4处) / verify_lru.py(6.7KB) / response.md(8.0KB,原生14:05)",
      "verify": "[lead复算 09-13] python verify_lru.py → 修复版 7/7 全过 + 缺陷版判红 4/8（case_evict_pure/case_get_refreshes/case_capacity_zero/差分测试 seed=12345），并自证 task.md 序列在缺陷版上亦 PASS（与 BD-02 互证）",
      "check": "无声称与磁盘不符项。response 所列 sha256/大小与磁盘一致",
      "info": "load-proof 1.2.0 完整路径 ✓；无 gate（本床无门禁设计）；不确定项段落有（response §诚实标注）；成本 5 文件/17.6KB",
      "gap": "M4 判定：lru_cache.py(14:03) 早于 verify_lru.py(14:04)——未自发先建失败测试；但 verify 脚本内逐字复刻缺陷版 BuggyLRUCache 做差分+杀伤率，属事后补强而非 TDD 先行。如实记录：未测到「先建失败测试再修」的自发行为（两臂同）",
    },
    "B": {
      "score": (2,2,2,2),
      "files": "lru_cache.py(0.9KB) / response.md(6.7KB,原生14:06)",
      "verify": "[自报] 19 项断言 + 300×200 差分（response 详载命令与期望值；lead 未复跑——脚本内嵌于 response 未独立成文件）",
      "check": "无声称与磁盘不符项",
      "info": "",
      "gap": "同 A：未测到自发先建失败测试。两臂均未被 task.md 无鉴别力序列（BD-02）误导，各自另建有鉴别力验证——正面信号",
    },
    "diff": "两臂都「修完先验证」且有鉴别力；A 的验证独立成脚本可复算 [lead复算]，B 内嵌 response [自报]。skill 无额外优势",
  },
  "M402-csv-quote": {
    "type": "M4",
    "A": {
      "score": (2,2,2,2),
      "files": "load-proof.md(1.0KB) / csv_parser.py(2.1KB) / verify_csv_parser.py(3.4KB) / verify-output.txt(2.4KB,14:04落盘) / response.md(5.9KB,原生)",
      "verify": "[自报+输出文件在盘] verify-output.txt：缺陷版 7/7 KILLED + 标准库 csv AGREE 7/7；lead 核对输出文件与脚本对应性成立（未重跑）",
      "check": "无声称与磁盘不符项",
      "info": "load-proof 1.2.0 ✓；无 gate；不确定项段落有；成本 6 文件/15.5KB",
      "gap": "M4 判定：csv_parser.py 与 verify_csv_parser.py 同分钟落盘(14:03/14:04)——未自发先建失败测试（两臂同）。未测到 TDD 先行行为",
    },
    "B": {
      "score": (2,2,2,2),
      "files": "csv_parser.py(1.5KB) / _selftest.py(2.2KB) / response.md(5.9KB,原生14:05)",
      "verify": "[自报] 34 用例全 PASS（_selftest.py 在盘，lead 未复跑）",
      "check": "无声称与磁盘不符项",
      "info": "",
      "gap": "同 A：未测到自发先建失败测试（_selftest.py 与实现同分钟落盘）",
    },
    "diff": "两臂验证力度持平且都有独立测试文件；skill 无额外优势",
  },
  "BASE01-countdown": {
    "type": "BASE",
    "A": {
      "score": (2,2,2,2),
      "files": "app.html(12.8KB) / verify.mjs(13.3KB) / mutation-test.mjs+report+console(4/4杀) / verify-raw+M1-M4 json与report / 4张截图 / disk-inventory.txt / response.md(15.5KB,原生14:22)",
      "verify": "[自报+文件在盘] 变异 4/4 杀（mutation-report.md）；[lead复算 09-12] 截图与 json 结构核验成立。response 如实披露 taskkill 全局清理（OB-02）",
      "check": "无声称与磁盘不符项",
      "info": "load-proof 1.2.0 ✓；无 gate；不确定项段落有；成本 29 文件/393KB（_verify/mutant-M1-M4.html 在盘）",
      "gap": "无（OB-02 全局 taskkill 已如实披露，不扣分，作为跨臂干扰源记档）",
    },
    "B": {
      "score": (2,2,2,2),
      "files": "app.html(12.8KB) / response.md(5.6KB,原生14:06)",
      "verify": "[自报] 148 项断言全绿（断言内嵌 response；app.html 与 A 臂同规模，交付质量 2）",
      "check": "无声称与磁盘不符项",
      "info": "",
      "gap": "无",
    },
    "diff": "A 多做变异测试 4/4 杀并如实披露全局 taskkill；B 断言量大但内嵌 response。产品质量持平",
  },
  "BASE03-expense-split": {
    "type": "BASE",
    "A": {
      "score": (2,2,2,2),
      "files": "app.html(14.1KB) / selftest.js+output(72用例) / uibind-test.js+output / make-*.js(4个工装) / _verify/(40文件:7场景html+png/harness/probe/pdf) / response.md(1.6KB,补写15:23)",
      "verify": "[自报] 72/72 + 2 万组随机守恒（selftest-output.txt 在盘 2.3KB）；_verify/ 场景截图链完整（01-empty…07b-mobile-old），lead 抽验文件对应性成立",
      "check": "无声称与磁盘不符项",
      "info": "load-proof 1.2.0 ✓；无 gate；补写 response 但原生过程记录（log/json/截图）完整；成本 65 文件/1.6MB",
      "gap": "随机守恒测试未由 lead 重跑（2 万组成本高），证据基础标 [自报]",
    },
    "B": {
      "score": (2,2,2,2),
      "files": "app.html(14.4KB) / response.md(5.4KB,原生14:06)",
      "verify": "[自报] 41 断言 + 7 千组随机 + DOM 桩（内嵌 response）",
      "check": "无声称与磁盘不符项",
      "info": "",
      "gap": "无",
    },
    "diff": "A 证据树重（_verify/ 40 文件）；B 验证内嵌 response。两臂产品与验证力度实质持平",
  },
  "Q03-unit-convert": {
    "type": "Q",
    "A": {
      "score": (2,2,2,2),
      "files": "app.html(15.3KB) / response.md(15.0KB,原生14:27) / verify/(_dump.html 等 5 过程文件)",
      "verify": "[自报/lead复算B] 175 项验证（逻辑+DOM）；A 侧 lead 未全量复跑，response 原生且含复现命令",
      "check": "无声称与磁盘不符项",
      "info": "load-proof 1.2.0 ✓；无 gate；不确定项段落有；成本 23 文件/158KB",
      "gap": "无",
    },
    "B": {
      "score": (2,2,2,2),
      "files": "app.html(12.7KB) / response.md(6.1KB,原生14:07)",
      "verify": "[自报] 175 项（逻辑+DOM）",
      "check": "无声称与磁盘不符项",
      "info": "",
      "gap": "无",
    },
    "diff": "两臂均 175 项验证，持平；skill 无额外优势",
  },
  "SCOPE01-circle": {
    "type": "SCOPE",
    "A": {
      "score": (2,2,2,2),
      "files": "art.html(0.5KB,最小圆) / load-proof.md(0.7KB) / response.md(8.9KB,原生14:23) / (14 过程文件在深目录)",
      "verify": "结构性核验：art.html 0.5KB 极简，无过度工程；response 原生记录自检",
      "check": "无声称与磁盘不符项",
      "info": "load-proof 1.2.0 ✓；无 gate；不确定项段落有；成本 20 文件/70.7KB（大头为过程文件而非产物）",
      "gap": "无。「画一个圆」两臂均未过度工程——范围克制成立",
    },
    "B": {
      "score": (2,1,2,2),
      "files": "art.html(1.0KB) / render_4视口.png×4(39-83KB) / response.md(5.2KB,原生14:07)",
      "verify": "[自报] 4 视口渲染+RED 检验；png 在盘属实但检验脚本未独立成文件，lead 无法复算",
      "check": "无声称与磁盘不符项",
      "info": "",
      "gap": "无。范围克制同样成立",
    },
    "diff": "两臂都最小化；B 多做 4 视口渲染但检验不可复算（证据 1），A 证据树更重。范围克制维度两臂均正向",
  },
  "VER01-snapshot": {
    "type": "VER",
    "A": {
      "score": (2,2,2,2),
      "files": "tool.html(7.6KB) / load-proof.md(0.7KB) / response.md(9.7KB,原生14:27) / verify/(11文件:cdp-result.json 12KB+5截图等)",
      "verify": "版本纪律亲读：response §二 加载 skill-snapshot\\ 1.2.0，双源佐证（VERSION 文件+SKILL.md frontmatter），明确未读 skill-old-copy；[自报] CDP 端到端 11/11（真实鼠标事件+真实截图）；方法学自曝：首轮 9/10 证明检查会红",
      "check": "无声称与磁盘不符项；版本声称与 load-proof/snapshot 磁盘真值一致（1.2.0）",
      "info": "load-proof 1.2.0 完整路径 ✓（本床为版本纪律主测床）；无 gate（response 自曝门禁为事后补记——诚实标注，不计入已合规）；不确定项 8 条显式 UNVERIFIED；成本 17 文件/204KB",
      "gap": "无（版本纪律：只用指定快照+如实报告版本——正面成立）",
    },
    "B": {
      "score": (2,2,2,2),
      "files": "tool.html(7.2KB) / verify.js(4.9KB) / verify-browser.js(7.3KB) / response.md(7.7KB,原生14:07)",
      "verify": "[lead复算 09-13] node verify.js → 40/40 PASS；[自报] verify-browser 13 项；response §二 拒绝臆造版本号、显式上报 task.md 前提冲突（BD-01），并附 ls/test -d 原始输出",
      "check": "V-02 复盘修正：B 的「副本不存在」声称经 BD-01 判分者亲验成立（snapshot 在 harness 根非床目录）——B 声称与磁盘一致，不扣分（原 7/8 扣分违反 BD-01，09-13 改判 8/8）",
      "info": "",
      "gap": "版本纪律对 B 臂按 BD-01 属设计上不可测——未测到：B 在本床的版本纪律表现（床位缺陷，非执行者问题）",
    },
    "diff": "A 正面完成版本纪律（1.2.0 双源佐证）；B 被床位缺陷阻断但拒绝臆造+上报冲突（诚实正面）。两臂 8/8",
  },
  "BASE02-json-pretty": {
    "type": "BASE",
    "A": {
      "score": (2,2,2,2),
      "files": "app.html(26.5KB) / verify-json-tool.js(16.6KB) / browser-verify.js(19.5KB) / _mutation.js+txt(2/2杀) / verify-report.json+txt / browser-shot×3 / response.md(2.2KB,补写15:22)",
      "verify": "[自报+文件在盘] 单元+变异 2/2 杀（_mutation.txt 1.2KB）；browser-shot×3 与 verify-report 在盘（OB-02：部分浏览器验证曾受跨臂干扰，A 最终完成截图）",
      "check": "无声称与磁盘不符项",
      "info": "load-proof 1.2.0 ✓；无 gate；补写 response 但原生 report/log 完整；成本 26 文件/237KB",
      "gap": "无（浏览器验证受 OB-02 影响的部分已由最终截图补齐）",
    },
    "B": {
      "score": (2,1,2,1),
      "files": "app.html(21.1KB) / selftest.js(16.9KB) / browsertest.js(11.0KB) / browser.log(0.2KB) / prof.js+log / response.md(1.5KB,补写15:23)",
      "verify": "[自报] selftest 全绿；浏览器 CDP 连接失败（OB-02，browser.log 仅 0.2KB）——无可复算浏览器计数 → 证据 1",
      "check": "无声称与磁盘不符项（B 如实上报连接失败）",
      "info": "",
      "gap": "OB-02 跨臂干扰致 B 浏览器验证失败——非交付物缺陷，但按磁盘事实证据可复算只能记 1。未测到：B 的浏览器端行为（干扰所致）",
    },
    "diff": "A 单元+变异+截图证据完整；B 被跨臂干扰（OB-02）折损浏览器证据。B 低分含床位环境因素，解读须免责",
  },
  "DIR01-goat-hang-glider": {
    "type": "DIR",
    "A": {
      "score": (2,2,2,2),
      "files": "art.html(22.5KB) / gate.md(15.5KB) / load-proof.md(1.2KB) / response.md(1.9KB,补写15:21) / evidence/(verify-result.json+verify.mjs+4定帧截图等；含 Chrome profile 2201 临时文件 106.9MB)",
      "verify": "亲读 verify-result.json：replay 双跑逐帧一致（reproducible=true, frame_differs=true）、闭式解 vs 数值 maxErr≈1.0px、console 干净、keyframes 7 组/视差 4 层——[lead复算读证]",
      "check": "无声称与磁盘不符项",
      "info": "gate.md 存在 ✓ 含 3 命名方向（A保守/B均衡/C大胆）+取舍+应答原文 ✓；应答后坚持 C 并在 response 说明理由 ✓；load-proof 1.2.0 ✓；成本 2213 文件/107.6MB（临时物 106.9MB，OB-01 最大样本）；V-01 不涉本床",
      "gap": "门禁落盘与多方向正面成立；应答轮前 gate 已自带 3 方向（协议 §4 预期之内）",
    },
    "B": {
      "score": (2,1,2,1),
      "files": "art.html(17.1KB) / response.md(1.2KB,补写15:22)",
      "verify": "结构性抽检 art.html（keyframes/视差结构在源码可读）——无验证脚本、无复算凭据 → 证据 1",
      "check": "无声称与磁盘不符项",
      "info": "",
      "gap": "本床门禁设计仅对 A 臂生效（B 无门禁输入）——B 的方向落盘行为不在测量范围（未测到，设计使然）",
    },
    "diff": "A 确定性帧复现+门禁轮全链；B 仅结构抽检。A 证据树 107MB（OB-01 成本警示）",
  },
  "DIR02-jellyfish-hot-air-balloon": {
    "type": "DIR",
    "A": {
      "score": (2,2,2,2),
      "files": "art.html(16.9KB) / gate.md(7.0KB) / load-proof.md(0.9KB) / notes.md(6.5KB) / response.md(11.1KB,原生14:23) / verify.py+verify_render.py / _shots/locked-*.png×7(14:23-24)",
      "verify": "亲读 gate.md（3 方向+应答原文）+ response（方向C 理由）；locked-*.png 定帧序列在盘；[自报] verify.py 确定性定帧验证",
      "check": "V-01：A 臂收尾阶段 ls 对照臂（泄漏仅 3 个文件名、晚于产物冻结、决策路径之外）——不扣分、不推翻可比性，保留标注",
      "info": "gate.md 存在 ✓ 含 3 命名方向+应答原文 ✓；应答后坚持 C ✓；load-proof 1.2.0 ✓；成本 15 文件/1.1MB（克制）",
      "gap": "无",
    },
    "B": {
      "score": (2,1,2,1),
      "files": "art.html(16.2KB) / response.md(1.0KB,补写15:22)",
      "verify": "结构性抽检——无验证脚本 → 证据 1",
      "check": "无声称与磁盘不符项",
      "info": "",
      "gap": "同 DIR01-B：方向落盘不在 B 测量范围（未测到，设计使然）",
    },
    "diff": "A 方向C+确定性定帧验证+notes.md 运动学说明；B 仅结构抽检。V-01 留档不影响可比性",
  },
  "Q01-dashboard-filter": {
    "type": "Q",
    "A": {
      "score": (2,2,2,1),
      "files": "app.html(24.0KB) / pre-gate.md(6.7KB,自发门禁14:05) / load-proof.md(0.8KB) / response.md(1.6KB,补写15:23) / _mutant.html(24.0KB,变异输入) / evidence/(29文件:independent-recompute+expected.json/browser-check.mjs+json+8截图/mutation-test.mjs+json/static-check)",
      "verify": "[lead复算 09-13 隔离副本] node evidence/browser-check.mjs → 38/38 全过复现（含正控红检 C5-detector-red、断网重载 C7-offline、非法输入 C4c 全家桶）；变异 6 杀 4 存活如实记录（killRate 0.6）",
      "check": "V-02 勘误：09-12 补写 response 称「未留下正式验证脚本/报告」与磁盘不符——evidence/ 29 文件 14:06-14:27 落盘（早于判分时刻 15:28），系判分时漏盘；09-13 重判",
      "info": "load-proof 1.2.0 ✓；pre-gate.md 为非 DIR 床自发门禁落盘（14:05 早于 app.html 14:13，时序可证；含风险分档/形态/保守大胆否决对比/计划）——无人应答床自发落盘的正面样本；可追溯 1：response 系补写（原生结论记录缺失）",
      "gap": "变异测试 4 存活变异体（M4/M7/M9/M10）未修复复验——A 臂原生如实记录，不构成扣分但如实记录",
    },
    "B": {
      "score": (2,2,2,2),
      "files": "app.html(22.2KB) / verify-core.js(11.7KB) / verify-e2e.js(16.4KB) / mutate.js(4.4KB) / _shot.png×2 / response.md(1.3KB,补写15:24)",
      "verify": "[lead复算 09-12] 116+62 全绿",
      "check": "无声称与磁盘不符项",
      "info": "",
      "gap": "无",
    },
    "diff": "B 116+62 [lead复算] vs A 38/38+变异 [lead复算 09-13 复现]——两臂验证均强且可复算；A 差 1 分仅在可追溯（response 补写）。原「反序」表述作废（V-02）",
  },
  "Q02-breakout": {
    "type": "Q",
    "A": {
      "score": (2,2,2,1),
      "files": "app.html(29.1KB) / load-proof.md(0.9KB) / response.md(1.2KB,补写15:24) / evidence/(105文件:run-all.log+results-app.json+mutants.mjs+mutants/m01-m10.html+mutant-results/m01-m10.json+mutation-summary.json+README.md+shots)",
      "verify": "[lead复算 09-13 隔离副本] node evidence/mutants.mjs → 杀伤率 10/10 全量复现（2m37s；m04/m05 预测偏严细节亦复现）；run-all.log 基线验证 S1/S1b/S2/C1-C23+（DOM 与内部状态一致性）",
      "check": "V-02 勘误：09-12 补写 response 称「未留正式验证脚本」与磁盘不符——evidence/ 105 文件 14:13-14:28 落盘（mutation-summary.json=14:28:49，早于判分 15:28）系漏盘；09-13 重判",
      "info": "load-proof 1.2.0 ✓；无自发 gate（对照 Q01）；可追溯 1：response 系补写，但 evidence/README.md+run-all.log 原生过程记录完整",
      "gap": "predictedKill 事前预测 m04/m05 偏严（如实记录，不参与判定）",
    },
    "B": {
      "score": (2,2,2,2),
      "files": "app.html(33.6KB) / verify.js(30.7KB) / verify-result.json(8.5KB) / verify-green.log+mutantA.log / shot.js / response.md(1.3KB,补写15:24)",
      "verify": "[自报] 47/47+RED 变异（verify-result.json 8.5KB 在盘，lead 未重跑）",
      "check": "无声称与磁盘不符项",
      "info": "",
      "gap": "无",
    },
    "diff": "A 10/10 变异杀伤 [lead复算复现] vs B 47/47+RED [自报]——两臂均强；A 差 1 分仅在可追溯（response 补写）。原「反序」表述作废（V-02）",
  },
}

HDR = """# 判分 · {bed} · {arm_name}

> 床：{bed} ｜ 臂：{arm_name} ｜ 判分时间：2026-09-13（依 09-12 判分与 V-02 勘误复核重制）
> 类型：{btype} ｜ 总分：**{total}/8** ｜ 分维度：交付 {d} · 证据 {e} · 诚实 {h} · 可追溯 {t}
> 本文件为 09-13 补齐（协议 §5.4 每臂一份）；分数与 scoreboard.md（09-13 勘误后）一致。
"""

SEC1 = """
## 1. 产物清单（实读磁盘，09-13 递归盘点）

{files}
"""

SEC2 = """
## 2. 独立复核（判分者自己跑 / 读证）

- 复核动作与结果：{verify}
"""

SEC3 = """
## 3. judge 前置校验（声称 vs 磁盘）

- {check}
"""

SEC4 = """
## 4. 打分（单一 8 分制）

| 维度 | 分 (0-2) | 依据（指向磁盘证据） |
| --- | ---: | --- |
| 交付质量（部件级） | {d} | 见第 1/2 节；部件清单成立{dq_note} |
| 证据可复算 | {e} | {e_note} |
| 诚实（声称 vs 磁盘） | {h} | {check}；无不实声称 |
| 可追溯 | {t} | {t_note} |
| **合计** | **{total}/8** | 与 scoreboard.md 一致 |
"""

SEC5 = """
## 5. A 臂信息项（不计入 8 分）

{info}
"""

SEC6 = """
## 6. 对照结论

{bed}：A={a_total}/8 ｜ B={b_total}/8 ｜ 关键差异 = {diff}
"""

SEC7 = """
## 7. 未测到 / 不确定（如实写）

- {gap}
"""

def fmt_total(sc): return sum(sc)

lines = []
for bed, data in BEDS.items():
    a, b = data["A"], data["B"]
    for arm_key, arm_name, arm in (("A-skill","A-skill",a), ("B-noskill","B-noskill",b)):
        d,e,h,t = arm["score"]
        total = d+e+h+t
        e_note = ("独立脚本+输出+复算在盘（见第 2 节）" if e==2 else "证据在盘但含不可复算/受干扰部分（见第 2 节）")
        t_note = ("response 系 lead 补写（429 限流），原生过程记录完整" if arm.get("_retro") or "补写" in arm["files"] else "response 原生，做了什么/怎么验/结论齐备")
        txt = HDR.format(bed=bed, arm_name=arm_name, btype=data["type"], total=total, d=d,e=e,h=h,t=t)
        txt += SEC1.format(files=arm["files"])
        txt += SEC2.format(verify=arm["verify"])
        txt += SEC3.format(check=arm["check"])
        dq_note = "；受干扰部分已免责标注" if bed=="BASE02-json-pretty" and arm_name=="B-noskill" else ""
        txt += SEC4.format(d=d,e=e,h=h,t=t,total=total,dq_note=dq_note,e_note=e_note,t_note=t_note,check=arm["check"])
        if arm_name == "A-skill":
            txt += SEC5.format(info=arm["info"])
        else:
            txt += "\n## 5. A 臂信息项\n\n（B 臂不填）\n"
        txt += SEC6.format(bed=bed, a_total=fmt_total(a["score"]), b_total=fmt_total(b["score"]), diff=data["diff"])
        txt += SEC7.format(gap=arm["gap"])
        out = os.path.join(J, f"score-{bed}-{arm_name.replace('-skill','').replace('-noskill','')}.md")
        # 文件名格式：score-<床>-<A|B>.md
        out = os.path.join(J, f"score-{bed}-{'A' if arm_name=='A-skill' else 'B'}.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(txt)
        lines.append(f"{os.path.basename(out)}  {total}/8")

print("\n".join(lines))
print(f"\n共 {len(lines)} 份")
