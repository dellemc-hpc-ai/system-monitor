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

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/debug_01_10.txt', 'w', encoding='utf-8')

# Check Jan 10 in detail
d = date(2025, 1, 10)
out.write(f"=== Checking {d} ===\n")
out.write(f"  weekday = {d.weekday()} (4=Friday)\n")
out.write(f"  Is Friday? {d.weekday() == 4}\n")

# Step 4b
thu = d - timedelta(days=1)
out.write(f"\n  Step 4b:\n")
out.write(f"  thu = {thu}, thu.weekday = {thu.weekday()}\n")
out.write(f"  _is_noschool_day(thu) = {_is_noschool_day(thu)}\n")
thu_was_school = thu.weekday() == 3 and not _is_noschool_day(thu)
out.write(f"  thu_was_school = {thu_was_school}\n")
out.write(f"  (condition: thu.weekday==3 AND not noschool) -> {thu.weekday()==3} and {not _is_noschool_day(thu)}\n")

# Step 4c
out.write(f"\n  Step 4c:\n")
for delta in [5, 6]:
    dd = d + timedelta(days=delta-4)
    out.write(f"  d={dd}, weekday={dd.weekday()}, Fri={dd-timedelta(days=dd.weekday()-4)}\n")

# Check intervals directly
out.write(f"\n  Intervals containing {d}:\n")
for iv in ivs:
    if iv['start'] <= d.isoformat() <= iv['end']:
        out.write(f"    {iv['start']} to {iv['end']}: {iv['custodian']}/{iv['reason']}\n")

# Also check nearby
out.write(f"\n  Nearby Fridays:\n")
for day in range(7, 14):
    dd = date(2025, 1, day)
    c, r = find(dd)
    is_ns = _is_noschool_day(dd)
    out.write(f"  {dd}: {dd.strftime('%a')} is_noschool={is_ns} -> {c}/{r}\n")

out.close()
print("Done")