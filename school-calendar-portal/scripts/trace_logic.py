import json
import os
import sys
import calendar as calmod
from datetime import date, timedelta

proj_dir = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal'
sys.path.insert(0, proj_dir)

from src.statute_loader import load_statute
from src.rule_builder import build_custody_rules
from src.custody_calculator import CustodyCalculator, load_standard_calendar

# Load statute and build rules
statute = load_statute("TX", os.path.join(proj_dir, "data", "processed"))
cal = load_standard_calendar(os.path.join(proj_dir, "data", "processed", "rrisd_standard_calendar.json"))

rules = build_custody_rules(
    statute=statute,
    distance_miles=0.0,
    mode="espo",
    dad_lat=30.4425,
    dad_lon=-97.8134,
    mom_lat=30.4425,
    mom_lon=-97.8134,
)

calc = CustodyCalculator(rules, cal)

# Directly test the logic
d = date(2026, 4, 10)
print(f"Testing {d} ({d.strftime('%A')})")
print(f"_get_custodian({d}) = {calc._get_custodian(d)}")
print(f"_is_noschool_day({d}) = {calc._is_noschool_day(d)}")

# Check all steps manually
print("\n--- Manual trace ---")
rules_obj = rules

# Step 4
fridays = sorted([date(2026, 4, day[0]) for day in calmod.Calendar().itermonthdays2(2026, 4) if day[0] != 0 and day[1] == 4])
print(f"Step 4: fridays={fridays}")
print(f"  {d} in fridays: {d in fridays}")
if d in fridays:
    fri_rank = fridays.index(d) + 1
    print(f"  fri_rank={fri_rank}, in [1,3,5]: {fri_rank in [1,3,5]}")
    if fri_rank in [1, 3, 5]:
        print(f"  -> return dad/weekend")

# Step 4b
print(f"\nStep 4b:")
thu = d - timedelta(days=1)
fri_is_ns = calc._is_noschool_day(d)
thu_was_school = thu.weekday() == 3 and not calc._is_noschool_day(thu)
print(f"  thu={thu}, fri_is_noschool={fri_is_ns}, thu_was_school={thu_was_school}")
print(f"  Condition: {fri_is_ns and thu_was_school}")
if fri_is_ns and thu_was_school:
    print(f"  -> return dad/no_school_day")

# Step 4c
print(f"\nStep 4c:")
for wd in [5, 6]:
    dd = d + timedelta(days=wd - 4)
    fri = dd - timedelta(days=dd.weekday() - 4)
    print(f"  For {dd} ({dd.strftime('%A')}): preceding Fri={fri}, is_noschool={calc._is_noschool_day(fri)}")
    if dd.weekday() in (5, 6):
        if calc._is_noschool_day(fri):
            print(f"  -> return dad/no_school_day")

# Step 4d
print(f"\nStep 4d:")
if d.weekday() == 0:
    fri = d - timedelta(days=3)
    fridays2 = sorted([date(fri.year, fri.month, day[0]) for day in calmod.Calendar().itermonthdays2(fri.year, fri.month) if day[0] != 0 and day[1] == 4])
    was_dad_weekend = fri in fridays2 and (fridays2.index(fri) + 1) in [1, 3, 5]
    was_noschool_fri = calc._is_noschool_day(fri)
    print(f"  fri={fri}, was_dad_weekend={was_dad_weekend}, was_noschool_fri={was_noschool_fri}")

# Step 5
print(f"\nStep 5:")
print(f"  weekday={d.weekday()}")
if d.weekday() == 4:
    print(f"  Friday rank={fridays.index(d)+1}, in [1,3,5]: {fridays.index(d)+1 in [1,3,5]}")
    if fridays.index(d) + 1 in [1, 3, 5]:
        print(f"  -> return dad/weekend")
    else:
        print(f"  -> Fall through to default")

# Default
print(f"\nDefault: mom/default_custody")