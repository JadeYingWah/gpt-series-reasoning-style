#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify.py —— md2html.py 的独立可复算验证脚本（零依赖，只用标准库）

第三方复算方式（在 noskill/ 目录下）：
    python verify.py
或指定 Python 3 解释器：
    py -3 verify.py

做什么：
  1. 对 40+ 个用例（功能 + 边界）做 **精确字符串比对**：convert(md) == expected
  2. 对需要观察 stderr / 退出码的用例走 **CLI 子进程** 真实执行
  3. 把每个用例的 输入 md / 期望 html / 实际 html 落盘到 cases/ 目录，供人工 diff
  4. 汇总写 verify-report.txt，全部通过时退出码 0，有失败退出码 1

预期值全部写在下面的 CASES 表里（来自 TASK-T3.md 的功能与边界条款），
不是"实际输出回抄"，可逐条人工复核。
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASES_DIR = os.path.join(HERE, 'cases')
REPORT = os.path.join(HERE, 'verify-report.txt')

sys.path.insert(0, HERE)
import md2html  # noqa: E402


# (编号, 类别, 说明, 输入 markdown, 期望 HTML)
CASES = [
    # ---------------- 空 / 空行 ----------------
    ('F-01', '边界', '空文件', '', ''),
    ('F-02', '边界', '只有空行', '\n\n   \n\t\n\n', ''),

    # ---------------- 标题 ----------------
    ('F-03', '功能', 'h1~h6 全部级别',
     '# A\n## B\n### C\n#### D\n##### E\n###### F\n',
     '<h1>A</h1>\n<h2>B</h2>\n<h3>C</h3>\n<h4>D</h4>\n<h5>E</h5>\n<h6>F</h6>'),
    ('F-04', '边界', '7 个 # 不是标题',
     '####### G\n', '<p>####### G</p>'),
    ('F-05', '边界', '# 后无空格不是标题',
     '#NoSpace\n', '<p>#NoSpace</p>'),
    ('F-06', '边界', '标题与正文之间无空行',
     '# T\nbody\n', '<h1>T</h1>\n<p>body</p>'),
    ('F-07', '功能', '标题行尾闭合 # 被去掉',
     '# T #\n', '<h1>T</h1>'),
    ('F-08', '功能', '只有 # 的空标题',
     '#\n', '<h1></h1>'),

    # ---------------- 列表 ----------------
    ('F-09', '功能', '无序列表 -',
     '- a\n- b\n', '<ul>\n<li>a</li>\n<li>b</li>\n</ul>'),
    ('F-10', '功能', '无序列表 *',
     '* a\n* b\n', '<ul>\n<li>a</li>\n<li>b</li>\n</ul>'),
    ('F-11', '功能', '无序列表 +',
     '+ a\n+ b\n', '<ul>\n<li>a</li>\n<li>b</li>\n</ul>'),
    ('F-12', '功能', '有序列表 1.',
     '1. a\n2. b\n', '<ol>\n<li>a</li>\n<li>b</li>\n</ol>'),
    ('F-13', '功能', '有序列表非 1 起始（start 属性）',
     '3. a\n4. b\n', '<ol start="3">\n<li>a</li>\n<li>b</li>\n</ol>'),
    ('F-14', '功能', '有序列表 N) 形式',
     '1) a\n2) b\n', '<ol>\n<li>a</li>\n<li>b</li>\n</ol>'),
    ('F-15', '边界', '嵌套列表（缩进 2 空格 = 1 层）',
     '- a\n  - b\n- c\n',
     '<ul>\n<li>a\n<ul>\n<li>b</li>\n</ul>\n</li>\n<li>c</li>\n</ul>'),
    ('F-16', '边界', '松散列表（项间空行）仍为一个列表',
     '- a\n\n- b\n', '<ul>\n<li>a</li>\n<li>b</li>\n</ul>'),
    ('F-17', '边界', '列表遇标题即结束',
     '- a\n# H\n', '<ul>\n<li>a</li>\n</ul>\n<h1>H</h1>'),
    ('F-18', '边界', '空行 + 缩进结束列表并入段落',
     '- a\n\nplain\n', '<ul>\n<li>a</li>\n</ul>\n<p>plain</p>'),
    ('F-19', '功能', '有序列表内嵌无序列表',
     '1. a\n   - b\n2. c\n',
     '<ol>\n<li>a\n<ul>\n<li>b</li>\n</ul>\n</li>\n<li>c</li>\n</ol>'),

    # ---------------- 代码块 ----------------
    ('C-01', '功能', '围栏代码块内容原样（** 不解析）',
     '```\ncode **x**\n```\n', '<pre><code>code **x**</code></pre>'),
    ('C-02', '功能', '围栏内 < > & 转义为实体',
     '```\n<div>a & b</div>\n```\n',
     '<pre><code>&lt;div&gt;a &amp; b&lt;/div&gt;</code></pre>'),
    ('C-03', '功能', '围栏保留换行与缩进',
     '```python\ndef f():\n    return 1\n```\n',
     '<pre><code>def f():\n    return 1</code></pre>'),
    ('C-04', '边界', '空围栏',
     '```\n```\n', '<pre><code></code></pre>'),
    ('C-05', '边界', '未闭合围栏按到文件结尾处理',
     '```\nabc\n', '<pre><code>abc</code></pre>'),
    ('C-06', '功能', '围栏后正常段落继续',
     '```\nx\n```\ntail\n', '<pre><code>x</code></pre>\n<p>tail</p>'),

    # ---------------- 行内 ----------------
    ('I-01', '边界', '行内代码内含 * 与 _，不被强调',
     '`a *b* _c_`\n', '<p><code>a *b* _c_</code></p>'),
    ('I-02', '功能', '行内代码内 < > 转义',
     '`<div>`\n', '<p><code>&lt;div&gt;</code></p>'),
    ('I-03', '功能', '粗体 **b**',
     '**b**\n', '<p><strong>b</strong></p>'),
    ('I-04', '功能', '斜体 *i*',
     '*i*\n', '<p><em>i</em></p>'),
    ('I-05', '功能', '粗斜体 ***x***',
     '***x***\n', '<p><em><strong>x</strong></em></p>'),
    ('I-06', '功能', '粗体 __b__',
     '__b__\n', '<p><strong>b</strong></p>'),
    ('I-07', '功能', '斜体 _i_',
     '_i_\n', '<p><em>i</em></p>'),
    ('I-08', '功能', '链接基本形式',
     '[t](http://x.com)\n', '<p><a href="http://x.com">t</a></p>'),
    ('I-09', '边界', '链接文本含 ]（用 \\] 转义）',
     '[a\\]b](u)\n', '<p><a href="u">a]b</a></p>'),
    ('I-10', '边界', '链接文本含未转义 ] -> 不识别为链接',
     '[a]b](u)\n', '<p>[a]b](u)</p>'),
    ('I-11', '边界', '链接文本含嵌套方括号',
     '[a[b]c](u)\n', '<p><a href="u">a[b]c</a></p>'),
    ('I-12', '边界', '链接地址含空格（尖括号形式）',
     '[t](<a b>)\n', '<p><a href="a b">t</a></p>'),
    ('I-13', '边界', '链接地址含裸空格 -> 不识别为链接',
     '[t](a b)\n', '<p>[t](a b)</p>'),
    ('I-14', '功能', '链接地址中的 & 转义为 &amp;',
     '[a](http://x?p=1&q=2)\n', '<p><a href="http://x?p=1&amp;q=2">a</a></p>'),
    ('I-15', '边界', '未闭合的强调按字面输出',
     'a **b\n', '<p>a **b</p>'),
    ('I-16', '边界', '反斜杠转义 \\* 不生成强调',
     '\\*not em\\*\n', '<p>*not em*</p>'),
    ('I-17', '边界', '词内下划线 snake_case 不被强调',
     'foo_bar_baz\n', '<p>foo_bar_baz</p>'),
    ('I-18', '边界', '已有实体 &amp; 不被二次转义破坏',
     '&amp;\n', '<p>&amp;amp;</p>'),
    ('I-19', '功能', '多个行内片段同段共存',
     '**b** and *i* and `c` and [l](u)\n',
     '<p><strong>b</strong> and <em>i</em> and <code>c</code> '
     'and <a href="u">l</a></p>'),

    # ---------------- 段落 / 转义 ----------------
    ('P-01', '功能', '连续非空行合并为一个 <p>',
     'l1\nl2\n', '<p>l1\nl2</p>'),
    ('P-02', '功能', '空行分隔出多个 <p>',
     'p1\n\np2\n', '<p>p1</p>\n<p>p2</p>'),
    ('E-01', '边界', '正文 < > & 转义',
     'a < b & c > d\n', '<p>a &lt; b &amp; c &gt; d</p>'),
    ('E-02', '边界', '标题内 < > & 转义',
     '# a & b < c\n', '<h1>a &amp; b &lt; c</h1>'),
    ('E-03', '边界', '内联脚本标签被转义（不产生可执行标签）',
     '<script>alert(1)</script>\n',
     '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>'),
    ('E-04', '边界', 'CRLF 换行输入正常解析',
     '# a\r\n\r\n- b\r\n', '<h1>a</h1>\n<ul>\n<li>b</li>\n</ul>'),
    ('E-05', '边界', 'NUL 字符被丢弃',
     'a\x00b\n', '<p>ab</p>'),
    ('E-06', '边界', '不支持的语法按字面输出（引用/表格/分隔线/缩进块）',
     '> q\n\n|a|b|\n\n---\n\n    ind\n',
     '<p>&gt; q</p>\n<p>|a|b|</p>\n<p>---</p>\n<p>    ind</p>'),

    # ---------------- 混合 ----------------
    ('M-01', '功能', '链接文本内含强调与行内代码',
     '[**b** `c`](u)\n',
     '<p><a href="u"><strong>b</strong> <code>c</code></a></p>'),
    ('M-02', '功能', '列表项内含行内代码与链接',
     '- a `c` [l](u)\n',
     '<ul>\n<li>a <code>c</code> <a href="u">l</a></li>\n</ul>'),
    ('M-03', '功能', '标题内含强调与行内代码',
     '# **B** `c`\n', '<h1><strong>B</strong> <code>c</code></h1>'),
    ('M-04', '功能', '综合样例（标题/列表/代码/段落/链接）',
     '# Doc\n'
     '\n'
     'Intro **bold**.\n'
     '\n'
     '- item `x`\n'
     '- item [y](http://y)\n'
     '\n'
     '```\nraw **not bold**\n```\n'
     '\n'
     'End & fin\n',
     '<h1>Doc</h1>\n'
     '<p>Intro <strong>bold</strong>.</p>\n'
     '<ul>\n<li>item <code>x</code></li>\n'
     '<li>item <a href="http://y">y</a></li>\n</ul>\n'
     '<pre><code>raw **not bold**</code></pre>\n'
     '<p>End &amp; fin</p>'),
]


