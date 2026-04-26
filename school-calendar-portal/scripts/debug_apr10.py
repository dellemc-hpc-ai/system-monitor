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

# Load statute and build rules (same as main.py)
statute = load_statute("TX", os.path.join(proj_dir, "data", "processed"))
cal = load_standard_calendar(os.path.join(proj_dir, "data", "processed", "rrisd_standard_calendar.json"))

# Use a representative distance and dad location
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

out = open(f'{proj_dir}/scripts/debug_apr10.txt', 'w', encoding='utf-8')
d = date(2026, 4, 10)
c, r = calc._get_custodian(d)

out.write(f"=== April 10, 2026 Debug ===\n")
out.write(f"Result: {c}/{r}\n\n")

# Step 4 check
out.write("Step 4 (1st/3rd/5th Fri):\n")
fridays = sorted([date(2026, 4, day[0]) for day in calmod.Calendar().itermonthdays2(2026, 4) if day[0] != 0 and day[1] == 4])
out.write(f"  All April Fridays: {fridays}\n")
out.write(f"  April 10 is {fridays.index(d)+1}th Friday\n")
out.write(f"  Qualifying (1/3/5)? {fridays.index(d)+1 in [1,3,5]}\n\n")

# Step 4b check
out.write("Step 4b (Non-qual Fri no-school):\n")
thu = d - timedelta(days=1)
thu_was_school = thu.weekday() == 3 and not calc._is_noschool_day(thu)
out.write(f"  Thu = {thu} (weekday={thu.weekday()})\n")
out.write(f"  Thu is Thursday? {thu.weekday() == 3}\n")
out.write(f"  Thu is_noschool? {calc._is_noschool_day(thu)}\n")
out.write(f"  Thu was_school = {thu_was_school}\n")
out.write(f"  Fri is_noschool? {calc._is_noschool_day(d)}\n")
out.write(f"  Condition (noschool AND was_school)? {calc._is_noschool_day(d) and thu_was_school}\n\n")

# Step 5 check
out.write("Step 5 (Regular school day):\n")
out.write(f"  April 10 weekday = {d.weekday()} (4=Friday)\n")
out.write(f"  Friday rank = {fridays.index(d)+1}\n")
out.write(f"  Is qualifying (1/3/5)? {fridays.index(d)+1 in [1,3,5]}\n\n")

# Context around April 10
out.write("\nContext: April 7-15:\n")
for day in range(7, 16):
    dd = date(2026, 4, day)
    cc, rr = calc._get_custodian(dd)
    out.write(f"  {dd} ({dd.strftime('%a')}): {cc}/{rr}\n")

out.close()
print("Done. See scripts/debug_apr10.txt")