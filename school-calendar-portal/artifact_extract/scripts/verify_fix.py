import json
from datetime import date, timedelta

ivs = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'))['intervals']

def find(d):
    for iv in ivs:
        if iv['start'] <= d.isoformat() <= iv['end']:
            return iv['custodian'], iv['reason']
    return None, None

print("=== No-school day Fridays (correct labels) ===")
noschool_fridays = [
    (date(2025,11,7), "Staff Dev", 1),
    (date(2026,4,17), "Student Holiday", 3),
    (date(2026,9,4), "Staff Dev", 1),
    (date(2027,3,26), "Good Friday", 4),
]
for d, name, rank in noschool_fridays:
    c, r = find(d)
    sat = d + timedelta(days=1)
    sun = d + timedelta(days=2)
    cs, rs = find(sat)
    csu, rsu = find(sun)
    print(f"{d} ({d.strftime('%a')}, {rank}th, {name}): Fri={c}/{r}, Sat={cs}/{rs}, Sun={csu}/{rsu}")

print()
print("=== 2027 Easter weekend (Thu Mar 25 - Tue Mar 30) ===")
for delta in range(6):
    d = date(2027, 3, 25) + timedelta(days=delta)
    labels = ["Thu","Fri","Sat","Sun","Mon","Tue"]
    c, r = find(d)
    print(f"  {d} ({labels[delta]}): {c}/{r}")

print()
print("=== Monday no-school cases ===")
monday_noschool = [
    date(2026,1,19),  # MLK Day Mon
    date(2026,2,16),  # Presidents Day Mon
]
for d in monday_noschool:
    sun = d - timedelta(days=1)
    c, r = find(d)
    cs, rs = find(sun)
    print(f"Monday {d} ({d.strftime('%a')}): Sun={cs}/{rs}, Mon={c}/{r}")

print()
print("=== Summary: Is step 4b (non-qual Fri no-school) working? ===")
# 2027-03-26 is 4th Friday no-school
d = date(2027, 3, 26)
thu = date(2027, 3, 25)
c_thu, r_thu = find(thu)
c, r = find(d)
print(f"Fri 2027-03-26 (4th, no-school): Thu={c_thu}/{r_thu}, Fri={c}/{r}")
print(f"Expected: Thu=dad/thursday, Fri=dad/no_school_day (Dad extended through no-school Fri)")
print(f"Result: {'CORRECT' if c == 'dad' and c_thu == 'dad' else 'WRONG'}")