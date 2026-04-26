import json, bisect
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

print('=== All intervals with christmas ===')
for iv in ivs:
    if 'christmas' in iv['reason']:
        print(f'{iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')

print()
print('=== Direct query for specific dates ===')
target_dates = [
    date(2025,12,18), date(2025,12,19), date(2025,12,20), date(2025,12,21),
    date(2025,12,28), date(2025,12,29),
    date(2026,12,17), date(2026,12,18), date(2026,12,19),
]
starts = [date.fromisoformat(iv['start']) for iv in ivs]
for target in target_dates:
    idx = bisect.bisect_right(starts, target) - 1
    if idx >= 0:
        iv = ivs[idx]
        s = date.fromisoformat(iv['start'])
        e = date.fromisoformat(iv['end'])
        in_interval = s <= target <= e
        print(f'{target}: idx={idx}, interval={iv["start"]}-{iv["end"]}, in_interval={in_interval}')