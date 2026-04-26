import json
import calendar as calmod
from datetime import date, timedelta

# Load data
cal_data = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))
ivs = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'))['intervals']

def find(d):
    for iv in ivs:
        if iv['start'] <= d.isoformat() <= iv['end']:
            return iv['custodian'], iv['reason']
    return None, None

def _is_noschool_day(d):
    for sy in cal_data['schoolYears']:
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

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/trace_apr10.txt', 'w', encoding='utf-8')

d = date(2026, 4, 10)
out.write(f"=== Tracing {d} ({d.strftime('%A')}) ===\n")

# Check all steps
out.write(f"\nStep 4 (Extended Weekend Rule - 1st/3rd/5th Fridays):\n")
fridays = sorted([
    date(2026, 4, day[0])
    for day in calmod.Calendar().itermonthdays2(2026, 4)
    if day[0] != 0 and day[1] == 4
])
out.write(f"  All April Fridays: {fridays}\n")
if d in fridays:
    fri_rank = fridays.index(d) + 1
    out.write(f"  {d} is {fri_rank}th Friday\n")
    out.write(f"  Is qualifying (1/3/5)? {fri_rank in [1,3,5]}\n")
    if fri_rank in [1, 3, 5]:
        out.write(f"  -> Would return dad/weekend\n")

out.write(f"\nStep 4b (Non-qual Friday no-school):\n")
thu = d - timedelta(days=1)
fri_is_ns = _is_noschool_day(d)
thu_was_school = thu.weekday() == 3 and not _is_noschool_day(thu)
out.write(f"  thu = {thu} ({thu.strftime('%A')})\n")
out.write(f"  fri_is_noschool = {fri_is_ns}\n")
out.write(f"  thu_was_school = {thu_was_school}\n")
out.write(f"  Condition (fri_is_ns AND thu_was_school) = {fri_is_ns and thu_was_school}\n")

out.write(f"\nStep 4c (Sat/Sun after no-school Fri):\n")
for delta in [5, 6]:
    dd = date(2026, 4, 10) + timedelta(days=delta-4)
    out.write(f"  {dd} ({dd.strftime('%A')}): is_noschool(Fri) = {_is_noschool_day(d)}\n")

out.write(f"\nStep 4d (Monday no-school):\n")
out.write(f"  Not applicable (d is Friday)\n")

out.write(f"\nStep 5 (Regular school day rules):\n")
out.write(f"  d.weekday() = {d.weekday()} (3=Thu, 4=Fri)\n")
if d.weekday() == 4:
    fridays_list = sorted([
        date(2026, 4, day[0])
        for day in calmod.Calendar().itermonthdays2(2026, 4)
        if day[0] != 0 and day[1] == 4
    ])
    fri_rank2 = fridays_list.index(d) + 1
    out.write(f"  Friday rank = {fri_rank2}\n")
    out.write(f"  Qualifying (1/3/5)? {fri_rank2 in [1,3,5]}\n")
    if fri_rank2 in [1, 3, 5]:
        out.write(f"  -> Would return dad/weekend\n")

out.write(f"\nACTUAL RESULT from intervals: {find(d)}\n")

out.write(f"\n=== Context: April 6-13, 2026 ===\n")
for day in range(6, 14):
    dd = date(2026, 4, day)
    c, r = find(dd)
    is_ns = _is_noschool_day(dd)
    out.write(f"  {dd} ({dd.strftime('%a')}): noschool={is_ns} -> {c}/{r}\n")

out.close()
print("Done")