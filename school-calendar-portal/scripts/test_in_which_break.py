import sys, os, json
from datetime import date, timedelta

BASE = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal'
sys.path.insert(0, os.path.join(BASE, 'src'))
os.chdir(BASE)

import custody_calculator as cc

cal = cc.load_standard_calendar(os.path.join(BASE, 'data', 'processed', 'rrisd_standard_calendar.json'))
calc = cc.CustodyCalculator({}, cal)

results = []
for day in [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]:
    d = date(2026, 3, day)
    result = calc._in_which_break(d)
    br_data = result[1]
    br_end = br_data['end'] if br_data else 'N/A'
    results.append(f'3/{day}: break={result[0]}, br_end={br_end}')

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/test_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))