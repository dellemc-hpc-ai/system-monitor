import sys, os
sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal')
from src.statute_loader import load_statute
from src.rule_builder import build_custody_rules
from src.custody_calculator import CustodyCalculator, load_standard_calendar
from datetime import date

statute = load_statute('TX', 'data/TX_TEST')
rules = build_custody_rules(
    statute=statute,
    distance_miles=12.4,
    mode='espo',
    dad_lat=30.4425, dad_lon=-97.8134,
    mom_lat=30.4425, mom_lon=-97.8134,
)
cal = load_standard_calendar('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json')
calc = CustodyCalculator(rules, cal)
intervals = calc.compute_intervals()

checks = [
    # Date, description, expected_custodian, expected_reason
    # Non-break days
    # Aug 13-17, 2025: pre-instruction days (teachers report, students don't attend).
    # Treated as pre-school summer gap. Correct = mom/summer_remainder.
    ("2025-08-13", "pre-school summer (Aug gap)", "mom", "summer_remainder"),
    ("2025-09-06", "Saturday (not in break)", "mom", "default_custody"),
    # 1st/3rd/5th Friday
    ("2025-09-05", "1st Friday Sep", "dad", "weekend"),
    ("2025-10-03", "1st Friday Oct", "dad", "weekend"),
    ("2025-10-17", "3rd Friday Oct", "dad", "weekend"),
    ("2025-10-31", "5th Friday Oct", "dad", "weekend"),
    # Thanksgiving (odd year = Dad)
    ("2025-11-24", "thanksgiving Mon Dad(odd)", "dad", "thanksgiving"),
    ("2025-11-28", "thanksgiving Fri Dad(odd)", "dad", "thanksgiving"),
    # Christmas (odd year = Dad first half)
    ("2025-12-19", "christmas first half odd Dad", "dad", "christmas_first_half"),
    ("2025-12-29", "christmas second half odd Mom", "mom", "christmas_second_half"),
    # Christmas even year = Mom first half
    ("2026-12-18", "christmas first half even Mom", "mom", "christmas_first_half"),
    ("2026-12-29", "christmas second half even Dad", "dad", "christmas_second_half"),
    # Spring break (even year = Dad)
    ("2026-03-16", "spring break Mon Dad(even)", "dad", "spring_break"),
    ("2026-03-20", "spring break Fri Dad(even)", "dad", "spring_break"),
    # Summer Dad days
    ("2026-07-01", "summer day 1 Dad", "dad", "summer_possessory"),
    ("2026-07-15", "summer mid Dad", "dad", "summer_possessory"),
    ("2026-07-30", "summer last Dad day", "dad", "summer_possessory"),
    # Summer remainder
    ("2026-07-31", "summer first remainder Mom", "mom", "summer_remainder"),
    ("2026-08-12", "summer last day Mom", "mom", "summer_remainder"),
    # Fathers Day 2026 (June 21): Falls in summer break (May 22-Aug 17).
    # Per Frank: parents day overrides EVERYTHING. Summer should not apply.
    ("2026-06-19", "Fathers Day Fri in summer override", "dad", "fathers_day"),
    ("2026-06-20", "Fathers Day Sat in summer override", "dad", "fathers_day"),
    ("2026-06-21", "Fathers Day Sun in summer override", "dad", "fathers_day"),
    # Mothers Day 2026 (May 10): NOT in spring break (Mar 16-20).
    # Spring break ended. Correct = moms_day for the weekend.
    ("2026-05-08", "Mothers Day Fri", "mom", "mothers_day"),
    ("2026-05-09", "Mothers Day Sat", "mom", "mothers_day"),
    ("2026-05-10", "Mothers Day Sun", "mom", "mothers_day"),
]

print(f"Total intervals: {len(intervals)}")
all_ok = True
for ds, desc, exp_c, exp_r in checks:
    d = date.fromisoformat(ds)
    found = None
    for iv in intervals:
        if iv.start <= d <= iv.end:
            found = iv
            break
    if found:
        ok = "OK" if found.custodian == exp_c and found.reason == exp_r else "FAIL"
        if ok == "FAIL":
            all_ok = False
        print(f"  {ds}  {desc[:35]:35s}: {found.custodian} ({found.reason}) [{ok}]")
    else:
        print(f"  {ds}  {desc[:35]:35s}: NOT FOUND [FAIL]")
        all_ok = False

print()
print("All OK:", all_ok)
