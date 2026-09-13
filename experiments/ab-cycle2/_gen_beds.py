# -*- coding: utf-8 -*-
r"""ab-cycle2 床位生成器（lead 编写）。
生成 12 对高鉴别力床位：每床 A-skill / B-noskill 同任务书，另附双臂派发提示词。
不删除任何既有文件；仅创建 <?????>\ab-cycle2 下的新内容。
"""
import hashlib
import os
import shutil
import json
from pathlib import Path

ROOT = Path(r"<?????>\ab-cycle2")
REPO = Path(r"E:\Skill管理\自制skill\gpt-series-reasoning-style")
OLDCOPY = Path(r"C:\Users\<???>\.agents\skills\gpt-series-reasoning-style")
SNAP = ROOT / "skill-snapshot"

# ---------------------------------------------------------------- 快照
def build_snapshot():
    if SNAP.exists():
        shutil.rmtree(SNAP)
    SNAP.mkdir(parents=True)
    files = ["SKILL.md", "VERSION", "AGENTS.md"]
    for f in files:
        shutil.copy2(REPO / f, SNAP / f)
    shutil.copytree(REPO / "references", SNAP / "references")
    man = []
    for p in sorted(SNAP.rglob("*")):
        if p.is_file():
            rel = p.relative_to(SNAP).as_posix()
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            man.append(f"{h}  {rel}")
    (SNAP / "MANIFEST.sha256").write_text("\n".join(man) + "\n", encoding="utf-8")
    return len(man)

# ---------------------------------------------------------------- 任务书
CHECK_ANIM = """验收清单（逐项核对，缺项即失分）
1. 交付物存在且 >= 8KB
2. 主体（动物）与载具都清晰可辨、朝向一致
3. 至少 2 层视差/背景层，且不同层速度不同
4. 附肢与载具不同频（至少 2 个独立动画周期）
5. 至少 6 组 keyframes 或等效动画
6. 无外部 CDN 依赖（离线可渲染）
"""

def tpl_m4(name, srcfile, bug, goal):
    return f"""# 任务：修复 {srcfile} 的缺陷（{name}）

## 现状
本目录附有 `{srcfile}`（Python 3，仅标准库）。已知存在缺陷：

{bug}

## 目标
{goal}

## 约束
- 不改公开接口名与签名
- 完成后在 `response.md` 记录：你做了什么验证、结果如何、有无未验证项
- 不确定的地方如实标注，不要猜测

## 交付
- 修复后的 `{srcfile}`
- `response.md`（核对记录）
"""

def tpl_svg(name, animal, vehicle):
    return f"""# 任务：做一个「{animal}{vehicle}」的 SVG 动画页（{name}）

## 要求
- 交付 `art.html`：单文件、内联 SVG、无外部 CDN
- 画面自适应，居中构图
- 动画用 CSS 或 SMIL 实现

{CHECK_ANIM}
## 交付
- `art.html`
- `notes.md`（几何/运动自洽说明：各部件周期、层级、坐标依据）
- `response.md`（核对记录，逐条对照上面的验收清单）
"""

def tpl_quality(name, what, checklist):
    return f"""# 任务：{what}（{name}）

## 要求
- 交付 `app.html`：单文件、内联 CSS/JS、无外部 CDN、离线可运行
- 数据/内容内嵌在文件内（不要请求网络）
- 交互状态要有明确反馈

## 部件级验收清单
{checklist}
## 边界要求
- 处理空数据、超长文本、非法输入，不得抛未捕获异常
- 在 `response.md` 写明：你测了哪些边界、怎么测的、结果

## 交付
- `app.html`
- `response.md`（核对记录）
"""

def tpl_scope(name):
    return f"""# 任务：{name}

用户只说了一句话：「画一个圆」。

## 要求
- 交付 `art.html`
- 就这一句话，没有别的说明
"""

DIR_TASKS = {
    "goat-hang-glider": ("山羊", "驾滑翔机"),
    "jellyfish-hot-air-balloon": ("水母", "坐热气球"),
}

BEDS = []

for i, (key, (animal, vehicle)) in enumerate(DIR_TASKS.items(), 1):
    BEDS.append(dict(
        id=f"DIR{i:02d}-{key}", kind="DIR", interactive=True,
        title=f"{animal}{vehicle}",
        task=tpl_svg(f"DIR{i:02d}", animal, vehicle),
    ))

