import json
from datetime import date

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(path, encoding='utf-8') as f:
    cal = json.load(f)

# Check: is Aug 13-17 in ANY summer break across all school years?
test_dates = [date(2025, 8, d) for d in range(10, 20)]
print("Is Aug 10-19, 2025 in any summer break?")
for d in test_dates:
    found = False
    for sy in cal['schoolYears']:
        for br_name, br in sy.get('breaks', {}).items():
            if br_name == 'summer':
                br_start = date.fromisoformat(br['start'])
                br_end = date.fromisoformat(br['end'])
                if br_start <= d <= br_end:
                    print(f'  {d}: YES (in {sy["year"]} summer {br["start"]}-{br["end"]})')
                    found = True
                    break
        if found:
            break
    if not found:
        print(f'  {d}: NO (not in any summer break)')