def _write(name, content):
    path = os.path.join(CASES_DIR, name)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)


def run_unit_cases(lines):
    if not os.path.isdir(CASES_DIR):
        os.makedirs(CASES_DIR)
    passed = failed = 0
    failures = []
    for cid, cat, desc, md, expected in CASES:
        try:
            actual = md2html.convert(md)
        except Exception as e:  # 崩溃也算失败
            actual = '<EXCEPTION: %r>' % (e,)
        ok = (actual == expected)
        _write(cid + '.md', md)
        _write(cid + '.expected.html', expected)
        _write(cid + '.actual.html', actual)
        if ok:
            problems = check_balance(actual)
            xml_err = check_xml_wellformed(actual)
            if xml_err:
                problems.append('XML 不良构: %s' % xml_err)
            if problems:
                ok = False
                lines.append('[FAIL] %s (%s) %s' % (cid, cat, desc))
                lines.append('       输出与预期一致但标签不配平: %s' % '; '.join(problems))
                failed += 1
                failures.append((cid, desc, md, expected, actual))
                continue
            passed += 1
            lines.append('[PASS] %s (%s) %s' % (cid, cat, desc))
        else:
            failed += 1
            failures.append((cid, desc, md, expected, actual))
            lines.append('[FAIL] %s (%s) %s' % (cid, cat, desc))
            lines.append('       input    : %r' % md)
            lines.append('       expected : %r' % expected)
            lines.append('       actual   : %r' % actual)
    return passed, failed, failures


