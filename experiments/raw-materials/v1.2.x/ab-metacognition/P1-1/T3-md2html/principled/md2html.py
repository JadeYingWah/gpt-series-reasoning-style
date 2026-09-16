#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md2html —— 单文件、零依赖的 Markdown → HTML 转换器。

用法
    python md2html.py <file.md>        # 输出完整 HTML 文档到 stdout

支持（TASK-T3 功能要求）
    1. 标题      # ~ ######        -> <h1> ~ <h6>
    2. 列表      - / * 无序；1. 有序（支持一层以上缩进嵌套，见 DECLARATIONS）
    3. 围栏块    ```            -> <pre><code>（块内内容原样保留，只做实体转义）
    4. 行内代码  `code`          -> <code>
    5. 强调      **b** / __b__   -> <strong>；*i* / _i_ -> <em>
    6. 链接      [text](url)     -> <a href="...">
    7. 段落      连续非空行合并   -> <p>
    8. CLI

刻意不支持（超出任务书范围，未实现，见 DECLARATIONS）
    块引用、水平线、表格、Setext 标题、图片、脚注、HTML 块、转义反斜杠。

公开 API（供第三方验证脚本导入）
    escape_text(s) / escape_attr(s)
    inline(s)          -> 行内片段 HTML
    render(md)         -> body 片段 HTML
    render_document(md, title=None) -> 完整 HTML 文档
    main(argv)         -> 退出码
"""

import os
import re
import sys

__all__ = [
    "escape_text", "escape_attr", "quote_attr", "inline", "render",
    "render_document", "main",
]

# ---------------------------------------------------------------- 实体转义

def escape_text(s):
    """文本内容转义：& < > 转为实体（& 必须最先处理，避免二次转义）。"""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_attr(s):
    """属性值转义：文本转义 + 双引号转义。用于「未经转义的原始串」。"""
    return escape_text(s).replace('"', "&quot;")


def quote_attr(s):
    """只补转义双引号。用于「已经过 escape_text 的串」，避免 & 被二次转义。"""
    return s.replace('"', "&quot;")


# ---------------------------------------------------------------- 行内解析

_CODE_RE = re.compile(r"(`+)(.*?)\1")
_PLACEHOLDER_RE = re.compile(r"\x00(\d+)\x00")

_BOLD_STAR = re.compile(r"\*\*\*(?=\S)(.+?)(?<=\S)\*\*\*")     # ***both***
_BOLD_1 = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_BOLD_2 = re.compile(r"(?<!\w)__(?=\S)(.+?)(?<=\S)__(?!\w)")
_ITAL_1 = re.compile(r"\*(?=\S)(.+?)(?<=\S)\*")
_ITAL_2 = re.compile(r"(?<!\w)_(?=\S)(.+?)(?<=\S)_(?!\w)")

_TITLE_RE = re.compile(r'^\s*(?:"([^"]*)"|\'([^\']*)\'|\(([^)]*)\))\s*$', re.S)


def _emphasis(text):
    """强调：先 *** 再 **/__ 再 */_ 。行内代码已被占位符保护，不会被误判。"""
    text = _BOLD_STAR.sub(r"<em><strong>\1</strong></em>", text)
    text = _BOLD_1.sub(r"<strong>\1</strong>", text)
    text = _BOLD_2.sub(r"<strong>\1</strong>", text)
    text = _ITAL_1.sub(r"<em>\1</em>", text)
    text = _ITAL_2.sub(r"<em>\1</em>", text)
    return text


def _find_link_close(text, start):
    """从 '[' 位置 start 起，找到那个「紧跟着 '(' 的 ']'」。

    允许链接文本内部出现 ']'（TASK-T3 边界）：扫描时取满足条件的最后一个
    候选，因此 `[a]b](url)` 的链接文本为 `a]b`。
    """
    depth = 1
    k = start + 1
    n = len(text)
    while k < n:
        c = text[k]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth <= 0:
                depth = 0
                if k + 1 < n and text[k + 1] == "(":
                    return k
        k += 1
    return None