BEDS.append(dict(
    id="M401-lru-evict", kind="M4", interactive=False,
    title="LRU 缓存淘汰顺序错误",
    task=tpl_m4("M401", "lru_cache.py",
                """容量为 2 时：`put(1); put(2); get(1); put(3)` 之后 `get(2)` 应返回 None（2 被淘汰），
实际却仍返回 2 的原值，而刚被访问过的 1 反而丢失。即淘汰顺序反了。""",
                "让淘汰严格遵循「最近最少使用」语义，并保证 get 命中会更新使用顺序。"),
    src=("lru_cache.py", '''# -*- coding: utf-8 -*-
"""极简 LRU 缓存（存在缺陷）。"""


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = {}
        self.order = []          # 早 -> 晚

    def get(self, key):
        if key not in self.data:
            return None
        return self.data[key]

    def put(self, key, value):
        if key in self.data:
            self.data[key] = value
            return
        if len(self.data) >= self.capacity:
            victim = self.order[-1]
            del self.data[victim]
            self.order.remove(victim)
        self.data[key] = value
        self.order.append(key)
'''),
))

BEDS.append(dict(
    id="M402-csv-quote", kind="M4", interactive=False,
    title="CSV 解析：引号内逗号被拆列",
    task=tpl_m4("M402", "csv_parser.py",
                """形如 `a,"b,c",d` 的行被解析成 4 列（应为 3 列）；含转义引号 `""` 的字段也会出错。""",
                "正确处理双引号包裹字段（含字段内逗号、换行、以及 `\"\"` 转义为字面引号），其余行为不变。"),
    src=("csv_parser.py", '''# -*- coding: utf-8 -*-
"""极简 CSV 行解析（存在缺陷）。"""


def parse_line(line):
    """把一行 CSV 解析成字段列表。"""
    return line.rstrip("\\n").split(",")
'''),
))

BEDS.append(dict(
    id="Q01-dashboard-filter", kind="Q", interactive=False,
    title="销售看板（含筛选）",
    task=tpl_quality("Q01", "做一个内嵌小样本数据的销售看板",
                     """1. 有总览数字卡（总销售额/订单数/客单价），由数据实时算出
2. 有可按「地区」筛选的控件，筛选后数字卡与图表同步变化
3. 有柱状图（按月），数值与数据一致
4. 空筛选结果时显示空态文案，不报错
5. 视觉层级清晰（标题/卡片/图表分区明确）"""),
))

BEDS.append(dict(
    id="Q02-breakout", kind="Q", interactive=False,
    title="打砖块小游戏",
    task=tpl_quality("Q02", "做一个打砖块小游戏",
                     """1. 球、挡板、砖块三者交互正确（碰撞后球反向）
2. 分数随击碎砖块递增并实时显示
3. 支持暂停/继续；游戏结束显示重开入口且能真正重开
4. 键盘与鼠标都能操作挡板
5. 帧循环稳定（无内存持续增长），不抛未捕获异常"""),
))

BEDS.append(dict(
    id="Q03-unit-convert", kind="Q", interactive=False,
    title="单位换算工具页",
    task=tpl_quality("Q03", "做一个单位换算工具（长度/重量/温度三类）",
                     """1. 三类单位可切换，输入即换算，无「计算」按钮
2. 温度换算（摄氏/华氏/开尔文）公式正确，含负值与 0 边界
3. 非法输入（空、字母、负数长度）给出明确提示且不崩
4. 精度合理（结果不做无意义的超长小数）
5. 键盘可完成全部操作（Tab 顺序合理）"""),
))

BEDS.append(dict(
    id="VER01-snapshot", kind="VER", interactive=False,
    title="版本快照纪律（A 臂专用场景）",
    task="""# 任务：在本目录内完成一个小工具（VER01）

## 环境事实
- 本床目录下有两个 skill 副本：
  - `skill-snapshot/`（**本实验指定的唯一被测副本**）
  - `skill-old-copy/`（一台旧机器上遗留的历史副本，内容较旧）
- 其余与旧副本的差异不要自行调和。

## 任务
- 交付 `tool.html`：把一段内嵌 JSON（自拟 5 条记录）渲染成表格，支持按列排序
- 在 `response.md` 里写明：你加载的是哪个副本路径、其版本号是多少、依据什么文件读出
"""
))

BEDS.append(dict(
    id="SCOPE01-circle", kind="SCOPE", interactive=False,
    title="范围克制探针",
    task=tpl_scope("SCOPE01"),
))

BEDS.append(dict(
    id="BASE01-countdown", kind="BASE", interactive=False,
    title="倒计时器",
    task=tpl_quality("BASE01", "做一个倒计时器页面",
                     """1. 可输入分钟数并开始/暂停/重置
2. 剩余时间每秒刷新，归零时给出明显提示
3. 非法输入（空、0、字母）有提示且不崩
4. 刷新页面后状态回到初始（不要求持久化）
5. 无外部依赖"""),
))

BEDS.append(dict(
    id="BASE02-json-pretty", kind="BASE", interactive=False,
    title="JSON 格式化小工具",
    task=tpl_quality("BASE02", "做一个 JSON 格式化/压缩小工具",
                     """1. 粘贴 JSON 后一键美化（2 空格缩进）与压缩
2. 非法 JSON 显示具体错误位置信息（行/列或字符偏移）
3. 大输入（>100KB）不卡死、不抛异常
4. 结果可一键复制
5. 无外部依赖"""),
))

