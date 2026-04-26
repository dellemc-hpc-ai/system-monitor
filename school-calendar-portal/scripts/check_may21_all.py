import json
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

print('=== All intervals for May 21 2026 ===')
for iv in ivs:
    s = date.fromisoformat(iv['start'])
    e = date.fromisoformat(iv['end'])
    if s <= date(2026,5,21) <= e:
        print(f'  {iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')

print()
print('=== All intervals overlapping May 21 ===')
for iv in ivs:
    s = date.fromisoformat(iv['start'])
    e = date.fromisoformat(iv['end'])
    # Check overlap
    if s <= date(2026,5,21) <= e or (s <= e and e >= date(2026,5,21) >= s):
        print(f'  {iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')

print()
print('=== Full list around May 21 ===')
for iv in ivs:
    s = date.fromisoformat(iv['start'])
    e = date.fromisoformat(iv['end'])
    if s >= date(2026,5,18) and s <= date(2026,5,25):
        print(f'  {iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')