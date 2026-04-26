import sys
proj = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal'
sys.path.insert(0, proj)

from src.statute_loader import load_statute
from src.rule_builder import build_custody_rules
from src.custody_calculator import CustodyCalculator, load_standard_calendar
from datetime import date, timedelta

statute = load_statute('TX', proj + '/data/processed')
cal = load_standard_calendar(proj + '/data/processed/rrisd_standard_calendar.json')

rules = build_custody_rules(statute=statute, distance_miles=0.0, mode='espo',
    dad_lat=30.4425, dad_lon=-97.8134, mom_lat=30.4425, mom_lon=-97.8134)

calc = CustodyCalculator(rules, cal)

d = date(2026, 4, 10)

# Print all the intermediate values used in _get_custodian
import calendar as calmod

print(f"=== _get_custodian trace for {d} ===")
print(f"d.weekday() = {d.weekday()} (4=Friday)")

# Step 4 check
fridays = sorted([date(d.year, d.month, day[0]) for day in calmod.Calendar().itermonthdays2(d.year, d.month) if day[0] != 0 and day[1] == 4])
print(f"All Fridays in {d.year}-{d.month}: {fridays}")
print(f"{d} in fridays: {d in fridays}")
if d in fridays:
    fri_rank = fridays.index(d) + 1
    print(f"Friday rank: {fri_rank}, in [1,3,5]: {fri_rank in [1,3,5]}")

# Step 4b check
print(f"\nStep 4b:")
thu = d - timedelta(days=1)
print(f"thu = {thu}, thu.weekday() = {thu.weekday()}")
print(f"thu.weekday() == 3: {thu.weekday() == 3}")
print(f"_is_noschool_day({thu}): {calc._is_noschool_day(thu)}")
print(f"_is_noschool_day({d}): {calc._is_noschool_day(d)}")
thu_was_school = thu.weekday() == 3 and not calc._is_noschool_day(thu)
print(f"thu_was_school = {thu_was_school}")
print(f"Condition (noschool AND was_school): {calc._is_noschool_day(d) and thu_was_school}")

# Now call the actual function
result = calc._get_custodian(d)
print(f"\n_get_custodian({d}) = {result}")
print(f"Expected: mom/default_custody")

# Check if we're getting the correct result from the calculator
# by looking at what the intervals say
intervals = calc.compute_intervals()
for iv in intervals:
    if iv.start <= d <= iv.end:
        print(f"Interval for {d}: {iv.custodian}/{iv.reason}")
        break