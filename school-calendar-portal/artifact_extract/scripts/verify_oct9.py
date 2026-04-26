import json

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(path, 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

for yr in data.get('schoolYears', []):
    if yr.get('year') == '2026-2027':
        days = yr.get('noschoolDays', yr.get('noschool_days', []))
        print(f'2026-2027 has {len(days)} noschool days')
        for d in days:
            if '2026-10' in d.get('date',''):
                print(f'  Oct date: {d["date"]}, label: {d["label"]}')

# Now rebuild custody intervals and HTML
import sys, os
sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src')
from custody_interval_calculator import CustodyIntervalGenerator, load_calendar
from static_web_generator import HTMLBuilder

cal = load_calendar(path)
gen = CustodyIntervalGenerator(cal, mode='espo')
ivs = gen.generate()

# Check Oct 9
for iv in ivs.intervals:
    if iv.start.isoformat() == '2026-10-09':
        print(f'\nOct 9 custody: {iv.custodian} ({iv.reason})')
        print(f'  from {iv.start} to {iv.end}')

# Check surrounding
for d in ['2026-10-08','2026-10-09','2026-10-10','2026-10-11','2026-10-12']:
    for iv in ivs.intervals:
        if iv.start.isoformat() == d:
            print(f'{d}: {iv.custodian} / {iv.reason}')
            break

# Save
ivs_path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'
ivs.save_to(ivs_path)
print(f'\nSaved intervals')

# Build HTML
OUTPUT_DIR = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/output'
os.makedirs(OUTPUT_DIR, exist_ok=True)
html_dest = os.path.join(OUTPUT_DIR, 'custody_school_calendar.html')
HTMLBuilder('RRISD', ivs.dump(), []).build(html_dest)
print(f'Built HTML: {html_dest}')

# Show file hash
import hashlib
h = hashlib.sha1(open(html_dest,'rb').read()).hexdigest()
print(f'HTML hash: {h}')