import json
cal = json.load(open('C:\\Users\\frank\\.openclaw\\workspace\\projects\\TASK-001-allergy-report\\school-calendar-portal\\data\\processed\\rrisd_standard_calendar.json'))
from datetime import date
for sy in cal['schoolYears']:
    print('SY:', sy['year'])
    for nd in sy.get('noschool_days', []):
        d = date.fromisoformat(nd['date'])
        print(f"  {nd['date']} {d.strftime('%a')} en:{nd.get('label',{}).get('en','?')}")