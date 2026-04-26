import json
from datetime import date, timedelta

# Read the ACTUAL data used by the code
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

# Get Christmas intervals
print('=== Christmas intervals in espo_intervals.json ===')
for iv in ivs:
    if 'christmas' in iv['reason']:
        print(f'  {iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')

# Also check what the normalizer saved
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

print('\n=== Christmas in rrisd_standard_calendar.json ===')
for sy in cal['schoolYears']:
    xmas = sy['breaks'].get('christmas', {})
    print(f'{sy["year"]}: {xmas.get("start", "N/A")} to {xmas.get("end", "N/A")}')

# Now manually walk backward like the code does
print('\n=== Manual backward walk for 2025-2026 ===')
sy = cal['schoolYears'][0]
school_start = date.fromisoformat(sy['start'])
school_end = date.fromisoformat(sy['end'])
district_start = date.fromisoformat(sy['breaks']['christmas']['start'])
print(f'school_start: {school_start}')
print(f'school_end: {school_end}')
print(f'district_christmas_start: {district_start}')

d = district_start
while d >= school_start:
    wd = d.weekday()
    in_range = d <= school_end
    is_weekday = wd < 5
    print(f'  Checking {d} (weekday={wd}, in_range={in_range}, is_weekday={is_weekday})')
    if is_weekday and in_range:
        print(f'  -> FOUND: {d}')
        break
    d -= timedelta(days=1)

print()
print('=== Manual backward walk for 2026-2027 ===')
sy2 = cal['schoolYears'][1]
school_start2 = date.fromisoformat(sy2['start'])
school_end2 = date.fromisoformat(sy2['end'])
district_start2 = date.fromisoformat(sy2['breaks']['christmas']['start'])
print(f'school_start: {school_start2}')
print(f'school_end: {school_end2}')
print(f'district_christmas_start: {district_start2}')

d2 = district_start2
while d2 >= school_start2:
    wd2 = d2.weekday()
    in_range2 = d2 <= school_end2
    is_weekday2 = wd2 < 5
    print(f'  Checking {d2} (weekday={wd2}, in_range={in_range2}, is_weekday={is_weekday2})')
    if is_weekday2 and in_range2:
        print(f'  -> FOUND: {d2}')
        break
    d2 -= timedelta(days=1)