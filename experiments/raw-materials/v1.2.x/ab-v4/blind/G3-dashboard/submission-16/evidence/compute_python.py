# 路径2（Python 独立复算 + WCAG 对比度计算）：
# 独立实现（与 Node/页面互不共享代码）复算 5 个筛选态指标 → out_python.json；
# 并计算页面全部文本前景/背景对比度 → out_contrast.json。
import json, re, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
with open(os.path.join(ROOT, 'index.html'), encoding='utf-8') as f:
    html = f.read()

data = re.findall(r'm:"([^"]+)",\s*v:(\d+)', html)
assert len(data) == 12, f'FAIL: expected 12 months, got {len(data)}'
data = [(m, int(v)) for m, v in data]

RANGES = {'all': (0, 11), 'q1': (0, 2), 'q2': (3, 5), 'q3': (6, 8), 'q4': (9, 11)}

def fmt_int(n):
    s = str(n)
    out = ''
    while len(s) > 3:
        out = ',' + s[-3:] + out
        s = s[:-3]
    return s + out

def fmt_avg(x):
    # 四舍五入到 1 位小数（正数场景）
    return f'{math.floor(x * 10 + 0.5) / 10:.1f}'

out = {}
for key, (a, b) in RANGES.items():
    rows = data[a:b + 1]
    total = sum(v for _, v in rows)
    peak = max(rows, key=lambda t: t[1])
    out[key] = {
        'count': len(rows), 'total': total, 'avg': total / len(rows),
        'peakMonth': peak[0], 'peakValue': peak[1],
        'months': [m for m, _ in rows], 'values': [v for _, v in rows],
        'expect': {
            'kpiTotal': fmt_int(total) + ' 万元',
            'kpiAvg': fmt_avg(total / len(rows)) + ' 万元/月',
            'kpiPeak': peak[0] + str(peak[1]) + ' 万元',
            'bars': len(rows),
            'barValues': [v for _, v in rows],
        },
    }

with open(os.path.join(HERE, 'out_python.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

# ---- WCAG 2.x 相对亮度与对比度 ----
def srgb(c):
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def lum(h):
    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    return 0.2126 * srgb(r) + 0.7152 * srgb(g) + 0.0722 * srgb(b)

def ratio(fg, bg):
    l1, l2 = sorted([lum(fg), lum(bg)], reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

pairs = [
    ('ink/card(正文+KPI数字)',      '#111827', '#ffffff'),
    ('muted/card(标签/单位)',       '#4b5563', '#ffffff'),
    ('white/activeBtn(选中筛选钮)', '#ffffff', '#1e40af'),
    ('tick/card(Y轴刻度)',          '#6b7280', '#ffffff'),
    ('mlabel/card(月份标签)',       '#374151', '#ffffff'),
    ('val/card(柱顶数值)',          '#111827', '#ffffff'),
    ('ink/body(标题)',              '#111827', '#f5f7fb'),
    ('muted/body(副标题/页脚)',     '#4b5563', '#f5f7fb'),
]
results, ok = [], True
for name, fg, bg in pairs:
    r = ratio(fg, bg)
    passed = r >= 4.5
    ok = ok and passed
    results.append({'pair': name, 'fg': fg, 'bg': bg, 'ratio': round(r, 2), 'pass': passed})

with open(os.path.join(HERE, 'out_contrast.json'), 'w', encoding='utf-8') as f:
    json.dump({'pairs': results, 'all_pass': ok}, f, ensure_ascii=False, indent=2)

print('OK compute_python: contrast_all_pass=' + str(ok) +
      ' all=' + out['all']['expect']['kpiTotal'] + ' avg=' + out['all']['expect']['kpiAvg'] +
      ' peak=' + out['all']['expect']['kpiPeak'])
if not ok:
    sys.exit(1)
