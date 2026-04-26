import json
from datetime import date

cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/noschool_filter.txt', 'w', encoding='utf-8')

def is_student_noschool(entry):
    """Check if a noschool entry means students don't come.
    'Student Holiday' or 'Student & Staff Holiday' = students don't come
    'Staff Dev' or 'Teacher Work Day' without 'Student' = ambiguous, typically staff only
    """
    name = entry.get('name', entry.get('label', ''))
    if isinstance(name, dict):
        name = name.get('en', '')
    name_lower = name.lower()
    # Only count as student no-school if 'student' is mentioned
    return 'student' in name_lower

for sy in cal['schoolYears']:
    out.write(f"\n=== {sy['year']} ===\n")
    out.write(f"All noschool_days entries:\n")
    for n in sy.get('noschool_days', []):
        date_str = n['date']
        name = n.get('name', n.get('label', '???'))
        if isinstance(name, dict):
            name_en = name.get('en', '')
        else:
            name_en = str(name)
        student_noschool = is_student_noschool(n)
        out.write(f"  {date_str}: [{'+' if student_noschool else '-'}] {name_en}\n")

out.write("\n=== Key Fridays analysis ===\n")
key_fris = ['2025-10-24', '2025-10-31', '2025-11-07', '2026-04-17', '2026-09-04', '2027-03-26']
for sy in cal['schoolYears']:
    for n in sy.get('noschool_days', []):
        d = date.fromisoformat(n['date'])
        for fri_str in key_fris:
            fri = date.fromisoformat(fri_str)
            if d == fri:
                name = n.get('name', {})
                if isinstance(name, dict):
                    name_en = name.get('en', '')
                else:
                    name_en = str(name)
                student_noschool = is_student_noschool(n)
                out.write(f"{fri_str}: [{'+' if student_noschool else '-'}] {name_en}\n")

out.close()
print("Done")