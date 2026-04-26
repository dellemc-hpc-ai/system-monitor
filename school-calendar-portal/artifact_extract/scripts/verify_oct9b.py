import json, sys, os, hashlib

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(path, 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

found_oct9 = False
for yr in data.get('schoolYears', []):
    if yr.get('year') == '2026-2027':
        days = yr.get('noschoolDays', yr.get('noschool_days', []))
        print(f'2026-2027 noschool_days count: {len(days)}')
        for d in days:
            if '2026-10' in d.get('date',''):
                sys.stdout.buffer.write(f"Oct date: {d['date']}\n".encode('utf-8'))
                sys.stdout.buffer.flush()

sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src')
from custody_interval_calculator import CustodyIntervalGenerator, load_calendar
from static_web_generator import HTMLBuilder

cal = load_calendar(path)
gen = CustodyIntervalGenerator(cal, mode='espo')
ivs = gen.generate()

results = []
for iv in ivs.intervals:
    if iv.start.isoformat() in ['2026-10-08','2026-10-09','2026-10-10','2026-10-11','2026-10-12','2026-10-13']:
        results.append(f"{iv.start.isoformat()}: {iv.custodian} ({iv.reason})")

for r in results:
    sys.stdout.buffer.write((r + '\n').encode('utf-8'))
    sys.stdout.buffer.flush()

ivs_path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'
ivs.save_to(ivs_path)

OUTPUT_DIR = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/output'
os.makedirs(OUTPUT_DIR, exist_ok=True)
html_dest = os.path.join(OUTPUT_DIR, 'custody_school_calendar.html')
HTMLBuilder('RRISD', ivs.dump(), []).build(html_dest)

h = hashlib.sha1(open(html_dest,'rb').read()).hexdigest()
sys.stdout.buffer.write(f"HTML hash: {h}\n".encode('utf-8'))
sys.stdout.buffer.flush()