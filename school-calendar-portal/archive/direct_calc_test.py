import json
import sys
from datetime import date

sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src')
from custody_calculator import CustodyCalculator
from rule_builder import build_custody_rules

rules_data = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/config/texas_espo_spo_rules.json', encoding='utf-8'))
cal_data = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

rules = build_custody_rules(rules_data['rules']['espo'])
cc = CustodyCalculator(rules, cal_data['schoolYears'])

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/direct_calc.txt', 'w', encoding='utf-8')

# Test specific dates
test_dates = [
    date(2026, 1, 9),   # Thu before Jan 10
    date(2026, 1, 10),  # The problematic Friday
    date(2026, 1, 11),  # Sat after
    date(2026, 1, 12),  # Sun after
    date(2026, 1, 13),  # Mon
    date(2025, 12, 26), # Christmas break Friday
    date(2026, 11, 28), # Thanksgiving break Friday
]

for d in test_dates:
    result = cc._get_custodian(d)
    is_ns = cc._is_noschool_day(d)
    out.write(f"{d} ({d.strftime('%a')}): is_noschool={is_ns} -> {result}\n")

out.close()
print("Done")