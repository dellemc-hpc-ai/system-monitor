import json

import os
BASE = os.path.dirname(os.path.dirname(__file__))
PATH = os.path.join(BASE, 'data', 'processed', 'rrisd_standard_calendar.json')
with open(PATH, 'r', encoding='utf-8') as f:
    cal = json.load(f)

for sy in cal['schoolYears']:
    before = len(sy['noschool_days'])
    # PDF says Oct 9 and Oct 12 are normal school days (exam week), NOT noschool
    sy['noschool_days'] = [
        n for n in sy['noschool_days']
        if n['date'] not in ('2026-10-09', '2026-10-12')
    ]
    removed = before - len(sy['noschool_days'])
    print(f"SY {sy['year']}: removed {removed} noschool days")

with open(PATH, 'w', encoding='utf-8') as f:
    json.dump(cal, f, indent=2, ensure_ascii=False)

print('Saved rrisd_standard_calendar.json')
