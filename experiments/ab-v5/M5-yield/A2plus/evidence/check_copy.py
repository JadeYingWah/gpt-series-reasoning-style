# -*- coding: utf-8 -*-
"""landing-copy.md 机械检查脚本（验证路径1）
覆盖分段：禁词(D1)/感叹号(D3)/催促语(D4)/slogan长度(D5)/感官词(D6)/
场景字数(D7)/单句≤20字(D8)/段≤3句(D9)/场景锚定(D10)/结构完整(D11)/故事字数(D12)
D2（空泛形容词语义判断）由人工审查覆盖，脚本仅扫禁词表+扩展词表兜底。
"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PATH = r"<实验根目录>\ab-v5\M5-yield\A2plus\landing-copy.md"
text = open(PATH, encoding="utf-8").read()

FORBIDDEN = ["醇厚", "香浓", "丝滑", "臻选", "匠心", "极致", "赋能", "引领"]
URGE = ["快来买", "限时", "立即", "抢购", "手慢无", "最后一天", "仅剩"]
SENSORY = ["茉莉", "柑橘", "焦糖", "莓果", "花香", "果酸", "甜", "酸", "香"]
SCENES = ["清晨", "午后", "深夜", "加班", "周末"]

def chars(s):  # 去标点后的字数
    return len(re.sub(r"[\s，。、！？：；·—\"\"''（）]", "", s))

def sentences(s):  # 按句末标点切分
    return [x.strip() for x in re.split(r"[。！？]", s) if x.strip()]

results, fails = [], 0
def check(label, ok, detail):
    global fails
    results.append(f"[{'PASS' if ok else 'FAIL'}] {label} — {detail}")
    if not ok: fails += 1

# 解析章节
sections = re.split(r"^## ", text, flags=re.M)
sec = {}
for s in sections:
    name = s.split("\n", 1)[0].strip()
    if name: sec[name.split(" · ")[0]] = s.split("\n", 1)[1] if "\n" in s else ""

slogan_raw = sec.get("主 slogan", "").strip()
story_raw = sec.get("产品故事", "").strip()
sc_parts = re.split(r"^### ", sec.get("饮用场景", ""), flags=re.M)
scenarios = []  # (标题, 正文)
for p in sc_parts[1:]:
    lines = p.strip().split("\n")
    title = lines[0].strip()
    body = "\n".join(lines[1:]).strip()
    scenarios.append((title, body))

# D1 禁词
hits = [w for w in FORBIDDEN if w in text]
check("D1 禁词表8词0命中", not hits, f"命中: {hits or '无'}")

# D2兜底：空泛形容词扩展扫描
VAGUE = ["浓郁", "顺滑", "香醇", "醇香", "顶级", "完美", "超凡", "非凡"]
vhits = [w for w in VAGUE if w in text]
check("D2兜底 空泛形容词扩展0命中", not vhits, f"命中: {vhits or '无'}")

# D3 感叹号
n_ex = text.count("！") + text.count("!")
check("D3 感叹号≤1", n_ex <= 1, f"计数: {n_ex}")

# D4 催促语
uhits = [w for w in URGE if w in text]
check("D4 催促语0命中", not uhits, f"命中: {uhits or '无'}")

# D5 slogan 长度≤12
slogan = slogan_raw.replace("\n", "")
check("D5 slogan≤12字", chars(slogan) <= 12, f"{chars(slogan)}字: {slogan}")

# D6 slogan 含感官词
shits = [w for w in SENSORY if w in slogan]
check("D6 slogan含具体感官词", bool(shits), f"感官词: {shits or '无'}")

# D7 每条场景≤80字
for t, b in scenarios:
    n = chars(b)
    check(f"D7 场景[{t}]≤80字", n <= 80, f"{n}字")

# D8 单句≤20字（全篇正文：slogan+场景+故事）
all_body = slogan_raw + "".join(b for _, b in scenarios) + story_raw
long_s = [s for s in sentences(all_body) if chars(s) > 20]
check("D8 全篇单句≤20字", not long_s, f"超长句: {long_s or '无'}")

# D9 每段≤3句（场景与故事正文按段落）
bad_para = []
for t, b in scenarios:
    for para in [p for p in b.split("\n") if p.strip()]:
        if len(sentences(para)) > 3: bad_para.append(f"{t}:{para[:15]}")
for para in [p for p in story_raw.split("\n") if p.strip()]:
    if len(sentences(para)) > 3: bad_para.append(f"故事:{para[:15]}")
check("D9 每段≤3句", not bad_para, f"超段: {bad_para or '无'}")

# D10 场景锚定具体饮用场景
for t, b in scenarios:
    s_hit = [w for w in SCENES if w in t or w in b]
    check(f"D10 场景[{t}]锚定具体场景", bool(s_hit), f"锚点: {s_hit or '无'}")

# D11 结构完整：1 slogan + 3 场景 + 1 故事
check("D11 结构完整(1+3+1)", len(slogan) > 0 and len(scenarios) == 3 and len(story_raw) > 0,
      f"slogan:{bool(slogan_raw)} 场景数:{len(scenarios)} 故事:{bool(story_raw)}")

# D12 产品故事≈150字（140-160区间）
sn = chars(story_raw)
check("D12 故事≈150字(140-160)", 140 <= sn <= 160, f"{sn}字")

print("\n".join(results))
print(f"\n== 结果: {len(results)-fails}/{len(results)} PASS, {fails} FAIL ==")
sys.exit(1 if fails else 0)
