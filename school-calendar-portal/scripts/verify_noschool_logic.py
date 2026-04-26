import json
import calendar as calmod
from datetime import date

cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

def _is_noschool_day(d):
    for sy in cal['schoolYears']:
        sy_start = date.fromisoformat(sy['year'][:4] + '-08-01')
        sy_end = date.fromisoformat(sy['year'][5:] + '-07-31')
        if not (sy_start <= d <= sy_end):
            continue
        noschool = {date.fromisoformat(n['date']) for n in sy.get('noschool_days', [])}
        if d in noschool:
            return True
    return False

def all_fridays(year, month):
    c = calmod.Calendar()
    return sorted([
        date(year, month, day[0])
        for day in c.itermonthdays2(year, month)
        if day[0] != 0 and day[1] == 4
    ])

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/verify_noschool.txt', 'w', encoding='utf-8')

# Check ALL Fridays in 2025-2026 and 2026-2027 school years
out.write("=== All Fridays in school year range and their noschool status ===\n")
school_years = [2025, 2026, 2027]
for year in school_years:
    for month in range(1, 13):
        fridays = all_fridays(year, month)
        for fri in fridays:
            is_ns = _is_noschool_day(fri)
            label = " [NOSCHOOL]" if is_ns else ""
            # Also check if it's a qualifying Dad weekend (1st/3rd/5th)
            fri_rank = all_fridays(fri.year, fri.month).index(fri) + 1
            qual = " (qualifying)" if fri_rank in [1,3,5] else f" ({fri_rank}th)"
            out.write(f"{fri}:{qual}{label}\n")

out.close()
print("Done")