import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from src.custody_calculator import CustodyCalculator
from datetime import date

rules_path = 'data/rules.json'
cal_path = 'data/processed/rrisd_standard_calendar.json'
rules = json.load(open(rules_path))
cal = json.load(open(cal_path))

calc = CustodyCalculator(rules, [cal['school_years'][0], cal['school_years'][1]])

print("=== April 2026 daily custodian ===")
for day in range(1, 31):
    d = date(2026, 4, day)
    cust, reason = calc._get_custodian(d)
    dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]
    mark = ' ⬅ EXTENDED' if reason == 'weekend' and d.weekday() == 6 else ''
    print(f"  Apr {day:2d} ({dow}): {cust} | {reason}{mark}")

print()
print("=== Extended weekend check for Thu Apr 2 ===")
calc._check_extended_weekend_applies(date(2026, 4, 2))

print()
print("=== Check if May 21 2026 is summer day1 ===")
d = date(2026, 5, 21)
cust, reason = calc._get_custodian(d)
print(f"  May 21: {cust} | {reason}")

print()
print("=== June 2026 ===")
for day in [19, 20, 21, 22, 23]:
    d = date(2026, 6, day)
    cust, reason = calc._get_custodian(d)
    dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]
    print(f"  Jun {day:2d} ({dow}): {cust} | {reason}")