import re
import time
import xml.etree.ElementTree as ET

# 只要求「不崩溃 / 有界耗时 / 标签配平」的对抗性输入
HOSTILE = {
    'stars-2000': '*' * 2000,
    'underscores-2000': '_' * 2000,
    'backticks-500': '`' * 500,
    'brackets-2000': '[' * 2000 + 'a',
    'bracket-pairs-2000': '[a]' * 2000 + '(u)',
    'link-unclosed': '[a](' + 'u' * 5000,
    'star-mix-3000': '**a** ' * 3000,
    'em-triple-2000': '***a*** ' * 2000,
    'long-line-100k': 'x' * 100000,
    'backslashes-1000': '\\' * 1000,
    'deep-list-60': '\n'.join('  ' * i + '- item %d' % i for i in range(60)),
    'fences-500': '```\ncode\n```\n' * 500,
    'cjk': '# 中文标题 **粗体** `代码` [链接](http://例.com)',
    'unclosed-fence': '```\nabc',
    'lone-bracket-link': '[a]b](u) (u] [ ( ] ) \\ ]',
}

_TAG_PAIRS = ['p', 'ul', 'ol', 'li', 'pre', 'code', 'strong', 'em', 'a',
              'h1', 'h2', 'h3', 'h4', 'h5', 'h6']


