import json
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

print('=== May 18-24 2026 (direct lookup) ===')
for d in [date(2026,5,18+i) for i in range(7)]:
    for iv in ivs:
        s = date.fromisoformat(iv['start'])
        e = date.fromisoformat(iv['end'])
        if s <= d <= e:
            dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]
            print(f'{d} ({dow}): {iv["custodian"]} / {iv["reason"]} (interval: {iv["start"]}-{iv["end"]})')
            break

print()
print('=== Summer intervals containing May 21-22 ===')
for iv in ivs:
    if 'summer' in iv['reason']:
        s = date.fromisoformat(iv['start'])
        e = date.fromisoformat(iv['end'])
        if s <= date(2026,5,22) <= e:
            print(f'  {iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')

print()
print('=== All intervals for May 21 ===')
for iv in ivs:
    s = date.fromisoformat(iv['start'])
    e = date.fromisoformat(iv['end'])
    if s <= date(2026,5,21) <= e:
        print(f'  {iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')