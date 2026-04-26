import json, sys

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

sys.stdout.buffer.write(f"School years: {[sy['year'] for sy in cal['schoolYears']]}\n".encode('utf-8'))
for sy in cal['schoolYears']:
    sys.stdout.buffer.write(f"{sy['year']}: start={sy['start']}, end={sy['end']}\n".encode('utf-8'))
    br = sy['breaks'].get('summer')
    if br:
        sys.stdout.buffer.write(f"  summer: {br['start']} to {br['end']}\n".encode('utf-8'))
    xmas = sy['breaks'].get('christmas')
    if xmas:
        sys.stdout.buffer.write(f"  christmas: {xmas['start']} to {xmas['end']}\n".encode('utf-8'))