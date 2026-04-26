import sys, os
proj = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal'
sys.path.insert(0, proj)

from src.statute_loader import load_statute
from src.rule_builder import build_custody_rules
from src.custody_calculator import CustodyCalculator, load_standard_calendar
from datetime import date, timedelta

statute = load_statute('TX', os.path.join(proj, 'data', 'processed'))
cal = load_standard_calendar(os.path.join(proj, 'data', 'processed', 'rrisd_standard_calendar.json'))

rules = build_custody_rules(statute=statute, distance_miles=0.0, mode='espo',
    dad_lat=30.4425, dad_lon=-97.8134, mom_lat=30.4425, mom_lon=-97.8134)

calc = CustodyCalculator(rules, cal)

# Monkey-patch _get_custodian to trace
original_get = calc._get_custodian
call_count = [0]

def traced_get(d):
    result = original_get(d)
    call_count[0] += 1
    if call_count[0] <= 50 or d == date(2026, 4, 10):
        print(f"_get_custodian({d}) = {result}")
    return result

calc._get_custodian = traced_get

# Run compute_intervals
intervals = calc.compute_intervals()

# Find April 10 result
for iv in intervals:
    if iv.start <= date(2026, 4, 10) <= iv.end:
        print(f"\n=== April 10 interval: {iv.custodian}/{iv.reason} ===")
        break

print(f"Total intervals: {len(intervals)}")