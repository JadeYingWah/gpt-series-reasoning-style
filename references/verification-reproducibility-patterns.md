# 验证可复算性最佳实践（Verification Reproducibility Patterns）

> **定位**：本文件是参考示例，不是强制规则。执行者可自愿参考其中的模式来提升验证脚本的可复算性。是否采用、采用哪些，由执行者根据任务风险自行判断。
>
> **来源**：v1.2.3 修订验证实验（2026-09-13）中三份 submission 的实测对比——可复算性工程质量与产物可靠性正相关，但强制化在强模型上边际效益为负。故以 reference 形式沉淀，不升级为硬指标。

---

## 一、什么是"可复算性"

验证脚本的可复算性 = **第三方在干净环境中，不依赖执行者的本地状态，能独立运行验证脚本并得到与证据报告一致的结果**。

可复算性解决的问题：
- 执行者声称"测试全绿"，但第三方跑不起来（缺依赖、缺输入文件、硬编码路径）
- 验证脚本有副作用（覆写证据文件、修改系统状态），重复运行结果不一致
- 验证脚本依赖执行者的环境变量、缓存、未声明的输入

---

## 二、已验证有效的模式

### 模式1：`--parser` 参数指向任意副本

**问题**：验证脚本硬编码 `import csv_parser`，只能在交付目录内运行，第三方复制到其他目录就 ModuleNotFoundError。

**解法**：验证脚本接受 `--parser <path>` 参数，动态加载被验证的模块。

```python
# verify.py
import argparse, importlib.util, sys, tempfile, os

def load_parser(path):
    spec = importlib.util.spec_from_file_location("parser_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["parser_under_test"] = module
    spec.loader.exec_module(module)
    return module

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--parser", default="csv_parser.py", help="path to parser under test")
    args = ap.parse_args()
    parser = load_parser(args.parser)
    # ... run tests against parser
```

**效果**：第三方可以把验证脚本复制到任意目录，用 `--parser /path/to/copy/csv_parser.py` 指向任意副本，实现真正的独立复算。

### 模式2：tempfile 零副作用

**问题**：验证脚本在当前目录生成临时文件（测试用CSV、变异体副本），运行后残留，或更糟——覆写交付目录中的证据文件。

**解法**：所有临时文件用 `tempfile.TemporaryDirectory()`，用完即删。

```python
import tempfile, os

with tempfile.TemporaryDirectory() as tmpdir:
    test_file = os.path.join(tmpdir, "test.csv")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("a,b,c\n1,2,3\n")
    result = parser.parse(test_file)
    assert result == [["a","b","c"], ["1","2","3"]]
# tmpdir 自动清理，无残留
```

**额外防护**：在脚本顶部设置 `sys.dont_write_bytecode = True`，避免生成 `__pycache__`。

### 模式3：复算说明三要素

**问题**：证据报告只说"测试全绿"，第三方不知道怎么跑、跑什么、预期什么。

**解法**：证据报告中包含复算说明，三要素：

1. **环境要求**：Python 版本、依赖（仅标准库 / requirements.txt）、平台注意事项
2. **运行命令**：精确到可复制粘贴的命令，如 `python verify.py --parser csv_parser.py`
3. **预期输出**：退出码（0=全过）、关键输出行（如 `85/85 passed`）、失败时的表现

```markdown
## 复算说明

- 环境：Python 3.8+，仅标准库（csv/os/sys/tempfile/importlib），无 pip 依赖
- 命令：`python verify.py --parser csv_parser.py`
- 预期：退出码 0，输出末尾 `85/85 passed, 0 failed`
- 失败：退出码 1，输出失败用例名与断言详情
```

### 模式4：变异体独立文件 + 锚点 assert

**问题**：变异测试用字符串替换修改源码，但不保存变异体文件，第三方无法独立复算；或者变异体是"改变量名"这种无效变异，测试变红但没有鉴别力。

**解法**：
- 每个变异体写成独立文件（`mutant_m1.py`），保存在 `evidence/mutants/` 目录
- 变异体必须是**语义变异**（修改逻辑，如移除BOM处理、移除转义处理），不是语法变异（改变量名、加空格）
- 每个变异体有**锚点 assert**：明确指出哪个测试用例应该因为这个变异而失败

