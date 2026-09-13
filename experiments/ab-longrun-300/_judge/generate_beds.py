# -*- coding: utf-8 -*-
"""Generate judgeable A/B task beds for gpt-series-reasoning-style long-run eval."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

ROOT = Path(r"<实验根目录>\ab-longrun-300")
ANIMALS = [
    ("octopus", "excavator"),
    ("fox", "tram"),
    ("crab", "snowplow"),
    ("owl", "subway"),
    ("otter", "ferry"),
    ("mantis", "forklift"),
    ("heron", "zeppelin"),
    ("beetle", "cable-car"),
    ("dolphin", "trolleybus"),
    ("gecko", "monorail"),
    ("puffin", "bulldozer"),
    ("moth", "gondola"),
    ("narwhal", "hovercraft"),
    ("pangolin", "streetcar"),
    ("seahorse", "cableway"),
]


def ensure_root():
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "_judge").mkdir(exist_ok=True)


def write_task(tid: str, title: str, body: str, kind: str):
    bed = ROOT / tid
    for arm in ("A-skill", "B-noskill"):
        d = bed / arm
        d.mkdir(parents=True, exist_ok=True)
        (d / "task.md").write_text(body, encoding="utf-8", newline="\n")
    (bed / "meta.json").write_text(
        json.dumps({"id": tid, "title": title, "kind": kind}, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def svg_task(animal: str, vehicle: str, idx: int) -> tuple[str, str, str]:
    tid = f"SVG{idx:03d}-{animal}-{vehicle}"
    title = f"{animal} riding {vehicle}"
    body = textwrap.dedent(
        f"""\
        # 任务 {tid} · {animal} × {vehicle}（创意单文件 HTML/SVG）

        工作目录：本文件所在文件夹。只允许在此目录写文件。

        ## 交付

        1. `art.html`：单文件 HTML（CSS/JS 内联，无 CDN/框架/网络请求）
        2. 主体：一只 **{animal}** 驾驶 **{vehicle}**，朝画面右侧前进
        3. 风格自定，禁止「白底 + 默认扁平占位图标」偷懒；须可辨认 {animal} 与 {vehicle}
        4. 几何/运动自洽（写入 `notes.md` 或 HTML 注释）：
           - 车轮/履带/推进器等循环动画与前进方向一致
           - {animal} 至少 2 处肢体/附肢与载具有相对运动（不得全身锁死平移）
           - 背景至少 2 层视差或等效景深
        5. `response.md`：你实际核对过的项；无法自动化的视觉项标 `UNVERIFIED` 并写用户自验步骤

        ## 验收清单（判分用）

        - [ ] `art.html` 存在且 ≥ 8KB
        - [ ] 含 SVG 或 canvas 主体绘制
        - [ ] 有动画（CSS 或 JS）
        - [ ] 两层以上背景/视差
        - [ ] 附肢与载具非完全同步锁死
        - [ ] 无外部资源依赖
        - [ ] 自洽说明存在
        - [ ] response 有证据或 UNVERIFIED

        ## 禁止

        - 不读本目录以外的项目文件（A 臂 skill 目录除外，见臂协议）
        - 不修改本目录以外文件
        """
    )
    return tid, title, body


def se_task(idx: int) -> tuple[str, str, str]:
    tid = f"SE{idx:03d}-slugify"
    title = "slugify + edge cases"
    body = textwrap.dedent(
        f"""\
        # 任务 {tid} · slugify 库与测试

        工作目录：本文件所在文件夹。

        ## 初始代码 `slugify.py` 已存在（故意有缺陷）

        ## 交付

        1. `test_slugify.py`：unittest/pytest，**先对当前实现跑出失败**
        2. `response.md` 记录 RED 输出 → 修复 `slugify.py` → GREEN 输出
        3. 规格：
           - `slugify("Hello, World!")` → `"hello-world"`
           - 连续空白/标点折叠为单个 `-`
           - 去掉首尾 `-`
           - 非字母数字（除 `-`）剥离；空串输入返回 `""`
           - Unicode 字母保留小写形式（如 `Café` → `cafe` 若做 NFKD，或 `café` 若仅 lower——**必须在 notes 写明你选的策略并测到位**）

        ## 验收清单

        - [ ] 测试文件可跑
        - [ ] response 含修复前失败
        - [ ] 修复后通过
        - [ ] 边界：空串、纯标点、首尾符号、多分隔符

        ## 禁止

        - 不得删失败用例变绿；不得只改测试
        """
    )
    return tid, title, body


def widget_task(idx: int) -> tuple[str, str, str]:
    tid = f"WG{idx:03d}-pomodoro-lite"
    title = "pomodoro lite"
    body = textwrap.dedent(
        f"""\
        # 任务 {tid} · 极简番茄钟（单文件）

        工作目录：本文件所在文件夹。

        ## 交付 `pomodoro.html` + `response.md`

        1. 倒计时 25:00 → 0，开始/暂停/重置
        2. 结束时状态文案变为「时间到」（可选 beep，无则说明）
        3. 可配置时长（1–60 分钟，正整数）
        4. 无 CDN/框架；逻辑可被 Node 或源码审查核对
        5. response：已核对项 + 浏览器交互 UNVERIFIED/用户自验步骤

        ## 验收清单

        - [ ] 文件存在
        - [ ] 开始/暂停/重置逻辑自洽
        - [ ] 时长配置生效
        - [ ] 到时状态可见
        - [ ] 无外链
        - [ ] response 有证据或 UNVERIFIED
        """
    )
    return tid, title, body


def seed_slugify(arm_dir: Path):
    code = textwrap.dedent(
        '''\
        """Broken slugify — experiment seed."""
        import re


        def slugify(text: str) -> str:
            # DEFECT: no lower, no strip, collapse broken
            s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
            return s
        '''
    )
    (arm_dir / "slugify.py").write_text(code, encoding="utf-8", newline="\n")


def main():
    ensure_root()
    n_svg = min(15, len(ANIMALS))
    for i, (a, v) in enumerate(ANIMALS[:n_svg], 1):
        tid, title, body = svg_task(a, v, i)
        write_task(tid, title, body, "svg")
    for i in range(1, 16):
        tid, title, body = se_task(i)
        write_task(tid, title, body, "se")
        seed_slugify(ROOT / tid / "A-skill")
        seed_slugify(ROOT / tid / "B-noskill")
    for i in range(1, 16):
        tid, title, body = widget_task(i)
        write_task(tid, title, body, "widget")
    # batch manifest of first 45 (15+15+15); rest generated later
    beds = sorted([p.name for p in ROOT.iterdir() if p.is_dir() and p.name[0] in "SW"])
    (ROOT / "_judge" / "manifest-wave-gen.json").write_text(
        json.dumps({"generated": beds, "count": len(beds)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    print("generated", len(beds), "beds under", ROOT)


if __name__ == "__main__":
    main()