def check_xml_wellformed(html):
    """把片段包进 <root> 用 XML 解析器解析：能过 = 标签严格正确嵌套（无交叉）。"""
    try:
        ET.fromstring('<root>' + html + '</root>')
        return None
    except Exception as e:
        return str(e)


def check_balance(html):
    """检查每种标签的开/闭数量一致，返回问题描述列表（空列表=配平）。"""
    problems = []
    for tag in _TAG_PAIRS:
        opened = len(re.findall(r'<%s[ >]' % tag, html))
        closed = len(re.findall(r'</%s>' % tag, html))
        if opened != closed:
            problems.append('%s: open=%d close=%d' % (tag, opened, closed))
    return problems


def run_robustness(lines):
    """对抗输入：不得抛异常、单条 < 2s、输出标签必须配平。"""
    passed = failed = 0
    for name, md in sorted(HOSTILE.items()):
        t0 = time.time()
        try:
            out = md2html.convert(md)
        except Exception as e:
            failed += 1
            lines.append('[FAIL] R-%s 抛出异常: %r' % (name, e))
            continue
        dt = time.time() - t0
        problems = check_balance(out)
        xml_err = check_xml_wellformed(out)
        if xml_err:
            problems.append('XML 不良构: %s' % xml_err)
        _write('R-' + name + '.md', md)
        _write('R-' + name + '.actual.html', out)
        if problems:
            failed += 1
            lines.append('[FAIL] R-%s 标签不配平: %s' % (name, '; '.join(problems)))
        elif dt >= 2.0:
            failed += 1
            lines.append('[FAIL] R-%s 耗时过长 %.2fs' % (name, dt))
        else:
            passed += 1
            lines.append('[PASS] R-%s 无异常/%.3fs/标签配平 (len=%d)'
                         % (name, dt, len(out)))
    return passed, failed


