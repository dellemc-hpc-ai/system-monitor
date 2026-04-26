import json
from datetime import date, timedelta

ivs = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'))['intervals']

def find(d):
    for iv in ivs:
        if iv['start'] <= d.isoformat() <= iv['end']:
            return iv['custodian'], iv['reason']
    return None, None

print("Trace for 2027-03-26 weekend:")
for delta in range(5):  # Thu to Mon
    d = date(2027, 3, 25) + timedelta(days=delta)
    c, r = find(d)
    print(f"  {d} ({d.strftime('%a')}): {c}/{r}")

print()
print("Direct check:")
for d_str in ["2027-03-25", "2027-03-26", "2027-03-27", "2027-03-28", "2027-03-29", "2027-03-30"]:
    d = date.fromisoformat(d_str)
    c, r = find(d)
    print(f"  {d} ({d.strftime('%a')}): {c}/{r}")