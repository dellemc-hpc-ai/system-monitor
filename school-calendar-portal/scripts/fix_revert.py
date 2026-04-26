import json

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(path, encoding='utf-8') as f:
    cal = json.load(f)

sy = cal['schoolYears'][0]
print('Current SY start:', sy['start'])
sy['start'] = '2025-08-13'  # revert
print('Reverted SY start:', sy['start'])
print('Summer_pre_school present:', 'summer_pre_school' in sy['breaks'])

with open(path, 'w', encoding='utf-8') as f:
    json.dump(cal, f, indent=2, ensure_ascii=False)
print('Saved')
