#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
md2html.py —— 单文件、零依赖 Markdown -> HTML 转换器（Python 3 标准库 only）

用法：
    python md2html.py <file.md>        # 转出 HTML 片段到 stdout

作为库：
    import md2html
    html = md2html.convert(md_text)    # 返回 HTML 片段字符串

支持：
  * 标题 # ~ ###### -> h1~h6
  * 无序列表 - * + ；有序列表 N. / N)
  * 列表嵌套（按缩进：每 2 空格 = 1 层，制表符按 4 空格折算，层数不限）
  * ``` 围栏代码块 -> <pre><code>，内部原样保留（只做 & < > 实体转义，不做行内解析）
  * 行内代码 `code` -> <code>
  * 粗体 **b** / __b__ -> <strong>；斜体 *i* / _i_ -> <em>
  * 链接 [text](url) / [text](<url with space>)
  * 反斜杠转义 \* \_ \[ \] \( \) \` \\ 等
  * 段落：连续非空行合并为一个 <p>
  * 特殊字符 & < > 在任何位置均转义为 &amp; &lt; &gt;

行为声明（未在上方明确者，以此处为准）：
  1. 输出为 HTML **片段**，不包裹 <html>/<body>，也不含 CSS。
  2. `#Title`（# 后无空格）与 `#######`（7 个）不是标题，按段落输出。
  3. 围栏只认反引号 ```（>=3 个）；不支持 ~~~。围栏后的语言信息串被忽略（不生成 class）。
  4. 未闭合的 ``` 围栏：按“到文件结尾为止”输出 <pre><code>，并向 stderr 打印一条
     `md2html: warning:` 警告；不作为错误退出（exit code 仍为 0）。
  5. 链接文本中的 `]`：未转义的 `]` 结束链接文本；需要字面 `]` 时写 `\]`。
     支持链接文本内嵌套一层以上方括号，如 [a[b]c](u)。
  6. 链接地址含空格：必须写成 [t](<a b>)（尖括号形式）；写成 [t](a b) 时
     不识别为链接，整段按字面文本输出（已做实体转义）。
  7. 链接地址原样放入 href="..." 双引号内（空格不百分号编码），仅把 & 转 &amp;、
     " 转 &quot;；不做 javascript: 等协议白名单过滤（本工具定位为文本转换，非安全沙箱）。
  8. 行内强调不会进入行内代码与围栏代码块内部（先于强调抽取）。
  9. `_`/`__` 强调要求处于词边界（前后不能是字母数字或 _），故 foo_bar_baz 不会被强调。
 10. 段落内多行以 "\n" 连接（<p>line1\nline2</p>），与 Python-Markdown 一致。
 11. 缩进代码块（4 空格）、表格、引用 >、分隔线 ---、图片 ![]()、自动链接、
     脚注、HTML 块 等语法**均不支持**，按段落/字面文本输出。
 12. 输入中的 NUL(\x00) 字符被丢弃（占位符机制需要）。
 13. 输入按 UTF-8 读取，非法字节以 U+FFFD 替换，不抛异常。
