import json

cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'))
for sy_name, sy in cal['school_years'].items():
    print(f'=== {sy_name} ===')
    for br_name, br in sy.get('breaks', {}).items():
        print(f'  {br_name}: {br["start"]} to {br["end"]}')

# Check for Oct 9 in noschool_days
print('\n=== Checking Oct 9 in noschool_days ===')
for sy_name, sy in cal['school_years'].items():
    for ns in sy.get('noschool_days', []):
        if '2026-10' in ns['date']:
            print(f'  {sy_name}: {ns}')
