import json, bisect
from datetime import date, timedelta

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

# Find all intervals around Dec 18
print('=== All intervals around Dec 15-21 ===')
for iv in ivs:
    s = date.fromisoformat(iv['start'])
    e = date.fromisoformat(iv['end'])
    if s <= date(2025,12,21) and e >= date(2025,12,15):
        print(f'{iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')

print()
print('=== Which interval contains Dec 18? ===')
target = date(2025, 12, 18)
starts = [date.fromisoformat(iv['start']) for iv in ivs]
idx = bisect.bisect_right(starts, target) - 1
if idx >= 0:
    iv = ivs[idx]
    s, e = date.fromisoformat(iv['start']), date.fromisoformat(iv['end'])
    if s <= target <= e:
        print(f'Interval: {iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')
        # Show surrounding dates
        print(f'\nNeighboring dates:')
        for d_offset in range(-3, 4):
            d = target + timedelta(days=d_offset)
            if s <= d <= e:
                dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]
                print(f'  {d} ({dow}): in interval -> {iv["custodian"]} / {iv["reason"]}')
    else:
        print(f'No interval contains Dec 18 (gap)')

print()
print('=== Check: what was the Thursday before Dec 19 Friday? ===')
print('Dec 19 2025 is the 5th Friday of December')
print('Is Dec 19 in special_dates (Christmas break)?')
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)
for sy in cal['schoolYears']:
    if sy['year'] == '2025-2026':
        xmas = sy['breaks']['christmas']
        print(f'Christmas break: {xmas["start"]} to {xmas["end"]}')
        xmas_start = date.fromisoformat(xmas['start'])
        xmas_end = date.fromisoformat(xmas['end'])
        print(f'Dec 18 in Christmas break? {xmas_start <= date(2025,12,18) <= xmas_end}')
        print(f'Dec 19 in Christmas break? {xmas_start <= date(2025,12,19) <= xmas_end}')