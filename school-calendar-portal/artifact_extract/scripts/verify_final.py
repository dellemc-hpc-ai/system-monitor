import sys, os
sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src')
from custody_interval_calculator.interval_generator import CustodyIntervalGenerator, load_calendar
from datetime import date

cal = load_calendar('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json')
gen = CustodyIntervalGenerator(cal, mode='espo')
ivs = gen.generate()

tests = [
    '2025-11-24', '2025-11-27', '2025-12-19', '2025-12-29',
    '2026-11-23', '2026-11-26', '2026-03-16',
]
for ts in tests:
    d2 = date.fromisoformat(ts)
    iv = ivs.query(d2)
    print(ts, '->', iv.custodian if iv else 'None', '(' + (iv.reason if iv else 'None') + ')')
