import json
from datetime import date, timedelta
import calendar as calmod

cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

def _is_noschool_day(d):
    """Current (buggy) version - only checks noschool_days list, not breaks"""
    for sy in cal['schoolYears']:
        sy_start = date.fromisoformat(sy['year'][:4] + '-08-01')
        sy_end = date.fromisoformat(sy['year'][5:] + '-07-31')
        if not (sy_start <= d <= sy_end):
            continue
        noschool = {date.fromisoformat(n['date']) for n in sy.get('noschool_days', [])}
        if d in noschool:
            return True
    return False

def _in_which_break(d):
    """Check if d is inside a school break"""
    for sy in cal['schoolYears']:
        sy_start = date.fromisoformat(sy['year'][:4] + '-08-01')
        sy_end = date.fromisoformat(sy['year'][5:] + '-07-31')
        if not (sy_start <= d <= sy_end):
            continue
        for br_name, br in sy.get('breaks', {}).items():
            br_start = date.fromisoformat(br['start'])
            br_end = date.fromisoformat(br['end'])
            if br_start <= d <= br_end:
                return br_name, br
    return None, None

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/debug_noschool_vs_break.txt', 'w', encoding='utf-8')

# Check: are these Fridays inside breaks?
fris_to_check = [
    date(2025, 11, 28),  # Thanksgiving break
    date(2025, 12, 26),  # Christmas break
    date(2026, 1, 2),    # Christmas break
    date(2026, 3, 20),   # Spring break
    date(2026, 3, 27),   # After spring break
    date(2027, 3, 19),   # Spring break
    date(2027, 3, 26),   # Good Friday (no-school but NOT in spring break)
]
for d in fris_to_check:
    in_break, break_data = _in_which_break(d)
    is_ns = _is_noschool_day(d)
    out.write(f"{d} ({d.strftime('%a')}): _is_noschool_day={is_ns}, in_break={in_break}\n")

out.write("\n=== Christmas break dates ===\n")
for sy in cal['schoolYears']:
    xmas = sy.get('breaks', {}).get('christmas', {})
    if xmas:
        out.write(f"{sy['year']} Christmas: {xmas['start']} to {xmas['end']}\n")

out.write("\n=== Thanksgiving break ===\n")
for sy in cal['schoolYears']:
    tg = sy.get('breaks', {}).get('thanksgiving', {})
    if tg:
        out.write(f"{sy['year']} Thanksgiving: {tg['start']} to {tg['end']}\n")

out.close()
print("Done")