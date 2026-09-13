"""日期工具：给出某个日期的下一个日历日。

用法：python next_date.py YYYY-MM-DD
"""

def next_date(s):
    """返回输入日期的下一个日历日，格式 YYYY-MM-DD。"""
    y, m, d = map(int, s.split("-"))
    d += 1
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if d > days[m - 1]:
        d = 1
        m += 1
        if m > 12:
            m = 1
            y += 1
    return "%04d-%02d-%02d" % (y, m, d)

if __name__ == "__main__":
    import sys
    print(next_date(sys.argv[1]))
