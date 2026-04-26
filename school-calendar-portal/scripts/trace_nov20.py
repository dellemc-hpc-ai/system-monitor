import sys, os
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

print("=== Nov 16-30 trace ===")
for d in [date(2026,11,16), date(2026,11,17), date(2026,11,18),
          date(2026,11,19), date(2026,11,20), date(2026,11,21),
          date(2026,11,22), date(2026,11,23), date(2026,11,24),
          date(2026,11,25), date(2026,11,26), date(2026,11,27),
          date(2026,11,28), date(2026,11,29), date(2026,11,30)]:
    cust, reason = calc._get_custodian(d)
    is_ns = calc._is_noschool_day(d)
    is_break, break_data = calc._in_which_break(d)
    dow = d.strftime('%a')
    print(f"{d} ({dow}): cust={cust} reason={reason} is_noschool={is_ns} break={is_break}")
