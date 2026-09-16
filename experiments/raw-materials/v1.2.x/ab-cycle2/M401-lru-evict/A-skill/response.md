# response.md — M401-lru-evict · A 臂 · 阶段 2（实现）

- 床号：M401-lru-evict（A 臂 · 带 skill）
- 阶段：阶段 2 · 实现
- 运行时环境：Windows，`python --version` → `Python 3.13.14`
- 执行者：单 Agent 主干（规划/执行/审查面由同一 Agent 切换）

---

## 0. 门禁与授权（一句摘要）

实现前已输出【实现前确认】（风险分档＝中/偏轻、形态＝单 Agent 主干、资源盘点含 `OrderedDict` 作参考模型等），
因本床无用户在场，按 team-lead 的显式工作令与显式委托「按你自己判断推进」记录授权后继续（skill 明文：显式委托记录决定后即可继续）。
**未**读取 `B-noskill\` 目录；**未**读取机器上任何其他 skill 安装目录。

---

## 1. 磁盘清单（实际产出 / 改动）

| 文件 | 状态 | 大小 | sha256（前 16 位） |
|---|---|---|---|
| `<实验根目录>\ab-cycle2\M401-lru-evict\A-skill\lru_cache.py` | **修改**（交付物） | 1171 B | `5fcabd6d5eeaceab` |
| `<实验根目录>\ab-cycle2\M401-lru-evict\A-skill\verify_lru.py` | **新增**（验证脚本/证据产物） | 6881 B | `90dd16b630e691a5` |
| `<实验根目录>\ab-cycle2\M401-lru-evict\A-skill\response.md` | **新增**（本文件） | — | — |
| `<实验根目录>\ab-cycle2\M401-lru-evict\A-skill\task.md` | 未改动 | 738 B | — |
| `<实验根目录>\ab-cycle2\M401-lru-evict\A-skill\load-proof.md` | 未改动（阶段 1 产物） | 1022 B | — |

改动内容（`lru_cache.py`，共 4 处）：

1. `put()` 淘汰对象：`self.order[-1]` → `self.order[0]`，并 `remove` 改 `pop(0)`（取最久未使用者，修正淘汰顺序反了）；
2. `get()` 命中时把 key 移到 `order` 末尾（刷新使用顺序）；
3. `put()` 命中已有 key 时同样刷新 `order` 位置（原代码只更新值、不刷新顺序）；
4. 新增最小护栏：`capacity <= 0` 时 `put()` 为 no-op（原代码在 cap=0 时 `order[-1]` 会 `IndexError`）。

公开接口名与签名**未变**（见 §3 探针）。

---

## 2. 实际跑过的验证（命令 / 输入 / 输出摘要，第三方可复算）

### 2.1 主验证脚本

```
命令： python "<实验根目录>/ab-cycle2/M401-lru-evict/A-skill/verify_lru.py"
退出码：0
```

输入构成：7 个功能用例 + 1 个差分随机测试（seed=12345, steps=3000, cap=3, keymax=6），
对**修复版**与**原始缺陷版**（脚本内逐字复刻阶段 1 读到的原始代码，类名 `BuggyLRUCache`）跑**同一批断言**。

输出摘要（逐字）：

```
== 修复版 LRUCache · 功能用例 ==
  PASS  case_task_scenario
  PASS  case_evict_pure
  PASS  case_get_refreshes
  PASS  case_put_existing_refreshes
  PASS  case_capacity_one
  PASS  case_capacity_zero_no_crash
  PASS  case_miss_returns_none
  小计: 7/7 通过
== 修复版 LRUCache 差分测试 (seed=12345, steps=3000, cap=3, keymax=6) ==
  差分一致（返回值 / 键集合 / 使用顺序 全部与 oracle 相同）

== 原始缺陷版 BuggyLRUCache · 同一批断言（应判红） ==
  PASS  case_task_scenario
  FAIL  case_evict_pure -> AssertionError:
  FAIL  case_get_refreshes -> AssertionError:
  PASS  case_put_existing_refreshes
  PASS  case_capacity_one
  FAIL  case_capacity_zero_no_crash -> IndexError: list index out of range
  PASS  case_miss_returns_none
  小计: 4/7 通过
== 原始缺陷版 BuggyLRUCache 差分测试 ==
  DIFF-FAIL（如期判红）: step=12 get(1): got=None exp=449
