import sys, os
os.chdir('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal')
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from src.custody_calculator import CustodyCalculator, load_standard_calendar, build_custody_rules
from src.statute_loader import load_statute

statute = load_statute('TX', 'data/processed')
cal = load_standard_calendar('data/processed/rrisd_standard_calendar.json')

rules = build_custody_rules(statute=statute, distance_miles=0.0, mode='espo', dad_lat=30.44, dad_lon=-97.81, mom_lat=30.44, mom_lon=-97.81)
calc = CustodyCalculator(rules, cal)

# Trace March 16 specifically
d = __import__('datetime').date(2026, 3, 16)
sys.stdout.write(f'_is_noschool_day(3/16): {calc._is_noschool_day(d)}\n')
sys.stdout.write(f'_in_which_break(3/16): {calc._in_which_break(d)}\n')
sys.stdout.write(f'is_odd_year(2026): {2026 % 2 == 1}\n')

# Trace the last school day before spring break logic
for sy in cal['schoolYears']:
    br = sy.get('breaks', {}).get('spring')
    if br:
        sys.stdout.write(f'spring break: {br["start"]} to {br["end"]}\n')

# Check the \"last school day before break\" path
from datetime import date, timedelta
br_start = date.fromisoformat('2026-03-16')
prev = br_start - timedelta(days=1)
noschool = {date.fromisoformat(n['date']) for n in cal['schoolYears'][0].get('noschool_days', [])}
sys.stdout.write(f'noschool set: {noschool}\n')
sys.stdout.write(f'prev (3/15): weekday={prev.weekday()}, in noschool={prev in noschool}\n')