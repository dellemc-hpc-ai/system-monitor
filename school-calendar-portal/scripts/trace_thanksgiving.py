import sys, os
BASE = r'C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal'
sys.path.insert(0, os.path.join(BASE, 'src'))
os.chdir(BASE)

from datetime import date, timedelta
from custody_calculator import load_standard_calendar, CustodyCalculator
from statute_loader import load_statute
from rule_builder import build_custody_rules

cal = load_standard_calendar('data/processed/rrisd_standard_calendar.json')
statute = load_statute('TX', 'data/processed')
rules = build_custody_rules(statute, 0.0, 'espo', 30.44, -97.81, 30.44, -97.81)
calc = CustodyCalculator(rules, cal)

# Trace step 2 logic for Thanksgiving
sy = cal['schoolYears'][1]
br = sy['breaks']['thanksgiving']
br_start = date.fromisoformat(br['start'])
print(f"District Thanksgiving break starts: {br_start} ({br_start.strftime('%a')})")

# Walk backward from br_start-1
prev = br_start - timedelta(days=1)
print(f"  Checking backward from: {prev} ({prev.strftime('%a')})")
for i in range(10):
    if prev.weekday() < 5:
        noschool = {date.fromisoformat(n['date']) for n in sy.get('noschool_days', [])}
        is_ns = prev in noschool
        is_in_other = any(
            date.fromisoformat(b2['start']) <= prev <= date.fromisoformat(b2['end'])
            for n2, b2 in sy.get('breaks', {}).items()
        )
        print(f"  Day {prev} ({prev.strftime('%a')}): noschool={is_ns} in_other_break={is_in_other}")
        if not is_ns and not is_in_other:
            print(f"  => Last school day before Thanksgiving: {prev} ({prev.strftime('%a')})")
            break
        prev -= timedelta(days=1)
    else:
        print(f"  Day {prev} ({prev.strftime('%a')}): weekend, skip")
        prev -= timedelta(days=1)
