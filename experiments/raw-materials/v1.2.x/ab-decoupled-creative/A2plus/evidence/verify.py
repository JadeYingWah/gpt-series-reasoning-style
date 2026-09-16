"""创意文案验证脚本 - A2+配置"""
import re
import json

SRC = r"<实验根目录>\ab-decoupled-creative\A2plus\marketing.md"

def load():
    with open(SRC, encoding="utf-8") as f:
        return f.read()

def check_completeness(text):
    """完整性检查：5部分是否齐全"""
    sections = ["Slogan", "产品描述", "广告文案", "痛点分析", "品牌调性"]
    found = [s for s in sections if s in text]
    return len(found) == 5, f"找到{len(found)}/5部分: {found}"

def check_word_count(text):
    """字数检查：产品描述100-150字，广告每条50-80字"""
    results = {}
    # 产品描述
    m = re.search(r"## 2\. 产品描述\n\n(.+?)\n\n##", text, re.DOTALL)
    if m:
        desc = m.group(1).strip()
        desc_len = len(desc)
        results["产品描述"] = (100 <= desc_len <= 150, f"{desc_len}字")
    # 广告文案
    ads = re.findall(r"> (.+)", text)
    for i, ad in enumerate(ads):
        ad_len = len(ad)
        results[f"广告{i+1}"] = (50 <= ad_len <= 80, f"{ad_len}字")
    return results

def check_three_ads(text):
    """3条广告是否针对不同人群"""
    audiences = ["学生", "职场", "创作者"]
    found = [a for a in audiences if a in text]
    return len(found) == 3, f"找到{len(found)}/3人群: {found}"

def check_slogan_length(text):
    """Slogan不超过15字"""
    m = re.search(r"## 1\. Slogan\n\n\*\*「(.+?)」\*\*", text)
    if m:
        slogan = m.group(1)
        return len(slogan) <= 15, f"'{slogan}' {len(slogan)}字"
    return False, "未找到slogan"

def check_pain_points(text):
    """至少3个痛点"""
    rows = re.findall(r"\| (.+?) \|", text)
    pain_rows = [r for r in rows if r not in ["痛点", "---"] and not r.startswith(":")]
    return len(pain_rows) >= 3, f"找到{len(pain_rows)}个痛点"

def mutation_test():
    """变异测试：删除某个元素，看检查能否发现"""
    original = load()
    # 变异1：删除品牌调性部分
    mutant1 = re.sub(r"## 5\. 品牌调性说明.+", "", original, flags=re.DOTALL)
    r1, _ = check_completeness(mutant1)
    # 变异2：slogan改长（超过15字）
    mutant2 = original.replace("「想法不流失，笔记自动流。」", "「这是一个非常长的slogan超过了十五个字的限制。」")
    r2, _ = check_slogan_length(mutant2)
    # 变异3：删除一个人群广告
    mutant3 = original.replace("### 面向创作者\n\n> 灵感来了又走？NoteFlow AI 随时捕捉碎片想法，自动关联相似主题，下次创作时素材已经帮你备好了。", "")
    r3, _ = check_three_ads(mutant3)
    return {
        "删除品牌调性": not r1,  # 应该被发现（r1=False表示不完整）
        "slogan超长": not r2,    # 应该被发现
        "删除创作者广告": not r3, # 应该被发现
    }

if __name__ == "__main__":
    text = load()
    print("=== 创意文案验证 ===")
    c1, d1 = check_completeness(text)
    print(f"完整性: {'PASS' if c1 else 'FAIL'} - {d1}")
    c2, d2 = check_slogan_length(text)
    print(f"Slogan长度: {'PASS' if c2 else 'FAIL'} - {d2}")
    wc = check_word_count(text)
    for k, (ok, d) in wc.items():
        print(f"字数-{k}: {'PASS' if ok else 'FAIL'} - {d}")
    c4, d4 = check_three_ads(text)
    print(f"三人群覆盖: {'PASS' if c4 else 'FAIL'} - {d4}")
    c5, d5 = check_pain_points(text)
    print(f"痛点数量: {'PASS' if c5 else 'FAIL'} - {d5}")
    print("\n=== 变异测试 ===")
    mt = mutation_test()
    for k, killed in mt.items():
        print(f"{k}: {'被杀死' if killed else '存活'}")
    all_killed = all(mt.values())
    print(f"\n变异杀伤率: {sum(mt.values())}/3 = {sum(mt.values())/3*100:.0f}%")
