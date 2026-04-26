import json
from datetime import date

cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

def _is_noschool_day(d):
    """Same logic as in custody_calculator.py"""
    for sy in cal['schoolYears']:
        sy_start = date.fromisoformat(sy['year'][:4] + '-08-01')
        sy_end = date.fromisoformat(sy['year'][5:] + '-07-31')
        if not (sy_start <= d <= sy_end):
            continue
        noschool = {date.fromisoformat(n['date']) for n in sy.get('noschool_days', [])}
        if d in noschool:
            return True
    return False

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/test_noschool_check.txt', 'w', encoding='utf-8')

out.write("=== All noschool_days and their _is_noschool_day results ===\n")
for sy in cal['schoolYears']:
    for n in sy.get('noschool_days', []):
        d = date.fromisoformat(n['date'])
        name = n.get('name', {})
        if isinstance(name, dict):
            name_en = name.get('en', '')
        else:
            name_en = str(name)
        result = _is_noschool_day(d)
        out.write(f"{d}: _is_noschool_day={result}, name='{name_en}'\n")

out.write("\n=== Key Fridays ===\n")
key_fris = [
    (date(2025,11,7), "Staff Dev/Student Holiday"),
    (date(2026,4,17), "Student Holiday/Staff Dev"),
    (date(2026,9,4), "Staff Dev/Student Holiday"),
    (date(2027,3,26), "Good Friday"),
    (date(2025,10,24), "2nd Fri (Staff Dev on 10/22-23)"),
    (date(2025,10,31), "4th/5th Fri (Halloween)"),
]
for d, note in key_fris:
    result = _is_noschool_day(d)
    out.write(f"{d} ({note}): _is_noschool_day={result}\n")

out.close()
print("Done")