import json

d = json.load(open(r'C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal\data\processed\espo_intervals.json'))

print("=== April 2026 intervals ===")
for iv in d['intervals']:
    s = iv['start']
    if s.startswith('2026-04') or (s < '2026-04-01' and iv['end'] >= '2026-04-01'):
        print(f"{iv['start']} to {iv['end']}: {iv['custodian']} | {iv['reason']}")

print()
print("=== June 2026 intervals ===")
for iv in d['intervals']:
    s = iv['start']
    if s.startswith('2026-06') and s <= '2026-06-30':
        print(f"{iv['start']} to {iv['end']}: {iv['custodian']} | {iv['reason']}")