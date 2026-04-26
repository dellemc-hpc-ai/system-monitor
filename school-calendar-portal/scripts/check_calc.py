import sys, os
os.chdir('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal')
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from custody_calculator import CustodyCalculator, load_standard_calendar, build_custody_rules
from statute_loader import load_statute

statute = load_statute('TX', 'data/processed')
cal = load_standard_calendar('data/processed/rrisd_standard_calendar.json')

rules = build_custody_rules(statute=statute, distance_miles=0.0, mode='espo', dad_lat=30.44, dad_lon=-97.81, mom_lat=30.44, mom_lon=-97.81)
calc = CustodyCalculator(rules, cal)
ivs = calc.compute_intervals()

sys.stdout.write(f'Total intervals: {len(ivs)}\n')
for iv in ivs:
    if 'spring' in iv.reason or iv.start.isoformat() in ['2026-03-12','2026-03-13','2026-03-16']:
        sys.stdout.write(f'{iv.start.isoformat()} to {iv.end.isoformat()} {iv.custodian} {iv.reason}\n')