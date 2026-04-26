import json
from datetime import date, timedelta

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

print('=== All intervals starting in Dec 2025 ===')
for iv in ivs:
    if iv['start'].startswith('2025-12'):
        print(f'{iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')

print()
print('=== Check: what is Dec 18 2025? ===')
# Check if Dec 18 is in any noschool list
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

for sy in cal['schoolYears']:
    print(f'\n{sy["year"]} noschool_days in Dec:')
    for nd in sy.get('noschool_days', []):
        nd_date = date.fromisoformat(nd['date'])
        if nd_date.month == 12 and nd_date.year == 2025:
            print(f'  {nd["date"]}: {nd["label"]}')

    # Check Christmas break
    xmas = sy['breaks'].get('christmas', {})
    print(f'  Christmas: {xmas.get("start", "N/A")} to {xmas.get("end", "N/A")}')

    # Manually walk backward
    school_start = date.fromisoformat(sy['start'])
    school_end = date.fromisoformat(sy['end'])
    district_start = date.fromisoformat(xmas['start'])
    print(f'  District Christmas start: {district_start} ({["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][district_start.weekday()]})')

    d = district_start
    last_school_day = None
    while d >= school_start:
        if d <= school_end and d.weekday() < 5:
            last_school_day = d
            break
        d -= timedelta(days=1)

    print(f'  Last school day before Christmas: {last_school_day} ({["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][last_school_day.weekday()] if last_school_day else "N/A"})')
    print(f'  Expected: Dec 18 (Thu)')