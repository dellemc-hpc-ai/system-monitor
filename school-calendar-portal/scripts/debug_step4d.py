import json
import calendar
from datetime import date, timedelta

cal_data = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'))
ivs = cal_data['intervals']

def find(d):
    for iv in ivs:
        if iv['start'] <= d.isoformat() <= iv['end']:
            return iv['custodian'], iv['reason']
    return None, None

def is_noschool(d):
    sy_data = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))
    for sy in sy_data['schoolYears']:
        sy_start = date.fromisoformat(sy['year'][:4] + '-08-01')
        sy_end = date.fromisoformat(sy['year'][5:] + '-07-31')
        if not (sy_start <= d <= sy_end):
            continue
        noschool = {date.fromisoformat(n['date']) for n in sy.get('noschool_days', [])}
        if d in noschool:
            return True
    return False

print("Step 4d trace for 2027-03-29 (Mon, Easter Monday):")
d = date(2027, 3, 29)
print(f"  d = {d}, weekday = {d.weekday()} (0=Mon)")
fri = d - timedelta(days=3)
print(f"  fri = {fri}")
fridays = sorted([
    date(fri.year, fri.month, day[0])
    for day in calendar.Calendar().itermonthdays2(fri.year, fri.month)
    if day[0] != 0 and day[1] == 4
])
print(f"  all Fridays in {fri.year}-{fri.month}: {fridays}")
if fri in fridays:
    fri_rank = fridays.index(fri) + 1
    was_dad_weekend = fri_rank in [1, 3, 5]
    print(f"  fri {fri} is {fri_rank}th Friday, was_dad_weekend = {was_dad_weekend}")
else:
    was_dad_weekend = False
    print(f"  fri {fri} NOT in fridays list!")
was_noschool_fri = is_noschool(fri)
print(f"  is_noschool(fri {fri}) = {was_noschool_fri}")
d_noschool = is_noschool(d)
print(f"  is_noschool(d {d}) = {d_noschool}")
print(f"  Condition: (was_dad_weekend={was_dad_weekend} or was_noschool_fri={was_noschool_fri}) and d_noschool={d_noschool}")
print(f"  Result: {(was_dad_weekend or was_noschool_fri) and d_noschool}")

print()
print("Also check 2026-01-19 (MLK Day Monday):")
d = date(2026, 1, 19)
fri = d - timedelta(days=3)
print(f"  fri = {fri}")
print(f"  is_noschool(fri) = {is_noschool(fri)}")
print(f"  is_noschool(d) = {is_noschool(d)}")
print(f"  Result from find(): {find(d)}")