import json
from datetime import date, timedelta

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

# Check Oct 2025
d = date(2025, 10, 1)
print('Oct 2025 calendar:')
while d <= date(2025, 10, 31):
    dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]
    iv_found = None
    for iv in ivs:
        sd = date.fromisoformat(iv['start'])
        ed = date.fromisoformat(iv['end'])
        if sd <= d <= ed:
            iv_found = iv
            break
    if iv_found:
        print(f'{d} ({dow}): {iv_found["custodian"]} / {iv_found["reason"]}')
    else:
        print(f'{d} ({dow}): NO INTERVAL')
    d += timedelta(days=1)