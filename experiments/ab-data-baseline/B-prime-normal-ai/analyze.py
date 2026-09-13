import csv
from collections import defaultdict

data = []
with open(r'<实验根目录>\ab-data-baseline\B-prime-normal-ai\sales_data.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        row['数量'] = int(row['数量'])
        row['单价'] = float(row['单价'])
        row['销售额'] = float(row['销售额'])
        row['成本'] = float(row['成本'])
        data.append(row)

total_sales = sum(r['销售额'] for r in data)
total_cost = sum(r['成本'] for r in data)
total_profit = total_sales - total_cost
profit_margin = total_profit / total_sales * 100
total_qty = sum(r['数量'] for r in data)
avg_order = total_sales / len(data)

print('=== 基础指标 ===')
print(f'记录数: {len(data)}')
print(f'总销售额: {total_sales:,.2f}')
print(f'总成本: {total_cost:,.2f}')
print(f'总利润: {total_profit:,.2f}')
print(f'利润率: {profit_margin:.1f}%')
print(f'总销量: {total_qty}')
print(f'平均客单价: {avg_order:,.2f}')

print('\n=== 按区域 ===')
by_region = defaultdict(lambda: {'sales':0,'qty':0,'count':0})
for r in data:
    by_region[r['区域']]['sales'] += r['销售额']
    by_region[r['区域']]['qty'] += r['数量']
    by_region[r['区域']]['count'] += 1
for region, v in sorted(by_region.items(), key=lambda x: -x[1]['sales']):
    pct = v['sales']/total_sales*100
    print(f'{region}: 销售额{v["sales"]:,.0f} ({pct:.1f}%), 订单{v["count"]}')

print('\n=== 按产品 ===')
by_product = defaultdict(lambda: {'sales':0,'qty':0,'profit':0})
for r in data:
    by_product[r['产品']]['sales'] += r['销售额']
    by_product[r['产品']]['qty'] += r['数量']
    by_product[r['产品']]['profit'] += r['销售额'] - r['成本']
for product, v in sorted(by_product.items(), key=lambda x: -x[1]['sales']):
    margin = v['profit']/v['sales']*100
    print(f'{product}: 销售额{v["sales"]:,.0f}, 利润率{margin:.1f}%')

print('\n=== 按渠道 ===')
by_channel = defaultdict(lambda: {'sales':0,'count':0})
for r in data:
    by_channel[r['渠道']]['sales'] += r['销售额']
    by_channel[r['渠道']]['count'] += 1
for channel, v in sorted(by_channel.items(), key=lambda x: -x[1]['sales']):
    pct = v['sales']/total_sales*100
    print(f'{channel}: 销售额{v["sales"]:,.0f} ({pct:.1f}%), 订单{v["count"]}')

print('\n=== 月度趋势 ===')
by_month = defaultdict(float)
for r in data:
    by_month[r['月份']] += r['销售额']
for month in sorted(by_month.keys()):
    print(f'{month}: {by_month[month]:,.0f}')
