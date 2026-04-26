import sys, os
sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src')
from custody_interval_calculator import CustodyIntervalGenerator, load_calendar
from static_web_generator import HTMLBuilder
from datetime import date

PROJECT_ROOT = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal'
DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')

# Load existing calendar data
import json
cal_path = None
for f in os.listdir(DATA_DIR):
    if f.startswith('rrisd_standard_calendar') and f.endswith('.json'):
        cal_path = os.path.join(DATA_DIR, f)
        break

print(f'Using calendar: {cal_path}')
calendar = load_calendar(cal_path)

gen = CustodyIntervalGenerator(calendar, mode='espo')
ivs = gen.generate()

# Check Oct 9 2026
oct9 = None
for iv in ivs.intervals:
    if iv.start.isoformat() <= '2026-10-09' <= iv.end.isoformat():
        print(f'Oct 9 in: {iv.start} to {iv.end} -> {iv.custodian} ({iv.reason})')
        if iv.start.isoformat() == '2026-10-09':
            oct9 = iv

# Check surrounding dates
for d in ['2026-10-08', '2026-10-09', '2026-10-10', '2026-10-11']:
    for iv in ivs.intervals:
        if iv.start.isoformat() == d:
            print(f'{d}: {iv.custodian} ({iv.reason})')
            break

# Save intervals
ivs_path = os.path.join(DATA_DIR, 'espo_intervals.json')
ivs.save_to(ivs_path)
print(f'Intervals saved to {ivs_path}')

# Build HTML
html_dest = os.path.join(OUTPUT_DIR, 'custody_school_calendar.html')
os.makedirs(OUTPUT_DIR, exist_ok=True)
HTMLBuilder('RRISD', ivs.dump(), []).build(html_dest)
print(f'HTML built: {html_dest}')