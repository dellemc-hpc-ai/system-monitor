import json, bisect
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

starts = [date.fromisoformat(iv['start']) for iv in ivs]
for target in [date(2025,11,29), date(2025,11,30), date(2026,5,21)]:
    idx = bisect.bisect_right(starts, target) - 1
    if idx >= 0:
        iv = ivs[idx]
        s, e = date.fromisoformat(iv['start']), date.fromisoformat(iv['end'])
        if s <= target <= e:
            print(f'{target}: {iv["custodian"]} / {iv["reason"]}')
        else:
            print(f'{target}: gap (interval: {iv["start"]}-{iv["end"]})')
    else:
        print(f'{target}: NO INTERVAL')