#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交付验收审计：order-report.html 的「12/12 自检」鉴别力审计。
方法：把页面 <script> 里那段自检的 12 条断言逐字移植为审计函数，
分别跑在「真实产物」和「若干变异体」上，统计每条检查对每类错误的杀伤力。
本脚本只读 order-report.html，不修改原产物。
"""
import re, os, hashlib

SRC = os.path.join(os.path.dirname(__file__), "..", "order-report.html")
with open(os.path.abspath(SRC), "r", encoding="utf-8") as f:
    HTML = f.read()

def amt_block(html, tag):
    m = re.search(r"<%s>(.*?)</%s>" % (tag, tag), html, re.S)
    return m.group(1) if m else ""

def line_amounts(html):
    body = amt_block(html, "tbody")
    return [float(x) for x in re.findall(r"¥(\d+\.\d{2})", body)]

def total_cell(html):
    foot = amt_block(html, "tfoot")
    txt = re.search(r'class="num total"[^>]*>([^<]+)<', foot)
    attr = re.search(r'data-amount="([^"]+)"', foot)
    return (txt.group(1).strip() if txt else None,
            attr.group(1).strip() if attr else None)

# ---- 逐字移植页面里的 12 条断言 ----
def run_checks(html):
    results = []
    def check(no, name, ok):
        results.append((no, name, bool(ok)))
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    title = title.group(1) if title else ""
    # 1 页面标题包含「对账单」
    check(1, "页面标题包含「对账单」", "对账单" in title)
    # 2 订单表格存在
    check(2, "订单表格存在", "order-table" in html)
    # 3 订单明细共 6 行
    body = amt_block(html, "tbody")
    check(3, "订单明细共 6 行", body.count("<tr>") == 6)
    # 4 合计栏存在
    check(4, "合计栏存在", "num total" in html)
    # 5 合计金额格式合法
    t, _ = total_cell(html)
    check(5, "合计金额格式合法", bool(t and re.match(r"^¥\d+\.\d{2}$", t)))
    # 6 合计文本与数据属性一致
    t, d = total_cell(html)
    check(6, "合计文本与数据属性一致", bool(t and d and t == d))
    # 7 货币符号统一为 ¥
    nums = re.findall(r'class="num[^"]*"[^>]*>([^<]*)<', html)
    # 只取明细 + 合计的数字单元格
    ok_cur = all("¥" in c for c in nums)
    check(7, "货币符号统一为 ¥", ok_cur)
    # 8 账期文本存在
    meta = re.search(r'class="meta"[^>]*>(.*?)<', html, re.S)
    check(8, "账期文本存在", bool(meta and "2026-08" in meta.group(1)))
    # 9 样式表已加载（页面用内联 <style>，styleSheets 必然 >0）
    check(9, "样式表已加载", "<style" in html)
    # 10/11/12 字面量 true
    check(10, "打印样式存在", True)
    check(11, "自检项共 12 项", True)
    check(12, "数据完整性校验通过", True)
    return results

def passed(results):
    return sum(1 for r in results if r[2])

def summarize(label, html):
    res = run_checks(html)
    p = passed(res)
    print(f"[{label}] 自检结果 {p}/{len(res)} 通过")
    detail = {1:"",2:"",3:"",4:"",5:"",6:"",7:"",8:"",9:"",10:"字面true",11:"字面true",12:"字面true"}
    for no, name, ok in res:
        tag = "OK " if ok else "FAIL"
        extra = f"  <-- {detail[no]}" if not ok and detail[no] else ""
        print(f"   #{no:<2} {tag} {name}{extra}")
    return res, p

print("=" * 64)
print("A. 真实产物上的算术核对（最关键：合计 == 各明细之和？）")
print("=" * 64)
items = line_amounts(HTML)
s = sum(items)
t_txt, t_attr = total_cell(HTML)
print(f"明细金额: {[ '¥%.2f'%x for x in items ]}")
print(f"明细求和 Σ = ¥{s:.2f}")
print(f"页面合计 total = {t_txt}  (data-amount={t_attr})")
diff = s - float(t_txt.replace('¥',''))
print(f"差额 Σ - total = ¥{diff:.2f}  -> {'一致 ✓' if abs(diff) < 1e-9 else '不一致 ✗ 真实缺陷'}")
print()

print("=" * 64)
print("B. 逐字执行页面自检 12 条（真实产物）")
print("=" * 64)
summarize("真实产物", HTML)
print()

print("=" * 64)
print("C. 变异体：把「真实缺陷」注入后，自检会不会变红？")
print("=" * 64)
# m-A: 合计被整体改成错误值，但 text 与 data-amount 一起改（典型手滑/复制错）
mut_A = HTML.replace('¥435.00', '¥999.00').replace('data-amount="¥999.00"', 'data-amount="¥999.00"') \
            if False else HTML.replace('¥435.00', '¥999.00')
# 上面 replace 同时改了 tfoot 文本与 data-amount（同字符串），模拟「两处一起写错」
summarize("m-A 合计改为¥999且两处同步", mut_A)
print()

# m-B: 少一行明细（5 行）
mut_B = re.sub(r'<tr><td>SSL 证书</td>.*?</tr>\s*', '', HTML, flags=re.S)
summarize("m-B 删除一行明细(剩5行)", mut_B)
print()

# m-C: 某个明细金额去掉 ¥ 符号
mut_C = HTML.replace('¥280.00', '280.00', 1)
summarize("m-C 某明细去¥符号", mut_C)
print()

# m-D: 标题去掉「对账单」
mut_D = HTML.replace('云服务月度对账单', '云服务月度清单')
summarize("m-D 标题去掉对账单", mut_D)
print()

print("=" * 64)
print("D. 杀伤率汇总（按错误类别）")
print("=" * 64)
print("错误类别                 | 变异体 | 被抓住 | 杀伤率")
print("-------------------------|--------|--------|------")
print("数值正确性(Σ≠total)       |   1    |   0    |  0%  <- 最致命，无人看守")
print("明细行数缺失              |   1    |   1    | 100% (check3)")
print("货币符号不统一            |   1    |   1    | 100% (check7)")
print("标题语义错误              |   1    |   1    | 100% (check1)")
print("写死true/自证类(check9/10/11/12) |   -    |   -    | 无鉴别力")
print()
print("结论：页面显示 12/12 全部通过 · 本产物可交付，")
print("      但该结论对『合计≠明细之和』这一真实缺陷毫无鉴别力。")
