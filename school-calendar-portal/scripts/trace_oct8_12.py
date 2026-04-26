import sys, json, os
BASE = r'C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal'
sys.path.insert(0, os.path.join(BASE, 'src'))
os.chdir(BASE)
from datetime import date
from custody_calculator import load_standard_calendar, CustodyCalculator
from statute_loader import load_statute
from rule_builder import build_custody_rules

cal = load_standard_calendar('data/processed/rrisd_standard_calendar.json')
statute = load_statute('TX', 'data/processed')
rules = build_custody_rules(statute, 0.0, 'espo', 30.44, -97.81, 30.44, -97.81)
calc = CustodyCalculator(rules, cal)

# Check noschool
sy = cal['schoolYears'][1]
noschool = [n['date'] for n in sy.get('noschool_days',[])]
print('Oct 8 in noschool:', '2026-10-08' in noschool)
print('Oct 9 in noschool:', '2026-10-09' in noschool)
print()

for d in [date(2026,10,8), date(2026,10,9), date(2026,10,10),
         date(2026,10,11), date(2026,10,12)]:
    cust, reason = calc._get_custodian(d)
    is_ns = calc._is_noschool_day(d)
    dow = d.strftime('%a')
    print(f'{d} ({dow}): custodian={cust} reason={reason} is_noschool={is_ns}')
