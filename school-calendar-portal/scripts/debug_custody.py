import json
espo = json.load(open(r'C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal\data\processed\espo_intervals.json'))
print(f"Total intervals: {espo['count']}")
print("\n=== April 2026 intervals ===")
for iv in espo['intervals']:
    s = iv['start']
    e = iv['end']
    if s.startswith('2026-04'):
        print(f"  {s} to {e}: {iv['custodian']} | {iv['reason']}")