"""

import re
import sys

__version__ = "1.0"

# ---------------------------------------------------------------- 基础转义

_ESCAPABLE = set('\\`*_{}[]()#+-.!<>&$:/"\'|~^=?@%;,')


def escape_html(s):
    """转义 & < > 为实体（三个字符在所有输出位置都必须转义）。"""
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def escape_attr(s):
    """转义属性值：在 escape_html 基础上再转义双引号。"""
    return escape_html(s).replace('"', '&quot;')


# ---------------------------------------------------------------- 行内解析

_CODE_RE = re.compile(r'(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)', re.S)

# 强调的内容段禁止跨越 '<' / '>'，即不允许跨越已生成的标签边界，
# 否则会出现 <em><strong><em></strong></em> 这类交叉嵌套的非法 HTML。
_EM_BOTH = re.compile(r'\*\*\*(?!\s)([^<>]+?)(?<!\s)\*\*\*', re.S)
_EM_STRONG = re.compile(r'(?<!\*)\*\*(?!\s)([^<>]+?)(?<!\s)\*\*(?!\*)', re.S)
_EM_STRONG_U = re.compile(r'(?<![\w_])__(?!\s)([^<>]+?)(?<!\s)__(?![\w_])', re.S)
_EM_EM = re.compile(r'(?<!\*)\*(?!\s)([^*<>]+?)(?<!\s)\*(?!\*)', re.S)
_EM_EM_U = re.compile(r'(?<![\w_])_(?!\s)([^_<>]+?)(?<!\s)_(?![\w_])', re.S)

_PLACEHOLDER_RE = re.compile('\x00(\\d+)\x00')


def _find_close(s, start, open_ch, close_ch):
    """从 s[start]（必须是 open_ch）开始找配对的 close_ch，支持嵌套与反斜杠转义。

    返回配对字符的下标，找不到返回 -1。
    """
    depth = 0
    i = start
    n = len(s)
    while i < n:
        c = s[i]
        if c == '\\':
            i += 2
            continue
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _links(text, hold):
    """抽取 [text](url) 链接；链接文本递归行内解析。无法配对则原样保留。"""
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c != '[':
            out.append(c)
            i += 1
            continue
        j = _find_close(text, i, '[', ']')
        if j == -1:
            out.append(c)
            i += 1
            continue
        if j + 1 >= n or text[j + 1] != '(':
            out.append(c)
            i += 1
            continue
        k = _find_close(text, j + 1, '(', ')')
        if k == -1:
            out.append(c)
            i += 1
            continue
        inner = text[j + 2:k]
        url = None
        if inner.startswith('<') and inner.endswith('>') and len(inner) >= 2:
            cand = inner[1:-1]
            if '<' not in cand and '>' not in cand:
                url = cand
        elif not re.search(r'\s', inner):
            url = inner
        if url is None:
            out.append(c)
            i += 1
            continue
        label = _inline(text[i + 1:j], hold)
        out.append(hold('<a href="%s">%s</a>' % (escape_attr(url), label)))
        i = k + 1
    return ''.join(out)


def _inline(text, hold):
    """行内解析。hold(html) 把已生成的 HTML 存入共享仓库并返回占位符。"""
    # 1) 行内代码（优先，内部不再做任何行内解析）
    def _code(m):
        return hold('<code>' + escape_html(m.group(2)) + '</code>')

    text = _CODE_RE.sub(_code, text)

    # 2) 链接（可包含行内代码 / 强调）
    text = _links(text, hold)

    # 3) 反斜杠转义
    def _esc(m):
        c = m.group(1)
        if c in _ESCAPABLE:
            return hold(escape_html(c))
        return hold(escape_html('\\' + c))

    text = re.sub(r'\\(.)', _esc, text, flags=re.S)

    # 4) & < > 实体转义
    text = escape_html(text)

    # 5) 强调：*** 先于 **/__ 先于 */_ ，避免 ** 被 * 抢走
    text = _EM_BOTH.sub(r'<em><strong>\1</strong></em>', text)
    text = _EM_STRONG.sub(r'<strong>\1</strong>', text)
    text = _EM_STRONG_U.sub(r'<strong>\1</strong>', text)
    text = _EM_EM.sub(r'<em>\1</em>', text)
    text = _EM_EM_U.sub(r'<em>\1</em>', text)

    return text


def inline(text):
    """行内解析入口：返回最终 HTML（占位符已还原）。"""
    store = []

    def hold(html):
        store.append(html)
        return '\x00%d\x00' % (len(store) - 1)

    out = _inline(text, hold)
    for _ in range(16):  # 处理「链接里套代码」这类嵌套占位符
        if not _PLACEHOLDER_RE.search(out):
            break
        out = _PLACEHOLDER_RE.sub(lambda m: store[int(m.group(1))], out)
    return out


# ---------------------------------------------------------------- 块级解析

_FENCE_RE = re.compile(r'^[ \t]{0,3}(`{3,})(.*)$')
_HEADING_RE = re.compile(r'^[ \t]{0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$')
_ITEM_RE = re.compile(r'^([ \t]*)([-*+]|\d{1,9}[.)])([ \t]+)(.*)$')
_TRAILING_HASH_RE = re.compile(r'[ \t]+#+[ \t]*$')


def _item_meta(m):
    """从 ITEM_RE 的 match 取出 (level, ordered, start, content)。"""
    indent = len(m.group(1).expandtabs(4))
    marker = m.group(2)
    ordered = marker[-1] in '.)' and marker[0].isdigit()
    start = 1
    if ordered:
        try:
            start = int(marker[:-1])
        except ValueError:
            start = 1
    return indent // 2, ordered, start, m.group(4)


def _collect_list(lines, i):
    """从 lines[i]（已知是列表项）开始收集整个列表，返回 (items, next_i)。"""
    items = []
    n = len(lines)
    while i < n:
        m = _ITEM_RE.match(lines[i])
        if not m:
            break
        level, ordered, start, first = _item_meta(m)
        content = [first]
        i += 1
        while i < n:
            if _ITEM_RE.match(lines[i]):
                break
            if not lines[i].strip():
                # 空行：向后看，若仍是列表项则跳过空行继续（松散列表按紧凑渲染）
                j = i
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and _ITEM_RE.match(lines[j]):
                    i = j
                    continue
                break
            if _FENCE_RE.match(lines[i]) or _HEADING_RE.match(lines[i]):
                break
            content.append(lines[i].strip())
            i += 1
        items.append((level, ordered, start, content))
    return items, i


def _build_tree(items):
    root = []
    stack = [(-1, root)]  # (level, container)
    for level, ordered, start, content in items:
        node = {'ordered': ordered, 'start': start,
                'content': content, 'children': []}
        while len(stack) > 1 and stack[-1][0] >= level:
            stack.pop()
        stack[-1][1].append(node)
        stack.append((level, node['children']))
    return root


def _render_list(nodes):
    out = []
    i = 0
    while i < len(nodes):
        ordered = nodes[i]['ordered']
        start = nodes[i]['start']
        if ordered:
            out.append('<ol start="%d">' % start if start != 1 else '<ol>')
        else:
            out.append('<ul>')
        while i < len(nodes) and nodes[i]['ordered'] == ordered:
            node = nodes[i]
            inner = inline('\n'.join(node['content']))
            if node['children']:
                inner += '\n' + _render_list(node['children']) + '\n'
            out.append('<li>' + inner + '</li>')
            i += 1
        out.append('</ol>' if ordered else '</ul>')
    return '\n'.join(out)


def convert(md_text):
    """把 Markdown 文本转成 HTML 片段。warnings 通过 stderr 由调用方处理。"""
    if '\x00' in md_text:
        md_text = md_text.replace('\x00', '')
    lines = md_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    out = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # 空行
        if not line.strip():
            i += 1
            continue

        # 围栏代码块
        m = _FENCE_RE.match(line)
        if m:
            fence = m.group(1)
            fence_ln = i + 1
            close_re = re.compile(r'^[ \t]{0,3}`{%d,}[ \t]*$' % len(fence))
            buf = []
            i += 1
            closed = False
            while i < n:
                if close_re.match(lines[i]):
                    closed = True
                    i += 1
                    break
                buf.append(lines[i])
                i += 1
            if not closed:
                sys.stderr.write(
                    'md2html: warning: 第 %d 行的代码围栏未闭合，已按到文件结尾处理\n'
                    % fence_ln)
            while len(buf) and not buf[-1].strip():
                buf.pop()  # 去掉结尾空行，使闭合/未闭合围栏表现一致
            out.append('<pre><code>' + escape_html('\n'.join(buf)) + '</code></pre>')
            continue

        # 标题
        m = _HEADING_RE.match(line)
        if m:
            content = m.group(2) or ''
            content = _TRAILING_HASH_RE.sub('', content)
            out.append('<h%d>%s</h%d>' % (len(m.group(1)), inline(content), len(m.group(1))))
            i += 1
            continue

        # 列表
        if _ITEM_RE.match(line):
            items, i = _collect_list(lines, i)
            out.append(_render_list(_build_tree(items)))
            continue

        # 段落
        buf = []
        while i < n and lines[i].strip():
            if _FENCE_RE.match(lines[i]) or _HEADING_RE.match(lines[i]) \
                    or _ITEM_RE.match(lines[i]):
                break
            buf.append(lines[i])
            i += 1
        out.append('<p>' + inline('\n'.join(buf)) + '</p>')

    return '\n'.join(out)


# ---------------------------------------------------------------- CLI

def main(argv):
    if len(argv) != 2 or argv[1] in ('-h', '--help'):
        sys.stderr.write('用法: python md2html.py <file.md>\n')
        return 0 if len(argv) == 2 else 2
    path = argv[1]
    try:
        with open(path, 'rb') as f:
            raw = f.read()
    except OSError as e:
        sys.stderr.write('md2html: error: 无法读取 %s: %s\n' % (path, e))
        return 1
    text = raw.decode('utf-8', errors='replace')
    try:  # 固定用 \n 换行，保证跨平台输出字节一致
        sys.stdout.reconfigure(newline='\n')
    except Exception:
        pass
    sys.stdout.write(convert(text) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
