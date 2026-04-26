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

with open(html_dest, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

sys.stdout.buffer.write(f'output/ HTML hash: {h}\n'.encode('utf-8'))
idx = content.find('2026-10-23')
if idx >= 0:
    sys.stdout.buffer.write(f'Oct 23 in output HTML: {content[idx-50:idx+80]}\n'.encode('utf-8'))

# ALSO build root custody_school_calendar.html
root_dest = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/custody_school_calendar.html'
HTMLBuilder('RRISD', ivs_data, []).build(root_dest)
root_h = hashlib.sha1(open(root_dest,'rb').read()).hexdigest()

with open(root_dest, 'r', encoding='utf-8', errors='ignore') as f:
    root_content = f.read()

sys.stdout.buffer.write(f'root HTML hash: {root_h}\n'.encode('utf-8'))
idx2 = root_content.find('2026-10-23')
if idx2 >= 0:
    sys.stdout.buffer.write(f'Oct 23 in root HTML: {root_content[idx2-50:idx2+80]}\n'.encode('utf-8'))