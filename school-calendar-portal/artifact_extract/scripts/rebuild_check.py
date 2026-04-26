import json, sys, os, hashlib

sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src')
from custody_interval_calculator.interval_generator import CustodyIntervalGenerator, load_calendar
from static_web_generator import HTMLBuilder

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
cal = load_calendar(path)
gen = CustodyIntervalGenerator(cal, mode='espo')
ivs = gen.generate()

# Show Oct 16-23
sys.stdout.buffer.write(b'Oct 16-23 custody:\n')
for iv_data in ivs.dump():
    if iv_data['start'] >= '2026-10-16' and iv_data['start'] <= '2026-10-23':
        sys.stdout.buffer.write(f"{iv_data['start']}: {iv_data['custodian']} ({iv_data['reason']})\n".encode('utf-8'))

# Save intervals
ivs_path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'
with open(ivs_path, 'w', encoding='utf-8') as f:
    json.dump(ivs.dump(), f, indent=2, ensure_ascii=False)

# Build HTML
OUTPUT_DIR = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/output'
os.makedirs(OUTPUT_DIR, exist_ok=True)
html_dest = os.path.join(OUTPUT_DIR, 'custody_school_calendar.html')
HTMLBuilder('RRISD', ivs.dump(), []).build(html_dest)
h = hashlib.sha1(open(html_dest,'rb').read()).hexdigest()
sys.stdout.buffer.write(f"HTML hash: {h}\n".encode('utf-8'))