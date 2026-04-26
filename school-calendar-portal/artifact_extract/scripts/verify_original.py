import json
from datetime import date, timedelta

data = json.load(open('C:\\Users\\frank\\.openclaw\\workspace\\projects\\TASK-001-allergy-report\\school-calendar-portal\\data\\processed\\espo_intervals.json'))
ivs = data['intervals']

def find_custodian(d):
    for iv in ivs:
        if iv['start'] <= d.isoformat() <= iv['end']:
            return iv['custodian'], iv['reason']
    return None, None

print("=== No-school day Fridays (2025-2027) ===")
noschool_fridays = [
    date(2025, 11, 7),   # Staff Dev - 1st Fri
    date(2026, 4, 17),   # Student Holiday - 3rd Fri
    date(2026, 9, 4),    # Staff Dev - 1st Fri
    date(2027, 3, 26),   # Good Friday - 3rd Fri
]
for d in noschool_fridays:
    c, r = find_custodian(d)
    sat = d + timedelta(days=1)
    sun = d + timedelta(days=2)
    cs, rs = find_custodian(sat)
    csu, rsu = find_custodian(sun)
    print(f"  {d} ({d.strftime('%a')}) [rank?]: Fri={c}/{r}, Sat={cs}/{rs}, Sun={csu}/{rsu}")