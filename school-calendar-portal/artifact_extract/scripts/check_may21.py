import json, bisect
from datetime import date, timedelta

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

print('=== School Year 2025-2026 ===')
for sy in cal['schoolYears']:
    if sy['year'] == '2025-2026':
        print(f'School: {sy["start"]} to {sy["end"]}')
        print(f'Summer break: {sy["breaks"]["summer"]["start"]} to {sy["breaks"]["summer"]["end"]}')

print()
print('=== May 2026 dates around school end ===')
starts = [date.fromisoformat(iv['start']) for iv in ivs]
for d in [date(2026,5,18), date(2026,5,19), date(2026,5,20), date(2026,5,21), date(2026,5,22), date(2026,5,23), date(2026,5,24)]:
    idx = bisect.bisect_right(starts, d) - 1
    if idx >= 0:
        iv = ivs[idx]
        s, e = date.fromisoformat(iv['start']), date.fromisoformat(iv['end'])
        if s <= d <= e:
            dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]
            print(f'{d} ({dow}): {iv["custodian"]} / {iv["reason"]}')
        else:
            print(f'{d}: gap')
    else:
        print(f'{d}: NO INTERVAL')

print()
print('=== Analysis ===')
may21 = date(2026, 5, 21)
print(f'May 21 2026 is a {["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][may21.weekday()]}')
print(f'School year ends: 2026-05-21 (Thu)')
print(f'Summer starts: 2026-05-22 (in calendar data)')
print()
print('Question: Is May 21 (last day of school) regular school day or summer?')
print()
print('Logic A: Last school day is still school year -> regular_school_day')
print('  - School year end is May 21, so May 21 is the LAST school day')
print('  - Mom gets regular school days in odd year (2025-2026)')
print('  - Current output: dad / espo_thursday')
print()
print('Logic B: Last school day = summer custody starts')
print('  - Summer starts day after school ends = May 22')
print('  - May 21 is still school year, but LAST day')
print('  - Christmas uses "last day before break" logic')
print('  - Should May 21 also use this?')
print()
print('=== Current ESPO pattern for Thursdays ===')
print('Week 1 Fri: Dec 5 -> Dec 4 Thu = dad')
print('Week 2 Fri: Dec 12 -> Dec 11 Thu = dad')
print('Week 3 Fri: Dec 19 -> (Christmas) skip')
print('Week 4 Fri: Dec 26 -> (Christmas) skip')
print('Week 5 Fri: Jan 2 2026 -> Jan 1 Thu = ?')
print()
print('May 21 is Thursday. In odd year (2025-2026), who gets Thursday?')
print('Currently: dad gets Thursday')
print()
print('The issue: May 21 is the LAST school day.')
print('Under Christmas logic, the last day before break IS part of the break.')
print('Under our summer logic, summer starts the day AFTER school ends.')
print('So May 21 = last school day, summer starts May 22.')
print('But is May 21 still subject to ESPO Thursday rules?')
print()
print('Current local file shows: May 21 = dad / espo_thursday')
print('This suggests May 21 is treated as regular ESPO Thursday, NOT summer.')