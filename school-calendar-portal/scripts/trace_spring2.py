import sys, os, json
sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src')
from custody_calculator import CustodyCalculator, load_standard_calendar
from datetime import date, timedelta

cal = load_standard_calendar('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json')

# Load rules from processed espo_intervals
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json') as f:
    intervals_data = json.load(f)

# Build minimal rules from statute_loader
from src.statute_loader import load_statute
statute = load_statute("TX", "C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed")
from src.rule_builder import build_custody_rules
rules = build_custody_rules(statute=statute, distance_miles=0.0, mode="espo",
    dad_lat=30.4425, dad_lon=-97.8134, mom_lat=30.4425, mom_lon=-97.8134)

cc = CustodyCalculator(rules, cal)

for d in [date(2026,3,20), date(2026,3,21), date(2026,3,22), date(2026,3,23), date(2026,3,24), date(2026,4,1), date(2026,5,7)]:
    custodian, reason = cc._get_custodian(d)
    in_br, br_data = cc._in_which_break(d)
    print(f"{d} ({d.strftime('%a')}): {custodian}/{reason} | in_break: {in_br}")
    # Debug: show what the spring break extents are for each sy
    for sy in cc.school_years:
        spring = sy.get('breaks', {}).get('spring')
        if spring:
            from datetime import timedelta
            br_start = date.fromisoformat(spring['start'])
            br_end_raw = date.fromisoformat(spring['end'])
            resume_candidate = br_end_raw + timedelta(days=1)
            days_until_monday = (7 - resume_candidate.weekday()) % 7
            school_resume = resume_candidate + timedelta(days=days_until_monday)
            br_end_ext = school_resume - timedelta(days=1)
            br_start_ext = cc._last_school_day_before_break('spring')
            if br_start_ext:
                br_start_ext = br_start_ext.isoformat()
            print(f'  sy {sy["year"]}: spring {spring["start"]}-{spring["end"]} -> extended {br_start_ext}-{br_end_ext.isoformat()}')
