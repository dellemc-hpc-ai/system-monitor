import json
from datetime import date

cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/noschool_detail.txt', 'w', encoding='utf-8')

for sy in cal['schoolYears']:
    out.write(f"\n=== {sy['year']} ===\n")
    out.write(f"noschool_days (all):\n")
    for n in sy.get('noschool_days', []):
        date_str = n['date']
        # Check if it has 'name' field and what it contains
        name = n.get('name', n.get('label', '???'))
        # Write raw entry
        out.write(f"  {date_str}: {name}\n")

    out.write(f"\nbreaks noschool_days:\n")
    for bname, bdata in sy.get('breaks', {}).items():
        start = date.fromisoformat(bdata['start'])
        end = date.fromisoformat(bdata['end'])
        out.write(f"  {bname}: {bdata['start']} to {bdata['end']}\n")

out.close()
print("Done")