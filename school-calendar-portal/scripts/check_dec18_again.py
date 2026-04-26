import json, bisect
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

print('=== Dec 18 2025 current status ===')
target = date(2025, 12, 18)
dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][target.weekday()]
print(f'Dec 18 2025 is a {dow}')

starts = [date.fromisoformat(iv['start']) for iv in ivs]
idx = bisect.bisect_right(starts, target) - 1
if idx >= 0:
    iv = ivs[idx]
    s, e = date.fromisoformat(iv['start']), date.fromisoformat(iv['end'])
    if s <= target <= e:
        print(f'Current: {iv["custodian"]} / {iv["reason"]} (interval: {iv["start"]}-{iv["end"]})')
    else:
        print(f'Gap - interval: {iv["start"]}-{iv["end"]}')

print()
print('=== If Christmas break starts Dec 18 (instead of Dec 19) ===')
print('2025 is odd year -> first half goes to mom')
print('First half: Dec 18 to Dec 28 -> mom')
print('So Dec 18 would be mom / christmas_first_half')
print()
print('But current shows: dad / espo_thursday')
print()

print('=== Dec 18 as regular school day (odd year) ===')
print('Odd year: Mom gets regular school days Mon-Fri')
print('Dec 18 (Thu) -> mom regular_school_day')
print()
print('But current shows: dad espo_thursday')
print()

print('=== Dec 18 as noschool day (odd year) ===')
print('Odd year: Dad gets noschool days')
print('Dec 18 -> dad noschool_day')
print()

print('=== Key question: Is Dec 18 a noschool day in RRISD calendar? ===')
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)
for sy in cal['schoolYears']:
    if sy['year'] == '2025-2026':
        print(f'Christmas break: {sy["breaks"]["christmas"]["start"]} to {sy["breaks"]["christmas"]["end"]}')
        print('Noschool days in Dec 2025:')
        for nd in sy.get('noschool_days', []):
            nd_date = date.fromisoformat(nd['date'])
            if nd_date.month == 12 and nd_date.year == 2025:
                print(f'  {nd["date"]}: {nd["label"]}')

print()
print('=== Conclusion ===')
print('Christmas break starts Dec 19, so Dec 18 is NOT in Christmas break')
print('Dec 18 is a Thursday, regular school day')
print('Odd year (2025): mom gets regular school days -> Dec 18 should be mom / regular_school_day')
print()
print('Current shows: dad / espo_thursday')
print('This suggests Dec 18 might be a noschool day not in the calendar data,')
print('OR there is a bug in how Dec 18 is classified.')