import json
import sys

# Write output to file instead of stdout to avoid encoding issues
out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/debug_2027_out.txt', 'w', encoding='utf-8')

cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))
for sy in cal['schoolYears']:
    if '2026' in sy['year']:
        out.write(f"\n{sy['year']}:\n")
        ns = sy.get('noschool_days', [])
        for n in ns:
            try:
                name = n.get('name', n.get('label', '?'))
                out.write(f"  noschool: {n['date']} - {name}\n")
            except:
                out.write(f"  noschool: {n['date']}\n")
        spring = sy.get('breaks', {}).get('spring', {})
        out.write(f"  spring break: {spring}\n")

out.close()
print("Done")