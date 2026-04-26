import json, sys, os, hashlib

sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src')
from custody_interval_calculator.interval_generator import CustodyIntervalGenerator, load_calendar
from static_web_generator import HTMLBuilder

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
cal = load_calendar(path)
gen = CustodyIntervalGenerator(cal, mode='espo')
ivs = gen.generate()

ivs_data = ivs.dump()

# Save intervals JSON
ivs_path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'
with open(ivs_path, 'w', encoding='utf-8') as f:
    json.dump(ivs_data, f, indent=2, ensure_ascii=False)

# Build HTML
OUTPUT_DIR = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/output'
os.makedirs(OUTPUT_DIR, exist_ok=True)
html_dest = os.path.join(OUTPUT_DIR, 'custody_school_calendar.html')
HTMLBuilder('RRISD', ivs_data, []).build(html_dest)
h = hashlib.sha1(open(html_dest,'rb').read()).hexdigest()

# Check specific dates in built HTML
with open(html_dest, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

sys.stdout.buffer.write(f'HTML hash: {h}\n'.encode('utf-8'))
for search in ['2026-10-23', '2026-11-20', '2026-10-26']:
    idx = content.find(search)
    if idx >= 0:
        sys.stdout.buffer.write(f'{search} in HTML: {content[idx-50:idx+100]}\n'.encode('utf-8'))