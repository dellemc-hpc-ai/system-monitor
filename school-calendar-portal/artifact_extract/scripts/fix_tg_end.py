import json, bisect
from datetime import date

# Update processed calendar JSON
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

for sy in cal['schoolYears']:
    tg = sy['breaks'].get('thanksgiving')
    if tg and sy['year'] == '2025-2026':
        old = tg['end']
        tg['end'] = '2025-11-30'
        print(f'Fixed 2025-2026 Thanksgiving end: {old} -> 2025-11-30')

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'w', encoding='utf-8') as f:
    json.dump(cal, f, indent=2, ensure_ascii=False)
print('Done')