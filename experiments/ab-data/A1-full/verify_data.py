import csv
from collections import defaultdict

with open(r'<实验根目录>\ab-data\sales_data.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print(f'总记录数: {len(rows)}')
print(f'月份数: {len(set(r["月份"] for r in rows))}')
print(f'产品类别: {sorted(set(r["产品类别"] for r in rows))}')
print(f'地区: {sorted(set(r["地区"] for r in rows))}')
print()

total_sales = sum(int(r['销售额']) for r in rows)
total_cost = sum(int(r['成本']) for r in rows)
total_profit = sum(int(r['利润']) for r in rows)
total_orders = sum(int(r['订单数']) for r in rows)
total_customers = sum(int(r['客户数']) for r in rows)
print(f'总销售额: {total_sales:,}')
print(f'总成本: {total_cost:,}')
print(f'总利润: {total_profit:,}')
print(f'利润率: {total_profit/total_sales*100:.1f}%')
print(f'总订单数: {total_orders:,}')
print(f'总客户数: {total_customers:,}')
print(f'客单价: {total_sales/total_orders:.1f}')
print()

by_cat = defaultdict(lambda: {'sales':0,'profit':0,'orders':0,'customers':0})
for r in rows:
    c = r['产品类别']
    by_cat[c]['sales'] += int(r['销售额'])
    by_cat[c]['profit'] += int(r['利润'])
    by_cat[c]['orders'] += int(r['订单数'])
    by_cat[c]['customers'] += int(r['客户数'])
print('按类别:')
for c, d in sorted(by_cat.items()):
    print(f'  {c}: 销售额={d["sales"]:,} 占比={d["sales"]/total_sales*100:.1f}% 利润率={d["profit"]/d["sales"]*100:.1f}% 客单价={d["sales"]/d["orders"]:.0f}')
print()

by_region = defaultdict(lambda: {'sales':0,'profit':0,'orders':0,'customers':0})
for r in rows:
    reg = r['地区']
    by_region[reg]['sales'] += int(r['销售额'])
    by_region[reg]['profit'] += int(r['利润'])
    by_region[reg]['orders'] += int(r['订单数'])
    by_region[reg]['customers'] += int(r['客户数'])
print('按地区:')
for reg, d in sorted(by_region.items()):
    print(f'  {reg}: 销售额={d["sales"]:,} 占比={d["sales"]/total_sales*100:.1f}% 客单价={d["sales"]/d["orders"]:.0f}')
print()

by_month = defaultdict(int)
for r in rows:
    by_month[r['月份']] += int(r['销售额'])
print('月度销售额:')
prev = None
for m in sorted(by_month):
    chg = f'{(by_month[m]-prev)/prev*100:+.1f}%' if prev else '-'
    print(f'  {m}: {by_month[m]:,} ({chg})')
    prev = by_month[m]

# 季度
print()
quarters = {'Q1':['2025-01','2025-02','2025-03'], 'Q2':['2025-04','2025-05','2025-06'],
            'Q3':['2025-07','2025-08','2025-09'], 'Q4':['2025-10','2025-11','2025-12']}
print('季度销售额:')
for q, months in quarters.items():
    s = sum(by_month[m] for m in months)
    print(f'  {q}: {s:,} ({s/total_sales*100:.1f}%)')

# 地区x类别交叉
print()
print('地区x类别交叉(销售额):')
cross = defaultdict(int)
for r in rows:
    cross[(r['地区'], r['产品类别'])] += int(r['销售额'])
for reg in ['华东','华南','华北']:
    line = f'  {reg}:'
    for cat in ['电子产品','服装','食品']:
        line += f' {cat}={cross[(reg,cat)]:,}'
    print(line)
