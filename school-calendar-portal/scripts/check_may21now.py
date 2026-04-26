import json, bisect
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

starts = [date.fromisoformat(iv['start']) for iv in ivs]
print('=== May 2026 around school end ===')
for d in [date(2026,5,18), date(2026,5,19), date(2026,5,20), date(2026,5,21), date(2026,5,22), date(2026,5,23)]:
    idx = bisect.bisect_right(starts, d) - 1
    if idx >= 0:
        iv = ivs[idx]
        s, e = date.fromisoformat(iv['start']), date.fromisoformat(iv['end'])
        if s <= d <= e:
            dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]
            print(f'{d} ({dow}): {iv["custodian"]} / {iv["reason"]}')
        else:
            print(f'{d}: gap (interval: {iv["start"]}-{iv["end"]})')

print()
print('=== Summer intervals ===')
for iv in ivs:
    if 'summer' in iv['reason']:
        print(f'{iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')