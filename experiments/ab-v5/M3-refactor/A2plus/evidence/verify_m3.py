#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M3 个人主页 v2（浅色主题+联系表单）· 主验证脚本（保守方法：原始字节正则 + 标签栈 + WCAG 对比度）

变更 v2：浅色主题检查（亮度>0.85 + color-scheme:light）、14 组浅色对比度用例、
        联系表单结构与接线静态检查、内联脚本白名单化（外链仍为 0）。
用法: python evidence/verify_m3.py
输出: stdout + evidence/result_main.txt；全部通过时 RESULT: ALL GREEN，否则 FAIL（exit 1）
"""
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
HTML = BASE / "index.html"
OUT = Path(__file__).resolve().parent / "result_main.txt"

lines = []
passes = []
failures = []


def check(name, ok, detail=""):
    entry = f"{'PASS' if ok else 'FAIL'} | {name}" + (f" | {detail}" if detail else "")
    (passes if ok else failures).append(entry)
    lines.append(entry)


try:
    raw = HTML.read_bytes()
    text = raw.decode("utf-8")  # 非 UTF-8 直接抛异常
    check("单文件存在且可按 UTF-8 解码", True, f"{len(raw)} bytes, BOM={'有' if raw[:3] == b'\\xef\\xbb\\xbf' else '无'}")
except Exception as e:  # noqa: BLE001
    print(f"FATAL: 无法读取 index.html: {e}")
    sys.exit(2)

# ---- 1. 基础元信息 ----
check("DOCTYPE 声明存在", text.lstrip().lower().startswith("<!doctype html>"))
check("meta charset=UTF-8 存在", bool(re.search(r'<meta[^>]+charset=["\']?utf-8', text, re.I)))
check("viewport meta 存在", bool(re.search(r'<meta[^>]+name=["\']viewport["\']', text, re.I)))
check("lang 属性存在", bool(re.search(r'<html[^>]+lang=["\'][\w-]+["\']', text, re.I)))

# ---- 2. 外部依赖扫描（覆盖面分段：外部依赖注入向量；内联 <script> 允许，外链 0）----
EXT_PATTERNS = [
    (r"<script[^>]*\bsrc\s*=", "script 外链 src"),
    (r"src\s*=\s*[\"']?\s*(https?:|//)", "src 指向外部 URL / 协议相对地址"),
    (r"href\s*=\s*[\"']?\s*(https?:|//)", "href 指向外部 URL / 协议相对地址"),
    (r"@import", "CSS @import"),
    (r"url\(\s*[\"']?\s*(https?:|//)", "CSS url() 外部引用"),
    (r"fonts\.googleapis|fonts\.gstatic|cdn\.|unpkg\.com|jsdelivr|cdnjs", "公共 CDN 指纹"),
    (r"<link\b", "<link 外链标签（本页不应有）"),
    (r"https?://|//", "外部 URL / 协议相对地址字面量"),
]
for pat, desc in EXT_PATTERNS:
    hits = re.findall(pat, text, re.I)
    check(f"外部依赖 0 命中：{desc}", len(hits) == 0, f"命中 {len(hits)} 处" if hits else "")

attr_vals = re.findall(r'(?:href|src)\s*=\s*["\']([^"\']*)["\']', text, re.I)
bad_vals = [v for v in attr_vals if not (v == "#" or v.startswith("mailto:"))]
check("href/src 属性值全部在白名单（# / mailto:）", len(bad_vals) == 0,
      f"违规值: {bad_vals}" if bad_vals else f"共 {len(attr_vals)} 个属性值")
n_inline_script = len(re.findall(r"<script>", text))
check("存在且仅存在内联脚本（表单校验所需）", n_inline_script == 1, f"内联 <script> {n_inline_script} 个")

# ---- 3. 任务书点名场景（覆盖面分段：任务书点名场景；变更后结构保留+表单）----
check("头像占位存在（.avatar + 内联 SVG）",
      bool(re.search(r"class=[\"'][^\"']*avatar", text)) and "<svg" in text)
n_groups = len(re.findall(r"class=[\"']skill-group[\"']", text))
n_tags = len(re.findall(r"class=[\"']tag[\"']", text))
check("技能区块存在（#skills + 分组 + ≥5 个技能标签）",
      'id="skills"' in text and n_groups >= 1 and n_tags >= 5,
      f"分组 {n_groups} 个，标签 {n_tags} 个")
cards = len(re.findall(r"class=[\"']project-card[\"']", text))
check("项目卡片恰好 3 张（布局与内容结构保留）", cards == 3, f"实际 {cards} 张")

# ---- 4. 联系表单（变更点 2：真实可用表单 + 前端校验 + 成功提示）----
def has(pat, flags=re.I):
    return bool(re.search(pat, text, flags))


def field_check(tag_id, expected_type, is_textarea=False):
    """属性顺序无关的字段检查：提取完整标签后逐属性断言。"""
    pat = (rf"<textarea[^>]*id=[\"']{tag_id}[\"'][^>]*>" if is_textarea
           else rf"<input[^>]*id=[\"']{tag_id}[\"'][^>]*>")
    m = re.search(pat, text, re.I)
    if not m:
        return False, "标签未找到"
    tag = m.group(0)
    if not is_textarea and not re.search(rf"type=[\"']{expected_type}[\"']", tag, re.I):
        return False, f"type!={expected_type}"
    if not re.search(r"\brequired\b", tag):
        return False, "缺 required"
    if not re.search(rf"<label[^>]+for=[\"']{tag_id}[\"']", text, re.I):
        return False, "缺 label[for]"
    return True, ""


check("表单容器存在（#contact-form + novalidate 交由 JS 校验）",
      has(r'<form[^>]+id=["\']contact-form["\']') and has(r"<form[^>]+novalidate"))
for tid, ttype, ta, zh in (("cf-name", "text", False, "姓名"),
                           ("cf-email", "email", False, "邮箱"),
                           ("cf-message", "textarea", True, "留言")):
    ok, detail = field_check(tid, ttype, ta)
    check(f"{zh}字段（{ttype} + required + label[for]，属性顺序无关）", ok, detail)
check("错误提示元素齐备（err-name/err-email/err-message，初始 hidden）",
      all(has(rf'id=["\']err-{f}["\'][^>]*hidden') or has(rf'<p[^>]+hidden[^>]*id=["\']err-{f}["\']')
          for f in ("name", "email", "message")))
check("成功提示元素存在且初始 hidden", has(r'id=["\']form-success["\'][^>]*hidden')
      or has(r'<p[^>]+hidden[^>]*id=["\']form-success["\']'))
check("提交接线（submit 监听 + preventDefault）",
      has(r'addEventListener\(["\']submit["\']') and has(r"preventDefault\(\)"))
check("校验纯函数存在（可被 Node 动态执行）",
      has(r"VALIDATE-START") and has(r"VALIDATE-END") and has(r"function validateContact"))
check("空值→必填错误、格式→邮箱错误（静态分支可见）",
      has(r"请填写姓名") and has(r"请填写邮箱") and has(r"请填写留言") and has(r"邮箱格式不正确"))
check("提交成功路径存在（reset + success.hidden=false）",
      has(r"form\.reset\(\)") and has(r"success\.hidden\s*=\s*false"))

# ---- 5. 浅色主题（变更点 1：清爽浅色配色）----
def hex_lum(hx):
    hx = hx.lstrip("#")
    r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


bg_m = re.search(r"--bg:\s*(#[0-9a-fA-F]{6})", text)
check("浅色背景变量存在", bool(bg_m))
if bg_m:
    lum = hex_lum(bg_m.group(1))
    check("页面背景足够浅（相对亮度 > 0.85）", lum > 0.85, f"L={lum:.4f} ({bg_m.group(1)})")
check("color-scheme: light 声明", has(r"color-scheme[\"']?\s*[:=]\s*[\"']?light"))

# ---- 6. WCAG 对比度（覆盖面分段：可访问性；正常文本≥4.5，大字≥3.0；浅色调色板）----
def blend(fg_hex, bg_hex, alpha):
    f = [int(fg_hex.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(bg_hex.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    mixed = [round(a * alpha + c * (1 - alpha)) for a, c in zip(f, b)]
    return "#" + "".join(f"{v:02x}" for v in mixed)


def contrast(fg, bg):
    l1, l2 = hex_lum(fg), hex_lum(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


PAIRS = [
    ("#1f2937", "#f5f7fa", "正文 on 页面背景", 16, False),
    ("#1f2937", "#ffffff", "卡片正文 on surface", 16, False),
    ("#1f2937", "#eef1f5", "标签文字 on elevated", 14, False),
    ("#4b5563", "#f5f7fa", "副标题/表单标签/页脚链接 on 背景", 16, False),
    ("#4b5563", "#ffffff", "项目描述 on surface", 14, False),
    ("#626b78", "#f5f7fa", "状态/页脚弱化文字 on 背景", 14, False),
    ("#1d4ed8", "#f5f7fa", "链接 on 背景", 16, False),
    ("#1d4ed8", "#ffffff", "卡片内链接 on surface", 14, False),
    ("#1d4ed8", blend("#1d4ed8", "#ffffff", 0.08), "技术标签 on 混合底色(rgba 8%)", 12, False),
    ("#0f172a", "#3b82f6", "头像文字 on 渐变暗端", 30, True),
    ("#0f172a", "#93c5fd", "头像文字 on 渐变亮端", 30, True),
    ("#b42318", "#f5f7fa", "表单错误提示 on 背景", 14, False),
    ("#166534", blend("#166534", "#f5f7fa", 0.08), "成功提示 on 浅绿底(rgba 8%)", 14, False),
    ("#ffffff", "#1d4ed8", "按钮文字 on 按钮底", 14, False),
]
for fg, bg, label, px, bold in PAIRS:
    ratio = contrast(fg, bg)
    large = px >= 24 or (px >= 18.66 and bold)
    need = 3.0 if large else 4.5
    check(f"对比度 {label} = {ratio:.2f}:1（要求 ≥{need}）", ratio >= need, f"fg={fg} bg={bg}")

# ---- 7. HTML 标签闭合（覆盖面分段：HTML 边界）----
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr"}
stack, tag_errors = [], []
for m in re.finditer(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)([^>]*?)(/?)>", text):
    closing, tag, selfclose = m.group(1), m.group(2).lower(), m.group(4) == "/"
    if tag in VOID or selfclose:
        continue
    if not closing:
        stack.append(tag)
    elif stack and stack[-1] == tag:
        stack.pop()
    else:
        top = stack[-1] if stack else "空栈"
        tag_errors.append(f"</{tag}> 与栈顶 <{top}> 不匹配")
check("标签全部正确闭合", not tag_errors and not stack,
      "; ".join(tag_errors[:5]) or (f"未闭合: {stack}" if stack else ""))

# ---- 汇总 ----
lines.insert(0, f"目标文件: {HTML}")
lines.insert(1, f"检查项: {len(passes) + len(failures)} | PASS: {len(passes)} | FAIL: {len(failures)}")
lines.append("")
if failures:
    lines.append("--- 失败明细 ---")
    lines.extend(failures)
    lines.append("")
    lines.append("RESULT: FAIL")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    sys.exit(1)
lines.append("RESULT: ALL GREEN")
OUT.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