def _parse_dest(text, open_paren):
    """解析 (...) 中的目标地址与可选标题。

    返回 (结束下标, dest, title)；非法时返回 (None, None, None)。
    规则：目标地址可用 <> 包裹以允许空格；未包裹且含空白 -> 视为非法链接，
    按字面文本输出（不产出半截 href）。
    """
    depth = 1
    k = open_paren + 1
    n = len(text)
    buf = []
    while k < n:
        c = text[k]
        if c == "(":
            depth += 1
            buf.append(c)
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
            buf.append(c)
        elif c == "\n":
            return None, None, None
        else:
            buf.append(c)
        k += 1
    else:
        return None, None, None  # 没有闭合的 ')'

    raw = "".join(buf)
    # 注意：此时文本已做过实体转义，故 '<' 呈现为 '&lt;'
    if raw.startswith("&lt;"):
        gt = raw.find("&gt;")
        if gt < 0:
            return None, None, None
        dest = raw[len("&lt;"):gt].replace(" ", "%20")   # <> 包裹时允许空格
        rest = raw[gt + len("&gt;"):]
    else:
        m = re.match(r"\s*(\S*)(.*)$", raw, re.S)
        dest, rest = m.group(1), m.group(2)
        if " " in dest or "\t" in dest:
            return None, None, None
    dest = re.sub(r"\s+", "", dest)

    rest_stripped = rest.strip()
    title = None
    if rest_stripped:
        tm = _TITLE_RE.match(rest)     # 标题必须独占剩余内容
        if not tm:
            return None, None, None
        title = tm.group(1) or tm.group(2) or tm.group(3) or ""
    return k, dest, title


def _links(text):
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "[":
            out.append(text[i])
            i += 1
            continue
        close = _find_link_close(text, i)
        if close is None or close + 1 >= n or text[close + 1] != "(":
            out.append(text[i])
            i += 1
            continue
        end, dest, title = _parse_dest(text, close + 1)
        if end is None:
            out.append(text[i])
            i += 1
            continue
        label = _emphasis(text[i + 1:close])   # 链接文本与 dest 均已转义，不再重复转义
        attr = ' href="%s"' % quote_attr(dest)
        if title:
            attr += ' title="%s"' % quote_attr(title)
        out.append("<a%s>%s</a>" % (attr, label))
        i = end + 1
    return "".join(out)


def inline(text):
    """行内解析：行内代码优先保护 -> 实体转义 -> 链接 -> 强调 -> 还原代码。"""
    codes = []

    def _stash(m):
        codes.append(escape_text(m.group(2)))
        return "\x00%d\x00" % (len(codes) - 1)

    text = text.replace("\x00", "")       # NUL 是内部占位符，先剔除
    text = _CODE_RE.sub(_stash, text)
    text = escape_text(text)
    text = _links(text)
    text = _emphasis(text)
    return _PLACEHOLDER_RE.sub(lambda m: "<code>%s</code>" % codes[int(m.group(1))], text)


# ---------------------------------------------------------------- 块级解析

_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
_UL_ITEM_RE = re.compile(r"^([ \t]*)([-*])[ \t]+(.*)$")
_OL_ITEM_RE = re.compile(r"^([ \t]*)(\d{1,9})[.][ \t]+(.*)$")


def _indent_width(prefix):
    return len(prefix.replace("\t", "    "))


def _item_match(line):
    m = _UL_ITEM_RE.match(line)
    if m:
        return _indent_width(m.group(1)), False, 1, m.group(3)
    m = _OL_ITEM_RE.match(line)
    if m:
        return _indent_width(m.group(1)), True, int(m.group(2)), m.group(3)
    return None


def _parse_list(lines, i):
    """收集连续的列表项行，返回 (items, 新的行下标)。"""
    items = []
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            # 空行后仍是列表项 / 缩进续行 -> 松散列表，按紧排渲染（声明见下）
            if j < n and (_item_match(lines[j]) or
                          (lines[j][:1] in (" ", "\t") and lines[j].strip())):
                i = j
                continue
            break
        m = _item_match(line)
        if m:
            indent, ordered, num, content = m
            items.append({"level": indent // 2, "ordered": ordered,
                          "num": num, "lines": [content]})
            i += 1
            continue
        if items and line[:1] in (" ", "\t") and line.strip():
            items[-1]["lines"].append(line.strip())   # 懒延续行
            i += 1
            continue
        break
    return items, i


def _render_seq(items):
    """把扁平 items 渲染为嵌套 <ul>/<ol>。同级但类型不同时自动拆成两个列表。"""
    out = []
    i = 0
    n = len(items)
    while i < n:
        base = items[i]["level"]
        ordered = items[i]["ordered"]
        start_num = items[i]["num"]
        tag = "ol" if ordered else "ul"
        attrs = ' start="%d"' % start_num if (ordered and start_num != 1) else ""
        out.append("<%s%s>" % (tag, attrs))
        while i < n and items[i]["level"] == base and items[i]["ordered"] == ordered:
            it = items[i]
            content = inline("\n".join(it["lines"]).strip())
            j = i + 1
            children = []
            while j < n and items[j]["level"] > base:
                children.append(items[j])
                j += 1
            if children:
                content += "\n" + _render_seq(children)
            out.append("<li>%s</li>" % content)
            i = j
        out.append("</%s>" % tag)
    return "\n".join(out)


