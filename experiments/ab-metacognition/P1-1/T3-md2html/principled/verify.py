#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md2html 独立验证脚本（第三方可复算）。

用法
    python verify.py                 # 验证同目录下的 md2html.py
    python verify.py <path/to/md2html.py>
    python verify.py --no-mutation   # 只跑功能/边界，不做变异杀伤测试

退出码：0 = 全部通过；1 = 存在失败；2 = 用法/加载错误。

设计要点（对应 skill 的「通过率不是鉴别力」）
    * CASES 按「输入域分段」编号组织（S1 正常 / S2 边界 / S3 畸形 / S4 任务书点名
      边界 / S5 安全注入 / S6 复合文档），每段至少一个用例触达。
    * 除定向断言外，额外做「变异杀伤测试」：把 md2html.py 按源码字符串替换成
      若干已知缺陷版本，要求本测试电池对每个变异体至少报错一次——证明断言有鉴别力，
      而不是恒真。
    * 无网络、无第三方依赖、无随机性（模糊测试用固定种子）。

产物：在脚本所在目录下 evidence/verify-report.txt 写入可复算报告。
"""

import importlib.util
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TARGET = os.path.join(HERE, "md2html.py")

# ---------------------------------------------------------------- 输入域分段
SEGMENTS = {
    "S1": "正常值：任务书要求的 8 项功能各自的最小正确输入",
    "S2": "边界值：空输入 / 仅空行 / 无尾换行 / 连续空行 / 标题紧贴正文 / 单行",
    "S3": "畸形值：未闭合围栏、未闭合行内代码、未闭合强调、7 个 #、孤立 [、空链接文本",
    "S4": "任务书点名边界（8 项）：逐条对应 TASK-T3.md『边界情况』",
    "S5": "安全注入：<script>、事件属性、引号截断属性值",
    "S6": "复合文档：多元素混合 + 完整 HTML 文档结构 + CLI 端到端",
}

# ---------------------------------------------------------------------- 用例
# 断言种类：eq = 与 render() 输出完全相等 / has = 包含子串 / hasnt = 不含子串
#           rx = 正则匹配
CASES = []


def case(cid, segment, desc, md, eq=None, has=(), hasnt=(), rx=()):
    CASES.append({
        "id": cid, "seg": segment, "desc": desc, "md": md,
        "eq": eq, "has": tuple(has), "hasnt": tuple(hasnt), "rx": tuple(rx),
    })


# --- S1 正常值：功能 1-8 ----------------------------------------------------
case("S1-01", "S1", "h1 最小用例", "# Title", eq="<h1>Title</h1>")
case("S1-02", "S1", "h6 最小用例", "###### Six", eq="<h6>Six</h6>")
case("S1-03", "S1", "六级标题全覆盖",
     "# 1\n## 2\n### 3\n#### 4\n##### 5\n###### 6",
     has=("<h1>1</h1>", "<h2>2</h2>", "<h3>3</h3>", "<h4>4</h4>",
          "<h5>5</h5>", "<h6>6</h6>"))
case("S1-04", "S1", "无序列表 -", "- a\n- b",
     eq="<ul>\n<li>a</li>\n<li>b</li>\n</ul>")
case("S1-05", "S1", "无序列表 *", "* a\n* b",
     eq="<ul>\n<li>a</li>\n<li>b</li>\n</ul>")
case("S1-06", "S1", "有序列表 1.", "1. a\n2. b",
     eq="<ol>\n<li>a</li>\n<li>b</li>\n</ol>")
case("S1-07", "S1", "围栏代码块", "```\nraw <b>\n```",
     eq="<pre><code>raw &lt;b&gt;\n</code></pre>")
case("S1-08", "S1", "围栏带语言标注", "```python\nx = 1\n```",
     eq='<pre><code class="language-python">x = 1\n</code></pre>')
case("S1-09", "S1", "行内代码", "use `code` here",
     eq="<p>use <code>code</code> here</p>")
case("S1-10", "S1", "粗体 **", "**b**", eq="<p><strong>b</strong></p>")
case("S1-11", "S1", "斜体 *", "*i*", eq="<p><em>i</em></p>")
case("S1-12", "S1", "粗体 __ 与斜体 _", "__b__ and _i_",
     eq="<p><strong>b</strong> and <em>i</em></p>")
case("S1-13", "S1", "粗斜体 ***", "***x***", eq="<p><em><strong>x</strong></em></p>")
case("S1-14", "S1", "链接", "[text](http://a)",
     eq='<p><a href="http://a">text</a></p>')
case("S1-15", "S1", "链接带标题", '[text](http://a "T")',
     eq='<p><a href="http://a" title="T">text</a></p>')
case("S1-16", "S1", "段落合并（连续非空行）", "line one\nline two",
     eq="<p>line one\nline two</p>")
case("S1-18", "S1", "链接地址含 & 只转义一次（不得出现 &amp;amp;）",
     "[t](http://a?x=1&y=2)",
     eq='<p><a href="http://a?x=1&amp;y=2">t</a></p>',
     hasnt=("&amp;amp;",))
case("S1-17", "S1", "CLI 端到端", None, rx=(r"^<!DOCTYPE html>",),
     has=('<meta charset="utf-8">', "<h1>CLI</h1>", "<title>cli-demo</title>"))

# --- S2 边界值 --------------------------------------------------------------
case("S2-01", "S2", "空文件", "", eq="")
case("S2-02", "S2", "只有空行", "\n\n\n", eq="")
case("S2-03", "S2", "只有空格与制表符", "   \n\t\n", eq="")
case("S2-04", "S2", "单行无尾换行", "abc", eq="<p>abc</p>")
case("S2-05", "S2", "标题与正文之间无空行", "# T\nbody",
     eq="<h1>T</h1>\n<p>body</p>")
case("S2-06", "S2", "正文与标题之间无空行", "body\n# T",
     eq="<p>body</p>\n<h1>T</h1>")
case("S2-07", "S2", "连续标题无空行", "# A\n## B",
     eq="<h1>A</h1>\n<h2>B</h2>")
case("S2-08", "S2", "多个空行分隔段落", "a\n\n\n\nb", eq="<p>a</p>\n<p>b</p>")
case("S2-09", "S2", "首尾大量空行", "\n\npara\n\n", eq="<p>para</p>")
case("S2-10", "S2", "仅有围栏且为空", "```\n```", eq="<pre><code></code></pre>")
case("S2-11", "S2", "行尾多余空格被清理", "# T   \nbody  ",
     eq="<h1>T</h1>\n<p>body</p>")
case("S2-12", "S2", "CRLF 换行归一", "# T\r\n\r\nbody\r\n",
     eq="<h1>T</h1>\n<p>body</p>")
case("S2-13", "S2", "空标题（只有 #）", "#", eq="<h1></h1>")
case("S2-14", "S2", "# 后无空格不是标题", "#Title", eq="<p>#Title</p>")

# --- S3 畸形输入 ------------------------------------------------------------
case("S3-01", "S3", "未闭合的 ``` 围栏", "```\nabc\ndef",
     eq="<pre><code>abc\ndef\n</code></pre>")
case("S3-02", "S3", "未闭合且内容为空", "```", eq="<pre><code></code></pre>")
case("S3-03", "S3", "未闭合行内代码按字面输出", "a ` b", eq="<p>a ` b</p>")
case("S3-04", "S3", "未闭合粗体按字面输出", "**x", eq="<p>**x</p>")
case("S3-05", "S3", "7 个 # 不是标题", "####### seven", eq="<p>####### seven</p>")
case("S3-06", "S3", "孤立 [ 保持字面", "a [ b", eq="<p>a [ b</p>")
case("S3-07", "S3", "空链接文本", "[](http://a)",
     eq='<p><a href="http://a"></a></p>')
case("S3-08", "S3", "链接缺右括号", "[t](http://a", eq="<p>[t](http://a</p>")
case("S3-09", "S3", "链接文本内含嵌套方括号", "[a [b] c](http://u)",
     eq='<p><a href="http://u">a [b] c</a></p>')
case("S3-10", "S3", "双反引号行内代码含单反引号", "``a`b``",
     eq="<p><code>a`b</code></p>")
case("S3-11", "S3", "列表标记后无内容", "- \n- b", has=("<li>",))
case("S3-12", "S3", "NUL 字符被剔除（避免与内部占位符冲突）", "a\x00b `c`",
     eq="<p>ab <code>c</code></p>")

# --- S4 任务书点名边界（8 项，逐条） ----------------------------------------
case("S4-01", "S4", "[边界1] 空文件", "", eq="")
case("S4-02", "S4", "[边界1] 只有空行", "\n\n\n", eq="")
case("S4-03", "S4", "[边界2] 标题与正文之间无空行", "# H\ntext\n## H2\ntext2",
     eq="<h1>H</h1>\n<p>text</p>\n<h2>H2</h2>\n<p>text2</p>")
case("S4-04", "S4", "[边界3] 未闭合 ``` 围栏（内容保留且隐式闭合）",
     "```js\nvar a = 1 < 2;",
     eq='<pre><code class="language-js">var a = 1 &lt; 2;\n</code></pre>')
case("S4-05", "S4", "[边界4] 行内代码内含 * 不得强调",
     "a `x*y*z` b", eq="<p>a <code>x*y*z</code> b</p>")
case("S4-06", "S4", "[边界4] 行内代码内含 _ 不得强调",
     "a `x_y_z` b", eq="<p>a <code>x_y_z</code> b</p>")
case("S4-07", "S4", "[边界4] 行内代码内含 ** 与 __",
     "`**not**` and `__not__`",
     eq="<p><code>**not**</code> and <code>__not__</code></p>")
case("S4-08", "S4", "[边界5] 链接文本含 ]", "[a]b](http://x)",
     eq='<p><a href="http://x">a]b</a></p>')
case("S4-09", "S4", "[边界5] 链接地址含空格（非法 -> 字面输出）",
     "[t](http://a b)", eq="<p>[t](http://a b)</p>")
case("S4-10", "S4", "[边界5] 链接地址用 <> 包裹可含空格",
     "[t](<http://a b>)", eq='<p><a href="http://a%20b">t</a></p>')
case("S4-11", "S4", "[边界6] 一层缩进嵌套列表（实现，非降级）",
     "- a\n  - b\n- c",
     eq="<ul>\n<li>a\n<ul>\n<li>b</li>\n</ul></li>\n<li>c</li>\n</ul>")
case("S4-12", "S4", "[边界6] 有序列表嵌套无序列表",
     "1. a\n   - b\n2. c",
     eq='<ol>\n<li>a\n<ul>\n<li>b</li>\n</ul></li>\n<li>c</li>\n</ol>')
case("S4-13", "S4", "[边界7] < > & 转义为实体", "a < b & c > d",
     eq="<p>a &lt; b &amp; c &gt; d</p>")
case("S4-14", "S4", "[边界7] 代码块内同样转义", "```\nif (a<b && c>d) {}\n```",
     eq="<pre><code>if (a&lt;b &amp;&amp; c&gt;d) {}\n</code></pre>")
case("S4-15", "S4", "[边界7] 已存在的实体不二次转义", "&amp;",
     eq="<p>&amp;amp;</p>")
case("S4-16", "S4", "[边界8] 围栏内不做行内解析", "```\n**b** `c` [t](u)\n```",
     eq="<pre><code>**b** `c` [t](u)\n</code></pre>")

# --- S5 安全注入 ------------------------------------------------------------
case("S5-01", "S5", "script 标签被转义", "<script>alert(1)</script>",
     has=("&lt;script&gt;",), hasnt=("<script>",))
case("S5-02", "S5", "事件处理器属性被转义",
     '<img src=x onerror=alert(1)>',
     has=("&lt;img",), hasnt=("<img",))
case("S5-03", "S5", "链接地址引号被转义（不截断属性）",
     '[t](http://a"onerror="alert(1))',
     has=("&quot;",), hasnt=('onerror="alert',))
case("S5-04", "S5", "链接标题中的引号被转义", '[t](http://a "say &quot;hi&quot;")',
     has=("<a ",), hasnt=('title="say "hi""',))
case("S5-05", "S5", "javascript: 协议原样保留（转义但不做白名单，声明见报告）",
     "[t](javascript:alert(1))",
     has=('<a href="javascript:alert(1)">',))

# --- S6 复合文档 ------------------------------------------------------------
COMPOSITE = (
    "# Title\n"
    "Intro with **bold**, *italic*, `code` and [link](http://x).\n"
    "\n"
    "## List\n"
    "- one\n"
    "- two\n"
    "  - nested\n"
    "\n"
    "1. first\n"
    "2. second\n"
    "\n"
    "```python\n"
    "def f(a, b):\n"
    "    return a < b and a > 0\n"
    "```\n"
    "\n"
    "Tail <paragraph> & done.\n"
)
case("S6-01", "S6", "复合文档：标题齐全", COMPOSITE,
     has=("<h1>Title</h1>", "<h2>List</h2>"))
case("S6-02", "S6", "复合文档：行内元素齐全", COMPOSITE,
     has=("<strong>bold</strong>", "<em>italic</em>", "<code>code</code>",
          '<a href="http://x">link</a>'))
case("S6-03", "S6", "复合文档：两种列表与嵌套", COMPOSITE,
     has=("<ul>\n<li>one</li>\n<li>two\n<ul>\n<li>nested</li>\n</ul></li>\n</ul>",
          "<ol>\n<li>first</li>\n<li>second</li>\n</ol>"))
case("S6-04", "S6", "复合文档：代码块内容原样且已转义", COMPOSITE,
     has=("<pre><code class=\"language-python\">def f(a, b):\n"
          "    return a &lt; b and a &gt; 0\n</code></pre>"))
case("S6-05", "S6", "复合文档：段落实体转义", COMPOSITE,
     has=("<p>Tail &lt;paragraph&gt; &amp; done.</p>"))
case("S6-06", "S6", "完整文档结构", None,
     rx=(r"^<!DOCTYPE html>\n<html lang=\"zh\">\n<head>\n<meta charset=\"utf-8\">\n"
         r"<title>[^\n]*</title>\n</head>\n<body>\n",))
case("S6-07", "S6", "缩进 4 空格代码块不在范围内（按段落处理，声明 D9）",
     "    code block", eq="<p>code block</p>")
case("S6-08", "S6", "'+' 与 '1)' 标记不在范围内（按段落处理，声明 D9）",
     "+ a\n1) b", eq="<p>+ a\n1) b</p>")
case("S6-09", "S6", "有序列表起始编号非 1 时输出 start 属性",
     "3. a\n4. b", eq='<ol start="3">\n<li>a</li>\n<li>b</li>\n</ol>')
case("S6-10", "S6", "无序与有序相邻自动拆分为两个列表",
     "- a\n1. b", eq="<ul>\n<li>a</li>\n</ul>\n<ol>\n<li>b</li>\n</ol>")

# --------------------------------------------------------------- 结构平衡检查
VOID_TAGS = {"br", "hr", "img", "meta", "link", "input", "col", "area",
             "base", "embed", "source", "track", "wbr", "param"}


class _Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if not self.stack:
            self.errors.append("多余的 </%s>" % tag)
        elif self.stack[-1] != tag:
            self.errors.append("期望 </%s> 实得 </%s>" % (self.stack[-1], tag))
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()


def structural_check(html):
    p = _Balance()
    p.feed(html)
    p.close()
    if p.stack:
        p.errors.append("未闭合: %s" % ",".join(p.stack))
    return (not p.errors), "; ".join(p.errors)


# -------------------------------------------------------------------- 模糊测试
FUZZ_ALPHABET = list("#-*`[]()<>&_ \n\n.1ab\t") + ["```", "\n```\n", "1. ", "- "]
FUZZ_SEED = 20260913
FUZZ_N = 2000


def run_fuzz(mod):
    """固定种子模糊测试：render() 不得抛异常，且输出标签必须平衡。"""
    rng = random.Random(FUZZ_SEED)
    failures = []
    for i in range(FUZZ_N):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(FUZZ_ALPHABET) for _ in range(n))
        try:
            out = mod.render(s)
            mod.render_document(s)
        except Exception as exc:                      # noqa: BLE001 - 有意捕获全部
            failures.append("fuzz#%d 抛异常 %s: %r" % (i, type(exc).__name__, s))
            continue
        ok, msg = structural_check("<body>%s</body>" % out)
        if not ok:
            failures.append("fuzz#%d 标签不平衡(%s): %r" % (i, msg, s))
        if "\x00" in out:
            failures.append("fuzz#%d 输出残留占位符 \\x00: %r" % (i, s))
    return failures


# ------------------------------------------------------------------ CLI 端到端
CLI_MD = "# CLI\n\n`x` and [l](http://a)\n"


def run_cli(target):
    """真实子进程跑一次 CLI：退出码、文档结构、内容、中文/UTF-8 输出。"""
    tmp = tempfile.mkdtemp(prefix="md2html-verify-")
    failures = []
    try:
        md_path = os.path.join(tmp, "cli-demo.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(CLI_MD)
        proc = subprocess.run(
            [sys.executable, target, md_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=tmp)
        if proc.returncode != 0:
            failures.append("CLI 退出码 %d，stderr=%r"
                            % (proc.returncode, proc.stderr[:200]))
            return failures
        out = proc.stdout.decode("utf-8")
        for expect in ("<!DOCTYPE html>", '<meta charset="utf-8">',
                       "<title>cli-demo</title>", "<h1>CLI</h1>",
                       "<code>x</code>", '<a href="http://a">l</a>'):
            if expect not in out:
                failures.append("CLI 输出缺少 %r" % expect)
        ok, msg = structural_check(out)
        if not ok:
            failures.append("CLI 输出标签不平衡: %s" % msg)

        # 中文文件名 + 中文内容：验证 UTF-8 读写不炸
        cn_path = os.path.join(tmp, "中文.md")
        with open(cn_path, "w", encoding="utf-8") as f:
            f.write("# 标题\n\n正文 **加粗** 与 `代码`\n")
        proc2 = subprocess.run([sys.executable, target, cn_path],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               cwd=tmp)
        if proc2.returncode != 0:
            failures.append("中文用例 CLI 退出码 %d，stderr=%r"
                            % (proc2.returncode, proc2.stderr[:200]))
        else:
            out2 = proc2.stdout.decode("utf-8")
            if "<h1>标题</h1>" not in out2 or "<strong>加粗</strong>" not in out2:
                failures.append("中文用例输出不符预期: %r" % out2[:200])

        # 不存在的文件：应有非零退出码与可读报错，而不是 traceback
        proc3 = subprocess.run([sys.executable, target, "no-such-file.md"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               cwd=tmp)
        if proc3.returncode == 0:
            failures.append("缺失文件应返回非零退出码")
        if b"Traceback" in proc3.stderr:
            failures.append("缺失文件应给出友好报错而非 traceback")

        # 非 UTF-8(GBK) 文件：应非零退出 + 友好报错，而不是 traceback
        gbk_path = os.path.join(tmp, "gbk.md")
        with open(gbk_path, "wb") as f:
            f.write("# 中文\n".encode("gbk"))
        proc4 = subprocess.run([sys.executable, target, gbk_path],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               cwd=tmp)
        if proc4.returncode == 0:
            failures.append("GBK 文件不应返回 0（本工具只接受 UTF-8）")
        if b"Traceback" in proc4.stderr:
            failures.append("GBK 文件应给出友好报错而非 traceback")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return failures


# ------------------------------------------------------------------ 变异杀伤
# 每个变异体是一处源码字符串替换；要求测试电池至少报错一次（被"杀死"）。
MUTANTS = [
    ("M1 取消实体转义",
     'return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")',
     "return s"),
    ("M2 取消行内代码占位符保护（行内代码参与强调解析）",
     "    text = _CODE_RE.sub(_stash, text)",
     "    text = text"),
    ("M3 标题级数放宽到 7 级",
     'r"^ {0,3}(#{1,6})(?:[ \\t]+(.*?))?[ \\t]*$"',
     'r"^ {0,3}(#{1,7})(?:[ \\t]+(.*?))?[ \\t]*$"'),
    ("M4 围栏内容也做行内解析（违反『原样保留』）",
     '            code = escape_text("\\n".join(buf))',
     '            code = inline("\\n".join(buf))'),
    ("M5 允许链接地址含空格（未用 <> 包裹也整体吞下、丢弃空格非法判定）",
     '        m = re.match(r"\\s*(\\S*)(.*)$", raw, re.S)\n'
     "        dest, rest = m.group(1), m.group(2)\n"
     '        if " " in dest or "\\t" in dest:\n'
     "            return None, None, None",
     '        m = re.match(r"\\s*(\\S*)(.*)$", raw, re.S)\n'
     '        dest, rest = raw.strip(), ""'),
    ("M6 链接文本遇到第一个 ] 就结束（无法含 ]）",
     "                if k + 1 < n and text[k + 1] == \"(\":",
     "                if True:"),
    ("M7 嵌套列表强制压平为同一层级",
     '            items.append({"level": indent // 2, "ordered": ordered,',
     '            items.append({"level": 0, "ordered": ordered,'),
    ("M8 属性值不转义双引号",
     '    return s.replace(\'"\', "&quot;")',
     "    return s"),
    ("M10 链接地址二次转义（& -> &amp;amp;）",
     "        attr = ' href=\"%s\"' % quote_attr(dest)",
     "        attr = ' href=\"%s\"' % escape_attr(dest)"),
    ("M9 有序列表丢失 start 属性",
     '        attrs = \' start="%d"\' % start_num if (ordered and start_num != 1) else ""',
     '        attrs = ""'),
]


def load_module(path):
    spec = importlib.util.spec_from_file_location("md2html_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_suite(mod, target_path, with_cli=True):
    """对给定模块跑完整电池，返回 [(name, ok, msg), ...]。"""
    results = []

    def record(name, failures):
        results.append((name, not failures, "; ".join(failures)))

    for c in CASES:
        fails = []
        if c["md"] is None:
            if c["id"] == "S1-17":                     # CLI 用例：由 run_cli 覆盖
                continue
            if c["id"] == "S6-06":                     # 完整文档结构
                doc = mod.render_document("# T\n\nx\n")
                if not re.search(c["rx"][0], doc):
                    fails.append("正则未匹配: %s" % c["rx"][0])
                ok, msg = structural_check(doc)
                if not ok:
                    fails.append("标签不平衡: %s" % msg)
                record("%s %s" % (c["id"], c["desc"]), fails)
            continue
        try:
            got = mod.render(c["md"])
        except Exception as exc:                       # noqa: BLE001
            record("%s %s" % (c["id"], c["desc"]),
                   ["render() 抛异常 %s: %s" % (type(exc).__name__, exc)])
            continue
        if c["eq"] is not None and got != c["eq"]:
            fails.append("期望 %r\n                实得 %r" % (c["eq"], got))
        for sub in c["has"]:
            if sub not in got:
                fails.append("缺少子串 %r（实得 %r）" % (sub, got))
        for sub in c["hasnt"]:
            if sub in got:
                fails.append("不应包含 %r（实得 %r）" % (sub, got))
        for pat in c["rx"]:
            if not re.search(pat, got):
                fails.append("正则未匹配 %r（实得 %r）" % (pat, got))
        ok, msg = structural_check("<body>%s</body>" % got)
        if not ok:
            fails.append("标签不平衡: %s" % msg)
        record("%s %s" % (c["id"], c["desc"]), fails)

    record("FUZZ 固定种子模糊测试(%d 例)" % FUZZ_N, run_fuzz(mod))
    if with_cli:
        record("CLI 端到端（子进程 + 中文 + 缺失文件）", run_cli(target_path))
    return results


def run_mutation(source_path):
    """变异杀伤测试：返回 [(mutant, killed, detail), ...]。"""
    with open(source_path, "r", encoding="utf-8") as f:
        src = f.read()
    outcomes = []
    tmpdir = tempfile.mkdtemp(prefix="md2html-mut-")
    try:
        for idx, (name, old, new) in enumerate(MUTANTS):
            if old not in src:
                outcomes.append((name, False,
                                 "变异点源码未命中，变异体无效（视为未通过）"))
                continue
            mutated = src.replace(old, new, 1)
            mpath = os.path.join(tmpdir, "mutant_%d.py" % idx)
            with open(mpath, "w", encoding="utf-8") as f:
                f.write(mutated)
            try:
                mod = load_module(mpath)
                res = run_suite(mod, mpath, with_cli=False)
            except Exception as exc:                   # noqa: BLE001
                outcomes.append((name, True,
                                 "变异体无法导入/崩溃(%s) -> 计为被杀死" % exc))
                continue
            failed = [n for n, ok, _ in res if not ok]
            outcomes.append((name, bool(failed),
                             "杀死用例: %s" % ("; ".join(failed[:6]) if failed
                                               else "无（断言未能发现该缺陷！）")))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return outcomes


# ------------------------------------------------------------------------ 主流程
def main(argv):
    args = [a for a in argv if a != "--no-mutation"]
    do_mutation = "--no-mutation" not in argv
    target = args[0] if args else DEFAULT_TARGET
    target = os.path.abspath(target)
    if not os.path.isfile(target):
        sys.stderr.write("verify: 找不到目标文件 %s\n" % target)
        return 2

    try:
        mod = load_module(target)
    except Exception as exc:                           # noqa: BLE001
        sys.stderr.write("verify: 加载 %s 失败: %s\n" % (target, exc))
        return 2

    results = run_suite(mod, target, with_cli=True)
    passed = sum(1 for _, ok, _ in results if ok)
    failed_items = [(n, m) for n, ok, m in results if not ok]

    lines = []
    lines.append("md2html 验证报告")
    lines.append("=" * 72)
    lines.append("目标文件: %s" % target)
    lines.append("Python   : %s" % sys.version.split()[0])
    lines.append("复算命令: python verify.py %s" % os.path.basename(target))
    lines.append("")
    lines.append("一、输入域分段（用例设计前置枚举）")
    for k in sorted(SEGMENTS):
        lines.append("  %s: %s" % (k, SEGMENTS[k]))
    lines.append("")
    lines.append("二、用例结果 (%d/%d 通过)" % (passed, len(results)))
    for name, ok, msg in results:
        lines.append("  [%s] %s%s" % ("PASS" if ok else "FAIL", name,
                                      "" if ok else "\n        -> %s" % msg))
    lines.append("")

    mutation_score = None
    if do_mutation:
        outcomes = run_mutation(target)
        killed = sum(1 for _, k, _ in outcomes if k)
        mutation_score = (killed, len(outcomes))
        lines.append("三、变异杀伤测试（证明断言有鉴别力） %d/%d 被杀死"
                     % (killed, len(outcomes)))
        for name, k, detail in outcomes:
            lines.append("  [%s] %s\n        -> %s"
                         % ("KILLED" if k else "SURVIVED", name, detail))
        lines.append("")

    total_fail = len(failed_items)
    if mutation_score:
        total_fail += (mutation_score[1] - mutation_score[0])
    lines.append("四、结论: %s（失败 %d 项）"
                 % ("ALL GREEN" if total_fail == 0 else "FAILED", total_fail))

    report = "\n".join(lines) + "\n"
    outdir = os.path.join(HERE, "evidence")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "verify-report.txt"), "w",
              encoding="utf-8") as f:
        f.write(report)
    sys.stdout.write(report)
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