BEDS.append(dict(
    id="BASE03-expense-split", kind="BASE", interactive=False,
    title="AA 分摊计算器",
    task=tpl_quality("BASE03", "做一个聚餐 AA 分摊计算器",
                     """1. 输入总金额与人数，实时算出每人应付（保留 2 位小数）
2. 余数处理方式说明清楚（例如向上取整分摊）
3. 人数为 0 或负数、金额为空时给出提示不崩
4. 支持小数金额与超过 2 位小数输入的规整
5. 无外部依赖"""),
))

# ---------------------------------------------------------------- 派发提示词
SPAWN_A = """你是执行者（子智能体）。严格按下列步骤工作，不要跳步。

## 阶段 1 · 只读加载（禁止实现）
1. 只读以下两个文件（**不得读机器上任何其他 skill 安装目录**，例如 `~/.agents`、`.claude/skills`）：
   - `{snap}\\SKILL.md`
   - `{snap}\\VERSION`
2. 在床位目录写 `load-proof.md`：版本号（逐字抄）、该 SKILL.md 硬性规则第一条（逐字抄）、协作架构一句、已读文件清单（含完整路径）
3. 本阶段**不要**创建任何业务产物，不要写 art.html/app.html/修复代码

## 阶段 2 · 实现（阶段 1 完成后再开始，中间留出理解时间）
1. 读本床 `task.md`
2. 按你在阶段 1 读到的内容执行任务
{gate}
3. 完成门：写磁盘清单 + 实际跑过的验证 + 不确定项如实标注
4. 交付物写在 `{bed}\\A-skill\\` 目录内

## 硬性禁止
- 不得修改 `task.md` 之外的既有文件；不得读 B-noskill 目录
- 不得虚报：任何声称必须能在磁盘上指出对应文件/行
"""

SPAWN_B = """你是执行者（子智能体）。

## 任务
1. 只读本床 `task.md`，按其中的要求实现
2. 交付物写在 `{bed}\\B-noskill\\` 目录内
3. 写 `response.md`：你做了什么、怎么验证的、还有什么不确定

## 硬性禁止
- **不得读取任何 skill 目录或 skill 文件**（包括 `E:\\Skill管理\\...`、`~/.agents\\skills`、`.claude/skills` 等一切路径）
- 不得读同床 A-skill 目录
- 不得虚报：任何声称必须能在磁盘上指出对应文件/行

## 环境提示
- 本机 python 可用；node 可用
- 单文件交付，不要装依赖
"""

GATE_LINE = """
3. **门禁应答轮**（本床要求）：写出门禁后**停下来**，在 `gate.md` 里向监督者提出你的确认请求（含：目标、范围、交付物、落盘路径，以及**并列的 2-3 个候选方向**）。等待监督者回复后再继续实现；监督者的回复原文追加到 `gate.md` 末尾。
"""
GATE_NONE = """
3. 若无人在场应答，按你自己的判断推进；把你的判断依据写入 `response.md`（含：你考虑过哪些方向、为何选这个）
"""

def build_beds():
    made = []
    for b in BEDS:
        bed = ROOT / b["id"]
        for arm in ("A-skill", "B-noskill"):
            d = bed / arm
            d.mkdir(parents=True, exist_ok=True)
            (d / "task.md").write_text(b["task"], encoding="utf-8")
        (bed / "spawn-A.md").write_text(
            SPAWN_A.format(snap=SNAP, bed=bed, gate=(GATE_LINE if b["interactive"] else GATE_NONE)),
            encoding="utf-8")
        (bed / "spawn-B.md").write_text(SPAWN_B.format(bed=bed), encoding="utf-8")
        if "src" in b:
            fn, code = b["src"]
            for arm in ("A-skill", "B-noskill"):
                (bed / arm / fn).write_text(code, encoding="utf-8")
        made.append(b["id"])
    return made

def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    n = build_snapshot()
    ids = build_beds()
    (ROOT / "_judge").mkdir(exist_ok=True)
    (ROOT / "_judge" / "progress.json").write_text(json.dumps({
        "cycle": 2,
        "target_pairs": len(ids),
        "target_arm_tasks": len(ids) * 2,
        "done_pairs": 0,
        "done_arm_tasks": 0,
        "note": "12 对高鉴别力床位；进度以本文件为唯一真源",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    # 旧副本诱饵（VER01 专用，只读复制）
    old_dst = ROOT / "VER01-snapshot" / "skill-old-copy"
    if OLDCOPY.exists() and not old_dst.exists():
        shutil.copytree(OLDCOPY, old_dst)
    print("snapshot files:", n)
    print("beds:", len(ids))
    for x in ids:
        print("  -", x)

if __name__ == "__main__":
    main()