```python
# mutate_and_check.py
MUTATIONS = [
    {"id": "m1_bom_removed", "desc": "移除BOM跳过逻辑", "anchor_test": "test_bom_skip"},
    {"id": "m2_cr_removed", "desc": "移除\\r行尾处理", "anchor_test": "test_cr_line_endings"},
    # ...
]
```

**反模式**：MUTATOR-BROKEN——如果某个变异体的锚点测试没有失败，显式声明 `MUTATOR-BROKEN: 变异体m3未被test_xx捕获，可能是变异无效或测试覆盖不足`，不要假装全捕获。

---

## 三、常见错误（实测发现）

### 错误1：硬编码 sys.path 指向交付目录之外

**表现**：验证脚本第二行写 `sys.path.insert(0, r"C:\Users\executor\project\deliverable")`，第三方运行时 ModuleNotFoundError。

**后果**：违反"一键运行完全相同结果"的保证，可复算性为0。

**修复**：用相对路径或 `--parser` 参数（模式1），不要硬编码绝对路径。

### 错误2：验证脚本覆写证据文件

**表现**：`test_csv_parser.py` 运行时把测试结果写入 `evidence/test_report.txt`，第三方复跑时覆盖了原始证据。

**后果**：证据被污染，无法对比"原始运行"和"复算运行"的差异。

**修复**：测试输出写到 stdout 或 tempfile（模式2），不要覆写交付目录中的证据文件。如果必须写文件，写到 `evidence/rerun-report.txt` 并注明是复算产物。

### 错误3：测试输入依赖外部文件

**表现**：测试用例从 `data/test_cases.csv` 读取，但该文件不在交付目录中，或路径是相对路径但第三方的cwd不同。

**后果**：第三方运行时 FileNotFoundError。

**修复**：测试输入硬编码为字符串常量（`csv_content = "a,b\n1,2\n"`），或确保输入文件在交付目录中且用 `os.path.dirname(__file__)` 构建相对路径。

### 错误4：声称"独立交叉验证"但未附脚本

**表现**：证据报告说"与Python标准库csv.reader交叉验证30项一致"，但没有附交叉验证脚本。

**后果**：第三方无法复算，只能信任执行者的声称——这正是skill要避免的"宣称了但没附脚本"。

**修复**：交叉验证脚本必须在交付目录中（如 `evidence/oracle_check.py`），可复算说明中包含运行命令。

---

## 四、可复算性自检清单

执行者在交付前可自愿对照：

- [ ] 验证脚本是否只依赖标准库或已声明的 requirements.txt？
- [ ] 验证脚本是否可以在交付目录之外运行（用 `--parser` 或相对路径）？
- [ ] 所有临时文件是否用 tempfile，运行后无残留？
- [ ] 验证脚本是否不覆写交付目录中的证据文件？
- [ ] 测试输入是硬编码字符串还是交付目录内的文件？
- [ ] 证据报告是否包含复算说明三要素（环境/命令/预期输出）？
- [ ] 变异体是否是语义变异（不是改变量名）？是否有锚点 assert？
- [ ] 声称的"独立交叉验证"是否附了可运行的脚本？

> 注意：以上是自检清单，不是强制要求。简单任务可以只做其中几项，高风险任务建议全做。

---

## 五、实验依据

本文件的模式与错误均来自 2026-09-13 v1.2.3 修订验证实验的三份 submission 实测：

| submission | 可复算性工程 | 实测结果 |
|---|---|---|
| v1.2.3-draft（34号） | 最佳：`--parser` 参数 + tempfile零副作用 + 复算说明三要素 | 第三方干净环境一键复算 29/29 通过 |
| v1.2.2-rerun（89号） | 良好：相对路径 + tempfile自清理 + CLI显式编码 | 第三方复跑 85/85 通过，但需注意 PYTHONUTF8 |
| v1.2.2原对照（22号） | 有破绽：bug_sweep.py 硬编码sys.path指向交付目录之外 + test_csv_parser.py 覆写 evidence/test_report.txt | 主测试可复算，但 bug_sweep 第三方 ModuleNotFoundError |

**结论**：可复算性工程质量与产物可靠性正相关，但将其强制为硬指标在强模型上边际效益为负（强模型自发已做到大部分）。故以 reference 形式沉淀，供执行者自愿参考。

---

*本文件为参考示例，不构成强制规则。引用时注明来源：references/verification-reproducibility-patterns.md。*
