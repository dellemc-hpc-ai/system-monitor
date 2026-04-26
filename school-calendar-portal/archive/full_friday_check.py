import json
from datetime import date, timedelta
import calendar as calmod

ivs = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'))['intervals']
cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

def find(d):
    for iv in ivs:
        if iv['start'] <= d.isoformat() <= iv['end']:
            return iv['custodian'], iv['reason']
    return None, None

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

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/full_friday_check.txt', 'w', encoding='utf-8')

out.write("=== Every Friday in 2025-2027 with custodian ===\n")
for year in [2025, 2026, 2027]:
    for month in range(1, 13):
        fridays = all_fridays(year, month)
        for fri in fridays:
            is_ns = _is_noschool_day(fri)
            fri_rank = all_fridays(fri.year, fri.month).index(fri) + 1
            c, r = find(fri)
            label = "NOSCHOOL" if is_ns else "school day"
            qual = "qual" if fri_rank in [1,3,5] else f"{fri_rank}th"
            out.write(f"{fri}: {qual} {label} -> {c}/{r}\n")

out.close()
print("Done")