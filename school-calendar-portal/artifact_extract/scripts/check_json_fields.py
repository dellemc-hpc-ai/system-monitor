import json
from datetime import date

cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/check_json_fields.txt', 'w', encoding='utf-8')

for sy in cal['schoolYears']:
    out.write(f"\n=== {sy['year']} ===\n")
    out.write(f"noschool_days type: {type(sy.get('noschool_days', []))}\n")
    out.write(f"noschool_days count: {len(sy.get('noschool_days', []))}\n")
    if sy.get('noschool_days'):
        first = sy['noschool_days'][0]
        out.write(f"First entry type: {type(first)}\n")
        out.write(f"First entry keys: {first.keys() if hasattr(first, 'keys') else 'N/A'}\n")
        out.write(f"First entry: {first}\n")

    # Also check schoolYears structure
    out.write(f"\nschoolYears[0] keys: {list(sy.keys())}\n")

out.close()
print("Done")