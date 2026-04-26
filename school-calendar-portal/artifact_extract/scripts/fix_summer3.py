import json

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(path, encoding='utf-8') as f:
    cal = json.load(f)

sy = cal['schoolYears'][0]
br = sy['breaks']['summer']
print('SY start:', sy['start'])
print('Summer start:', br['start'])
print('Summer end:', br['end'])
print('Keys in breaks:', list(sy['breaks'].keys()))

# Fix summer_pre_school: covers May 22-Aug 17, 2025
# This handles Aug 13-17 (pre-instruction days) as summer (mom)
sy['breaks']['summer_pre_school'] = {
    'start': '2025-05-22',
    'end': '2025-08-17',
    'label': {'en': 'Pre-School Summer', 'cn': ''}
}
print('Added summer_pre_school')
print('All break keys now:', list(sy['breaks'].keys()))

with open(path, 'w', encoding='utf-8') as f:
    json.dump(cal, f, indent=2, ensure_ascii=False)
print('Saved')
