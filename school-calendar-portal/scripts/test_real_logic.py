import json
from datetime import date, timedelta

cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/test_real_logic.txt', 'w', encoding='utf-8')

# Use the ACTUAL school year start/end from the data
for sy in cal['schoolYears']:
    out.write(f"School year {sy['year']}: start={sy['start']}, end={sy['end']}\n")

def _is_noschool_day(d):
    for sy in cal['schoolYears']:
        sy_start = date.fromisoformat(sy['start'])
        sy_end = date.fromisoformat(sy['end'])
        if not (sy_start <= d <= sy_end):
            continue
        noschool = {date.fromisoformat(n['date']) for n in sy.get('noschool_days', [])}
        if d in noschool:
            return True
        for br_name, br in sy.get('breaks', {}).items():
            br_start = date.fromisoformat(br['start'])
            br_end = date.fromisoformat(br['end'])
            if br_start <= d <= br_end:
                return True
    return False

out.write("\n=== Check April 9, 10, 2026 ===\n")
for d in [date(2026,4,9), date(2026,4,10)]:
    sy_start = date.fromisoformat("2025-08-12")
    sy_end = date.fromisoformat("2026-05-21")
    in_range = sy_start <= d <= sy_end
    is_ns = _is_noschool_day(d)
    out.write(f"{d} ({d.strftime('%A')}): in_school_year={in_range}, is_noschool={is_ns}\n")

out.write("\n=== Check ALL April 2026 dates ===\n")
for day in range(1, 32):
    d = date(2026, 4, day)
    is_ns = _is_noschool_day(d)
    out.write(f"April {day}: is_noschool={is_ns}\n")

out.close()
print("Done")