import sys
sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src')
from custody_interval_calculator import load_calendar, CustodyIntervalGenerator
from datetime import date, timedelta

cal = load_calendar('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json')

for sy in cal.school_years:
    spring = sy.breaks.get('spring', {})
    if spring:
        end_d = date.fromisoformat(spring.end)
        # Find the Monday when school resumes: first Monday on or after (end_d + 1 day)
        resume_candidate = end_d + timedelta(days=1)
        days_until_monday = (7 - resume_candidate.weekday()) % 7
        resume = resume_candidate + timedelta(days=days_until_monday)
        end_custody = resume - timedelta(days=1)
        sys.stdout.write(f'{sy.year}: br.end={end_d} ({end_d.strftime("%A")})\n')
        sys.stdout.write(f'  resume_candidate={resume_candidate} ({resume_candidate.strftime("%A")})\n')
        sys.stdout.write(f'  days_until_monday={days_until_monday}\n')
        sys.stdout.write(f'  school resumes={resume} ({resume.strftime("%A")})\n')
        sys.stdout.write(f'  custody end={end_custody} ({end_custody.strftime("%A")})\n\n')