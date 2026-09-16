"""创意类通用验证脚本 - 传入路径参数"""
import re, sys

def verify(md_path, ad_keywords):
    with open(md_path, encoding="utf-8") as f:
        text = f.read()
    results = {}
    # 完整性
    sections = ["Slogan", "产品描述", "广告", "痛点", "调性"]
    results["完整性"] = (sum(1 for s in sections if s in text) == 5, f"{sum(1 for s in sections if s in text)}/5")
    # Slogan长度
    m = re.search(r"[「\"](.+?)[」\"]", text.split("Slogan")[1] if "Slogan" in text else text)
    slogan_len = len(m.group(1)) if m else 0
    results["Slogan长度"] = (slogan_len <= 15 and slogan_len > 0, f"{slogan_len}字")
    # 产品描述字数
    desc_m = re.search(r"产品描述\n+(.+?)\n+##", text, re.DOTALL)
    desc_len = len(desc_m.group(1).strip()) if desc_m else 0
    results["描述字数"] = (100 <= desc_len <= 150, f"{desc_len}字")
    # 广告字数
    ads = re.findall(r"> (.+)", text)
    ad_lens = [len(a) for a in ads]
    results["广告数量"] = (len(ads) >= 3, f"{len(ads)}条")
    results["广告字数"] = (all(50 <= l <= 80 for l in ad_lens), f"{ad_lens}")
    # 三人群
    results["三人群"] = (sum(1 for k in ad_keywords if k in text) >= 3, f"{sum(1 for k in ad_keywords if k in text)}/3")
    # 痛点数
    pain_rows = re.findall(r"\| (.+?) \|", text)
    pain_count = sum(1 for r in pain_rows if r not in ["痛点", "---"] and not r.startswith(":"))
    results["痛点数"] = (pain_count >= 3, f"{pain_count}个")
    # 变异测试
    mutant1 = re.sub(r"## 5\..+", "", text, flags=re.DOTALL)
    mutant2 = re.sub(r"[「\"](.+?)[」\"]", "「这是一个非常长的slogan超过了十五个字的限制。」", text, count=1)
    r1 = sum(1 for s in sections if s in mutant1) == 5
    m2 = re.search(r"[「\"](.+?)[」\"]", mutant2.split("Slogan")[1] if "Slogan" in mutant2 else mutant2)
    r2 = len(m2.group(1)) <= 15 if m2 else True
    results["变异测试"] = (not r1 and not r2, "2/2被杀死")
    return results

if __name__ == "__main__":
    path = sys.argv[1]
    keywords = sys.argv[2].split(",") if len(sys.argv) > 2 else ["学生", "职场", "创作者"]
    results = verify(path, keywords)
    allok = True
    for k, (ok, msg) in results.items():
        allok = allok and ok
        print(f"  {'PASS' if ok else 'FAIL'} - {k}: {msg}")
    print(f"\n总体: {'全部通过' if allok else '存在问题'}")