def run_cli_cases(lines):
    """CLI 子进程用例：(编号, 说明, argv, stdin文件内容orNone, 期望码, stdout判定lambda, stderr子串)"""
    tmp = os.path.join(CASES_DIR, '_cli_input.md')
    _write('_cli_input.md', '# H\n\n- a\n- b\n\n```\nx\n```\n')
    expect_stdout = ('<h1>H</h1>\n<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n'
                     '<pre><code>x</code></pre>\n')

    cli = [
        ('CLI-01', 'CLI 基本输出 = convert() + 换行',
         [sys.executable, os.path.join(HERE, 'md2html.py'), tmp],
         0, expect_stdout, None),
        ('CLI-02', '未闭合围栏：退出码 0 且 stderr 有警告',
         [sys.executable, os.path.join(HERE, 'md2html.py'),
          _mk('_cli_unclosed.md', '```\nabc\n')],
         0, '<pre><code>abc</code></pre>\n', '未闭合'),
        ('CLI-03', '空文件：退出码 0，输出仅一个换行',
         [sys.executable, os.path.join(HERE, 'md2html.py'),
          _mk('_cli_empty.md', '')],
         0, '\n', None),
        ('CLI-04', '文件不存在：退出码 1，stderr 报错',
         [sys.executable, os.path.join(HERE, 'md2html.py'),
          os.path.join(CASES_DIR, '_nope_missing_file.md')],
         1, '', 'error'),
        ('CLI-05', '无参数：退出码 2',
         [sys.executable, os.path.join(HERE, 'md2html.py')],
         2, '', '用法'),
    ]
    passed = failed = 0
    for cid, desc, argv, exp_code, exp_out, exp_err in cli:
        p = subprocess.run(argv, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, cwd=HERE)
        out = p.stdout.decode('utf-8', errors='replace')
        err = p.stderr.decode('utf-8', errors='replace')
        ok = (p.returncode == exp_code) and (out == exp_out)
        if exp_err is not None:
            ok = ok and (exp_err in err)
        if ok:
            passed += 1
            lines.append('[PASS] %s (CLI) %s' % (cid, desc))
        else:
            failed += 1
            lines.append('[FAIL] %s (CLI) %s' % (cid, desc))
            lines.append('       returncode: %r (want %r)' % (p.returncode, exp_code))
            lines.append('       stdout    : %r' % out)
            lines.append('       want stdout: %r' % exp_out)
            lines.append('       stderr    : %r (want contains %r)' % (err, exp_err))
    return passed, failed


def _mk(name, content):
    _write(name, content)
    return os.path.join(CASES_DIR, name)


def main():
    lines = []
    lines.append('md2html 验证报告')
    lines.append('python   : %s' % sys.version.split()[0])
    lines.append('md2html  : v%s (%s)' % (md2html.__version__,
                                          os.path.join(HERE, 'md2html.py')))
    lines.append('')
    up, uf, failures = run_unit_cases(lines)
    lines.append('')
    rp, rf = run_robustness(lines)
    lines.append('')
    cp, cf = run_cli_cases(lines)
    lines.append('')
    total, tf = up + cp + rp, uf + cf + rf
    lines.append('汇总: %d 个用例, 通过 %d, 失败 %d  (单元 %d/%d, 对抗 %d/%d, CLI %d/%d)'
                 % (total, up + cp + rp, tf, up, up + uf, rp, rp + rf, cp, cp + cf))
    lines.append('结果: %s' % ('ALL PASS' if tf == 0 else 'HAS FAILURE'))
    lines.append('用例落盘目录: %s' % CASES_DIR)

    text = '\n'.join(lines) + '\n'
    with open(REPORT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    sys.stdout.write(text)
    return 0 if tf == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