杀伤率（缺陷版被判红的检查数 / 总检查数）: 4/8
修复版全过: True
结论: 通过（修复版 7/7 + 差分一致；缺陷版被判红 4/8，验证有鉴别力）
```

**鉴别力（杀伤率）说明**：本验证不是「7/7 全过」就交差——同一批断言施加到缺陷版上被判红 4/8，
说明这套检查拿得动「淘汰顺序反了 / get 不刷新顺序 / cap≤0 崩溃」这组要防的错误。

### 2.2 按 task.md 原文序列直接复算

```
命令： cd A-skill && python -c "from lru_cache import LRUCache; c=LRUCache(2); c.put(1,'a'); c.put(2,'b'); print(c.get(1)); c.put(3,'c'); print(c.get(2)); print(c.get(1)); print(c.get(3)); print(c.order)"
输出： get(1)= a / get(2)= None / get(1)= a / get(3)= c / order= [1, 3]
```
与 task.md 的期望一致：访问过的 2 被淘汰（返回 `None`），刚访问过的 1 保留。

### 2.3 接口与边界探针

```
命令： cd A-skill && python -c "<inspect.signature + 边界探针>"
输出：
  __init__ (self, capacity)
  get (self, key)
  put (self, key, value)
  cap=-1 -> None {}
  cap=2 put 1,2,3 -> data {2: 2, 3: 3} order [2, 3]
  cap=1000 fill -> size 1000
```
接口签名与原始完全一致；负容量不崩溃；纯写入场景正确淘汰最久未用者 1。

---

## 3. 重要发现：task.md 自述的复现序列**不具鉴别力**（与验收目标直接相关，如实上报）

task.md 称：`put(1);put(2);get(1);put(3)` 后「实际却仍返回 2 的原值，而刚被访问过的 1 反而丢失」。

实测**否证**了这段描述：把 task.md 的原始代码原样运行该序列，结果是 `get(2) is None`、`get(1) == 'a'`
（即缺陷版通过的正是期望结果）。原因：`get` 不刷新顺序时 `order == [1, 2]`，`order[-1]` 恰好是 2，
"错选 MRU" 与 "正选 LRU" 在本序列上**结果巧合相同**（`order` 保持 `[1,3]`，两版一致）。

- 该序列**无法**区分修复版与缺陷版；
- 真正能判红缺陷版的是：纯写入淘汰（`case_evict_pure`）、get 刷新顺序（`case_get_refreshes`）、`cap<=0`（`case_capacity_zero`）与差分测试。
- 我按 task.md 的**目标表述**（「让淘汰严格遵循最近最少使用语义，并保证 get 命中会更新使用顺序」）与**期望结果**（`get(2)` 返回 `None`）实现；两版在该序列上对期望结果无分歧，故不构成实现方向冲突。

该发现已固化进 `verify_lru.py` 的输出（脚本会显式打印此注），第三方复算即可见。

---

## 4. 不确定项（如实标注）

- `UNVERIFIED`：本修复**未**在多有并发/多线程场景下验证线程安全（原实现即非线程安全，任务未要求，未扩大范围）。
- `UNVERIFIED`：`verify_lru.py` 的差分测试只覆盖 `cap=3, keymax=6, seed=12345, steps=3000` 一种参数组合与单一种子；未做多种子/多容量矩阵。理由：该组合已能判红缺陷版（有鉴别力），扩矩阵属范围外增益。
- `UNVERIFIED`：`capacity <= 0` 的护栏是我**主动增加**的行为（原代码在此输入下崩溃）。任务未明确规定该边界语义，我按「无容量＝不缓存」的通用 LRU 语义选择 no-op；若验收方另有定义，此项需回归。
- 交付目录内**未**创建 `B-noskill` 相关任何读取痕迹；此点已有 §0 声明，但无法用磁盘产物自证「未读」，仅以声明为准。

---

## 5. 考虑过的方向与取舍

| 方向 | 取舍 |
|---|---|
| 最小修正：保留 `data`(dict) + `order`(list)，只改淘汰索引 + 补 get/put 刷新 | **采用**。改动面最小、不新增依赖、接口与属性形态完全不变 |
| 用 `collections.OrderedDict.move_to_end` 重写 | 否。更简洁，但改动面大、暴露的数据结构与属性语义会变，超出「修缺陷 + 接口不变」的范围 |
| 只改 `order[-1] → order[0]`，不动 `get` | 否。修不全——任务明确要求 get 命中刷新顺序，否则纯读场景仍会淘汰错 |
| 保留 `order[-1]` 但把 `order` 语义反转（最新在头部） | 否。等价但会改动属性语义与注释约定，收益为零、风险更高 |

---

## 6. 收尾自评（用户视角整体重看）

- 交付物在用户眼里成立吗：改动是一份可直接 `from lru_cache import LRUCache` 使用的修复版；跑一次 `verify_lru.py` 即得可复算结论。
- 有无奇怪/多余/缺失：`verify_lru.py` 与 `response.md` 是证据产物，非运行时垃圾，符合 skill「证据留交付目录」约定；无多余重构（未动 `task.md`/`load-proof.md`）。
- 逐项操作通过 ≠ 结果合理：因此额外做了 §3 的鉴别力核查（缺陷版必须判红）与 §3 的 task.md 描述一致性核查（发现描述与代码不符），并如实上报。
