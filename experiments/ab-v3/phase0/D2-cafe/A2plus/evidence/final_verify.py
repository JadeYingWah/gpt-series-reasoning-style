import json, csv

with open(r'<实验根目录>\ab-v3\phase0\D2-cafe\A2plus\evidence\primary_results.json') as f:
    r = json.load(f)

print('=== Final verification ===')
print('Q1 repaired/valid:', r['repaired_rows'], '/', r['valid_rows'])
print('Q2 total revenue:', r['total_revenue'])
print('Q4 missing TS/Qty/Item:', r['missing_ts'], '/', r['missing_qty'], '/', r['missing_item'])
print('Q5 inconsistent:', r['inconsistent_amount'])
print()

with open(r'<实验根目录>\ab-v3\phase0\D2-cafe\A2plus\cleaned_sales.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
print('Cleaned CSV rows:', len(rows))
valid = sum(1 for x in rows if x['ts_valid'] == 'True')
repaired = sum(1 for x in rows if x['ts_repaired'] == 'True')
print('  ts_valid=True:', valid)
print('  ts_repaired=True:', repaired)

total = sum(float(x['Total Spent']) for x in rows if x['Total Spent'] != 'MISSING')
print('  Sum of TS in cleaned CSV:', total)
print('  Match report:', abs(total - r['total_revenue']) < 0.01)

with open(r'<实验根目录>\ab-v3\phase0\D2-cafe\A2plus\evidence\cross_validation_report.json') as f:
    cv = json.load(f)
s = cv['cross_validation_summary']
print()
print('Cross-val:', s['num_agree'], '/', s['num_metrics_compared'], 'agree, all_agree=', s['all_core_metrics_agree'])
