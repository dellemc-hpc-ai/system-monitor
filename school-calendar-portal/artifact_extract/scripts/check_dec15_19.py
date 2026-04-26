import json, bisect
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

starts = [date.fromisoformat(iv['start']) for iv in ivs]
for d in [date(2025,12,15), date(2025,12,16), date(2025,12,17), date(2025,12,18), date(2025,12,19)]:
    idx = bisect.bisect_right(starts, d) - 1
    if idx >= 0:
        iv = ivs[idx]
        s, e = date.fromisoformat(iv['start']), date.fromisoformat(iv['end'])
        if s <= d <= e:
            dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]
            print(f'{d} ({dow}): {iv["custodian"]} / {iv["reason"]}')