import sys, os, json
BASE = r'C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal'
sys.path.insert(0, os.path.join(BASE, 'src'))
os.chdir(BASE)

from custody_calculator import load_standard_calendar, CustodyCalculator
from statute_loader import load_statute
from rule_builder import build_custody_rules

cal = load_standard_calendar('data/processed/rrisd_standard_calendar.json')
statute = load_statute('TX', 'data/processed')
rules = build_custody_rules(statute, 0.0, 'espo', 30.44, -97.81, 30.44, -97.81)

print("=== Christmas rules ===")
print(json.dumps(rules['holidays']['christmas'], indent=2))

from datetime import date
calc = CustodyCalculator(rules, cal)
print("\n=== Dec 17-31 ===")
for d in [date(2026,12,17+i) for i in range(15)]:
    c, r = calc._get_custodian(d)
    print(f"{d} ({d.strftime('%a')}): {c} / {r}")