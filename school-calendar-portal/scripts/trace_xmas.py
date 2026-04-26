import json
from datetime import date, timedelta

# Trace through what the code does
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

for sy in cal['schoolYears']:
    if sy['year'] == '2025-2026':
        print('=== 2025-2026 ===')
        school_start = date.fromisoformat(sy['start'])
        school_end = date.fromisoformat(sy['end'])
        br = sy['breaks'].get('christmas', {})
        district_christmas_start = date.fromisoformat(br['start'])
        district_christmas_end = date.fromisoformat(br['end'])
        print(f'chool_start: {school_start}')
        print(f'school_end: {school_end}')
        print(f'district_christmas_start: {district_christmas_start}')
        print(f'district_christmas_end: {district_christmas_end}')

        # Walk backward from district_christmas_start - 1
        d = district_christmas_start - timedelta(days=1)
        print(f'Start walking backward from {d}')
        last_school_day = None
        while d >= school_start:
            print(f'  Checking {d} (weekday={d.weekday()}, in_range={d <= school_end})')
            if d.weekday() < 5 and d <= school_end:
                last_school_day = d
                print(f'  -> FOUND: {d}')
                break
            d -= timedelta(days=1)

        if last_school_day:
            print(f'Custody Christmas start: {last_school_day}')
            start_d = last_school_day
            end_d = district_christmas_end
            split_date = date(start_d.year, 12, 28)
            print(f'split_date: {split_date}')
            print(f'first half: {start_d} to {split_date}')
            print(f'second half: {split_date + timedelta(days=1)} to {end_d}')