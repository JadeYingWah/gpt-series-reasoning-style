"""创意文案验证 - 解耦版"""
import re, sys
sys.path.insert(0, r"<实验根目录>\ab-decoupled-creative\A2plus\evidence")
from verify import check_completeness, check_word_count, check_three_ads, check_slogan_length, check_pain_points, load

SRC = r"<实验根目录>\ab-decoupled-creative\Decoupled\marketing.md"

def load_local():
    with open(SRC, encoding="utf-8") as f:
        return f.read()

def mutation_test(text):
    m1 = re.sub(r"## 5\. 品牌调性说明.+", "", text, flags=re.DOTALL)
    m2 = text.replace("「随手一记，知识自成。」", "「这是一个非常长的slogan超过了十五个字的限制。」")
    m3 = text.replace("### 创作者版\n\n> 灵感稍纵即逝？打开 NoteFlow 记一句，AI 帮你串联相关素材，下次创作不再从零开始。", "")
    r1, _ = check_completeness(m1)
    r2, _ = check_slogan_length(m2)
    r3, _ = check_three_ads(m3)
    return {"删品牌调性": not r1, "slogan超长": not r2, "删创作者广告": not r3}

if __name__ == "__main__":
    text = load_local()
    print("=== 验证 ===")
    for name, func in [("完整性", check_completeness), ("Slogan长度", check_slogan_length), ("三人群", check_three_ads), ("痛点数", check_pain_points)]:
        ok, d = func(text)
        print(f"{name}: {'PASS' if ok else 'FAIL'} - {d}")
    wc = check_word_count(text)
    for k, (ok, d) in wc.items():
        print(f"字数-{k}: {'PASS' if ok else 'FAIL'} - {d}")
    print("\n=== 变异测试 ===")
    mt = mutation_test(text)
    for k, v in mt.items():
        print(f"{k}: {'被杀死' if v else '存活'}")
    print(f"杀伤率: {sum(mt.values())}/3")
