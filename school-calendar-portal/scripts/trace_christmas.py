import sys
sys.path.insert(0, 'src')
from custody_calculator import CustodyCalculator
from datetime import date
import json

with open('config/texas_espo_spo_rules.json', 'r', encoding='utf-8') as f:
    rules = json.load(f)
with open('data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8') as f:
    calendar_data = json.load(f)

calc = CustodyCalculator(rules, calendar_data)

print("=== Dec 15-31 trace ===")
for d in [date(2026,12,15+i) for i in range(17)]:
    br = calc._in_which_break(d)
    # Use internal get_custodian
    c, r = calc._get_custodian(d)
    print(f"{d} ({'Mon Tue Wed Thu Fri Sat Sun'.split()[d.weekday()]}): cust={c} reason={r} break={br[0] if br else None}")
