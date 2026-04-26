import json
from datetime import date
import calendar as calmod

ivs = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'))['intervals']
cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

def find(d):
    for iv in ivs:
        if iv['start'] <= d.isoformat() <= iv['end']:
            return iv['custodian'], iv['reason']
    return None, None

def _is_noschool(d):
    for sy in cal['schoolYears']:
        sy_start = date.fromisoformat(sy['year'][:4] + '-08-01')
        sy_end = date.fromisoformat(sy['year'][5:] + '-07-31')
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

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/verify_apr10_out.txt', 'w', encoding='utf-8')

# Check April 10, 2026
d = date(2026, 4, 10)
c, r = find(d)
is_ns = _is_noschool(d)

# Friday rank
fridays = sorted([
    date(2026, 4, day[0])
    for day in calmod.Calendar().itermonthdays2(2026, 4)
    if day[0] != 0 and day[1] == 4
])
fri_rank = fridays.index(d) + 1 if d in fridays else None

out.write(f"April 10, 2026:\n")
out.write(f"  weekday: {d.strftime('%A')} (Friday = weekday 4)\n")
out.write(f"  Friday rank in April: {fri_rank}\n")
out.write(f"  is_noschool: {is_ns}\n")
out.write(f"  custodian: {c}, reason: {r}\n")

out.write(f"\nAll Fridays in April 2026:\n")
for f in fridays:
    cf, rf = find(f)
    is_nsf = _is_noschool(f)
    rank = fridays.index(f) + 1
    out.write(f"  {f}: rank={rank}, noschool={is_nsf} -> {cf}/{rf}\n")

out.write(f"\nApril 2026 spring break check:\n")
for sy in cal['schoolYears']:
    spring = sy.get('breaks', {}).get('spring', {})
    if spring:
        out.write(f"  {sy['year']} spring break: {spring}\n")

out.close()
print("Done")