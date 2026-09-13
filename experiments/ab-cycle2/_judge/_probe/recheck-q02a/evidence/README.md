# evidence/ — 验证证据与复算工装

本目录是 `app.html` 的**可复算验证证据**，不是运行时垃圾（按 skill 工作流第 6 步：证据产物留在交付目录）。

## 一键复算

```bash
cd <本目录的上一级>
node evidence/verify.mjs --app "$PWD/app.html" --label app        # 29 项验证，exit 0 = 全过
node evidence/mutants.mjs                                        # 10 个变异体杀伤实验
node evidence/trace-physics.mjs "$PWD/app.html"                  # 逐物理步插桩（诊断用）
```

环境要求：Node ≥ 20（用到全局 `WebSocket`/`fetch`）、本机 Chrome。可用 `CHROME=<路径>` 覆盖浏览器位置。
无需 `npm install`（零第三方依赖，直接用 CDP over WebSocket 驱动 Chrome headless）。

## 各文件说明

| 文件 | 作用 |
| --- | --- |
| `verify.mjs` | 主验证工装。29 项检查（S1~S2 静态、C1~C24 运行时），真实 Chrome + `file://`，结果写 `results-<label>.json`，全过 exit 0 |
| `mutants.mjs` | 变异杀伤实验。对 `app.html` 逐点注入单点缺陷（独立副本，原产物只读），用同一工装跑每个变异体，验证工装**真的会红** |
| `trace-physics.mjs` | 逐物理步插桩器：打印每一步的位置/速度/砖块数/状态，用于定位物理偏差 |
| `results-app.json` | 冻结产物的一次完整验证结果（29 项逐条 pass + 证据字段） |
| `mutants/mXX.html` | 变异体副本（每个只含单点缺陷） |
| `mutant-results/mXX.json` | 每个变异体的逐项结果；被杀死的用例即 `pass:false` 的那些 |
| `mutation-summary.json` | 杀伤率汇总：每个变异体死了哪些用例、是否达到预期 |
| `shots/*.png` | 实操过程中的真实截图（开局/运行中/暂停/结束/重开/通关/超长文本） |
| `run-all.log` | 最近一次"全量验证 + 变异实验"的完整 stdout 留痕 |

## 关键设计（为什么这份证据可复算）

1. **真实环境**：Chrome headless + CDP，`file://` 直接打开单文件产物，走真实 `requestAnimationFrame`、真实 DOM、真实 Canvas。
2. **物理用例确定性**：所有物理断言在**单次 `Runtime.evaluate` 内同步完成**（JS 单线程，rAF 无法插入），并复用页面内同一条物理代码路径 `__breakout.simulate(ms)`，因此任何第三方重跑都得到同一结果。
3. **互动用例真实输入**：键盘走 `Input.dispatchKeyEvent`、鼠标走 `Input.dispatchMouseEvent`、按钮走真实 `.click()`，不是直接改内部变量。
4. **异常全程捕获**：`window.onerror` + `unhandledrejection` + CDP `Runtime.exceptionThrown` + `Log.entryAdded` 四路并行，任一非空即判失败。
5. **扫描器自证**：静态扫描（无 CDN/无网络）先用人工构造的已知靶子证明正则真的能命中（`S1b`），否则"0 命中"不构成证据。
6. **测错文件防护**：每次导航后核验 `location.pathname` 与目标产物一致。
7. **工装鉴别力自证**：`mutants.mjs` 以杀伤率而非通过率证明这套验证有效；变异点要求**恰好命中 1 次**，命中 0 次或 >1 次直接判定实验无效（避免 `replace` 只改第一处造成"假存活"——该缺陷在首轮实验中真实发生过并被捕获）。

## 已知局限

- 全部运行在 **Chrome headless**（Windows）。未在 Firefox/Safari、真机触屏、iOS/Android 上跑过 → 这些面 `UNVERIFIED`。
- 帧率/内存数字是 headless 环境下的实测值，不等价于用户机器上的数值。
- 变异实验只覆盖 10 个单点缺陷；不构成"无其它缺陷"的证明，只证明本工装对这 10 类缺陷有杀伤力。
