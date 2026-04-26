import json, bisect
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

print('=== May 2026 around school end ===')
for d in [date(2026,5,18), date(2026,5,19), date(2026,5,20), date(2026,5,21), date(2026,5,22), date(2026,5,23)]:
    dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]
    starts = [date.fromisoformat(iv['start']) for iv in ivs]
    idx = bisect.bisect_right(starts, d) - 1
    if idx >= 0:
        iv = ivs[idx]
        s, e = date.fromisoformat(iv['start']), date.fromisoformat(iv['end'])
        if s <= d <= e:
            print(f'{d} ({dow}): {iv["custodian"]} / {iv["reason"]}')
        else:
            print(f'{d} ({dow}): NO MATCH (interval: {iv["start"]}-{iv["end"]})')
    else:
        print(f'{d} ({dow}): NO INTERVAL')

print('\n=== Summer intervals ===')
for iv in ivs:
    if 'summer' in iv['reason']:
        print(iv['start'], '-', iv['end'], iv['custodian'], '/', iv['reason'])

print('\n=== Calendar school year ends ===')
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)
for sy in cal['schoolYears']:
    print(f'{sy["year"]}: end={sy["end"]}, summer={sy["breaks"]["summer"]["start"]} to {sy["breaks"]["summer"]["end"]}')