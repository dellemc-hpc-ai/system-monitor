import sys
sys.path.insert(0, 'C:\\Users\\frank\\.openclaw\\workspace\\projects\\TASK-001-allergy-report\\school-calendar-portal')
import json
from datetime import date, timedelta

from src.custody_calculator import CustodyCalculator, load_standard_calendar

BASE = 'C:\\Users\\frank\\.openclaw\\workspace\\projects\\TASK-001-allergy-report\\school-calendar-portal'
rules = json.load(open(BASE + '\\config\\texas_espo_spo_rules.json'))['rules']
cal = load_standard_calendar(BASE + '\\data\\processed\\rrisd_standard_calendar.json')
calc = CustodyCalculator(rules['espo'], cal)

print("=== Aug 2025 Fridays ===")
test_dates = [date(2025,8,1), date(2025,8,8), date(2025,8,15), date(2025,8,22), date(2025,8,29)]
for d in test_dates:
    cust, reason = calc._get_custodian(d)
    day_name = d.strftime("%a")
    print(f"{d} ({day_name}): {cust} / {reason}")

print()
print("=== April 2026 Friday weekends ===")
for d in [date(2026,4,3), date(2026,4,10), date(2026,4,17), date(2026,4,24)]:
    cust, reason = calc._get_custodian(d)
    day_name = d.strftime("%a")
    print(f"{d} ({day_name}): {cust} / {reason}")

print()
print("=== Verify full weekends in April 2026 ===")
for fri in [date(2026,4,3), date(2026,4,10), date(2026,4,17), date(2026,4,24)]:
    sat = fri + timedelta(days=1)
    sun = fri + timedelta(days=2)
    for d in [fri, sat, sun]:
        cust, reason = calc._get_custodian(d)
        day_name = d.strftime("%a")
        print(f"  {d} ({day_name}): {cust} / {reason}")
    print()