def render(md_text):
    """把 Markdown 文本转换为 body 片段 HTML。"""
    if md_text is None:
        md_text = ""
    text = md_text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\x00", "")   # NUL 是内部占位符，先剔除避免冲突
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()          # 去掉由文件末尾换行产生的空元素，避免代码块尾部多出空行


    out = []
    para = []

    def flush_para():
        if not para:
            return
        body = "\n".join(para).strip()
        if body:
            out.append("<p>%s</p>" % inline(body))
        del para[:]

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):                       # 围栏代码块
            flush_para()
            info = stripped[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            if i < n:
                i += 1                                       # 吃掉闭合围栏
            # 未闭合围栏：走到 EOF 即隐式闭合（声明见 DECLARATIONS）
            code = escape_text("\n".join(buf))
            if code:
                code += "\n"
            lang = info.split()[0] if info else ""
            cls = ' class="language-%s"' % escape_attr(lang) if lang else ""
            out.append("<pre><code%s>%s</code></pre>" % (cls, code))
            continue

        if not stripped:                                     # 空行分隔
            flush_para()
            i += 1
            continue

        m = _HEADING_RE.match(line)
        if m:                                                # 标题（与上下文有无空行无关）
            flush_para()
            level = len(m.group(1))
            content = (m.group(2) or "").strip()
            out.append("<h%d>%s</h%d>" % (level, inline(content), level))
            i += 1
            continue

        if _item_match(line):                                # 列表
            flush_para()
            items, i = _parse_list(lines, i)
            out.append(_render_seq(items))
            continue

        para.append(line.strip())                            # 段落
        i += 1

    flush_para()
    return "\n".join(out)


def render_document(md_text, title=None):
    """包装成完整 HTML 文档。标题缺省取首个 h1/h2... 标题，再退回 'Document'。"""
    if title is None:
        m = re.search(r"^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*$", md_text or "", re.M)
        title = m.group(1).strip() if m else "Document"
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh">\n<head>\n<meta charset="utf-8">\n'
        "<title>%s</title>\n</head>\n<body>\n%s\n</body>\n</html>\n"
        % (escape_text(title), render(md_text))
    )


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        sys.stderr.write("用法: python md2html.py <file.md>\n")
        return 2
    path = argv[0]
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as exc:
        # UnicodeDecodeError 不是 OSError：非 UTF-8 文件也要给友好报错而非 traceback
        sys.stderr.write("md2html: 无法读取 %s: %s\n" % (path, exc))
        return 1
    html = render_document(text, title=os.path.splitext(os.path.basename(path))[0])
    try:
        sys.stdout.buffer.write(html.encode("utf-8"))
        sys.stdout.buffer.flush()
    except AttributeError:                                   # 非二进制 stdout 的兜底
        sys.stdout.write(html)
    return 0


# ------------------------------------------------- 行为声明（供验证脚本引用）
DECLARATIONS = [
    "D1 未闭合 ``` 围栏：走到 EOF 隐式闭合，不报错、不丢内容。",
    "D2 嵌套列表：按缩进宽度/2 计算层级，子列表渲染为父 <li> 内的 <ul>/<ol>（实现而非降级）。",
    "D3 链接地址含未包裹空格：判定为非法链接，整段按字面文本输出（不产出截断 href）；"
    "用 <> 包裹时可含空格，空格转为 %20。",
    "D4 链接文本含 ']' ：取紧邻 '(' 的那个 ']' 作为结束，文本中的 ']' 原样保留。",
    "D5 松散列表按紧排渲染（列表项内容不额外包 <p>）。",
    "D6 行内代码内容只做实体转义，其中 * / _ 等字符绝不参与强调解析。",
    "D7 转义范围：文本 & < >；属性值额外转义 \"。代码块内同样转义。",
    "D8 输出为完整 HTML 文档（含 <!DOCTYPE>、meta charset、title），body 内为转换结果。",
    "D9 仅支持 - / * 无序标记与 '数字.' 有序标记；+ 与 '数字)' 不在任务书范围内，按普通段落处理。",
    "D10 围栏信息串（如 ```python）渲染为 <code class=\"language-python\">。",
    "D11 只接受 UTF-8 输入；非 UTF-8 文件给出友好报错并以退出码 1 结束（不抛 traceback）。",
    "D12 不做 URL 协议白名单：javascript: 等照常生成 <a href>（内容已转义）。"
    "任务书未要求安全过滤，越权加白名单会改变语义；需要过滤请另行明确要求。",
]


if __name__ == "__main__":
    sys.exit(main())
