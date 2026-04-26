import json, sys, os, hashlib

sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src')
from custody_interval_calculator.interval_generator import CustodyIntervalGenerator, load_calendar
from static_web_generator import HTMLBuilder

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
cal = load_calendar(path)
gen = CustodyIntervalGenerator(cal, mode='espo')
ivs = gen.generate()

OUTPUT_DIR = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/output'
os.makedirs(OUTPUT_DIR, exist_ok=True)
html_dest = os.path.join(OUTPUT_DIR, 'custody_school_calendar.html')
HTMLBuilder('RRISD', ivs.dump(), []).build(html_dest)

h = hashlib.sha1(open(html_dest,'rb').read()).hexdigest()
sys.stdout.buffer.write(f"HTML hash: {h}\n".encode('utf-8'))
sys.stdout.buffer.flush()

# Save intervals JSON manually
ivs_list = ivs.dump()
ivs_path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'
with open(ivs_path, 'w', encoding='utf-8') as f:
    json.dump(ivs_list, f, indent=2, ensure_ascii=False)
sys.stdout.buffer.write(f"Intervals saved: {len(ivs_list)} entries\n".encode('utf-8'))

# Show Oct 9 in intervals
for iv in ivs_list:
    if iv['start'] == '2026-10-09':
        sys.stdout.buffer.write(f"Oct 9 interval: {iv}\n".encode('utf-8'))
        break