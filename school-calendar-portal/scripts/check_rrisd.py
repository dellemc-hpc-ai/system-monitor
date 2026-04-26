import json, sys

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

sys.stdout.buffer.write(f'District: {cal.get("district")}\n'.encode('utf-8'))
sys.stdout.buffer.write(f'School years: {len(cal["schoolYears"])}\n'.encode('utf-8'))
for sy in cal['schoolYears']:
    sys.stdout.buffer.write(f"Year: {sy['year']} | start: {sy['start']} | end: {sy['end']}\n".encode('utf-8'))
    for k, v in sy['breaks'].items():
        sys.stdout.buffer.write(f"  {k}: {v['start']} - {v['end']}\n".encode('utf-8'))