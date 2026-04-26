import json, sys

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

sys.stdout.buffer.write(f'Num school years: {len(cal["schoolYears"])}\n'.encode('utf-8'))
for sy in cal['schoolYears']:
    sys.stdout.buffer.write(f'SY: {sy["year"]} start: {sy["start"]} end: {sy["end"]}\n'.encode('utf-8'))
    br = sy['breaks'].get('summer')
    if br:
        sys.stdout.buffer.write(f'  summer start: {br["start"]} end: {br["end"]}\n'.encode('utf-8'))