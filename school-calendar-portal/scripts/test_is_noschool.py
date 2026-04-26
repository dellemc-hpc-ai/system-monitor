import json
from datetime import date

cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/test_is_noschool.txt', 'w', encoding='utf-8')

def _is_noschool_day(d):
    for sy in cal['schoolYears']:
        sy_start = date.fromisoformat(sy['year'][:4] + '-08-01')
        sy_end = date.fromisoformat(sy['year'][5:] + '-07-31')
        if not (sy_start <= d <= sy_end):
            out.write(f"    {d}: NOT in {sy['year']} range ({sy_start} to {sy_end})\n")
            continue
        out.write(f"    {d}: IN {sy['year']} range\n")
        noschool = {date.fromisoformat(n['date']) for n in sy.get('noschool_days', [])}
        out.write(f"      noschool set: {noschool}\n")
        out.write(f"      d in noschool: {d in noschool}\n")
        if d in noschool:
            return True
        for br_name, br in sy.get('breaks', {}).items():
            br_start = date.fromisoformat(br['start'])
            br_end = date.fromisoformat(br['end'])
            out.write(f"      break '{br_name}': {br_start} to {br_end}\n")
            if br_start <= d <= br_end:
                out.write(f"      -> {d} IS in break {br_name}\n")
                return True
    return False

out.write("=== Testing _is_noschool_day for April 10, 2026 ===\n")
result = _is_noschool_day(date(2026, 4, 10))
out.write(f"\nResult: {result}\n")

out.write("\n=== Testing April 7, 2026 ===\n")
result2 = _is_noschool_day(date(2026, 4, 7))
out.write(f"\nResult: {result2}\n")

out.close()
print("Done")