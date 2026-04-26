import json

d = json.load(open(r'C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal\data\processed\espo_intervals.json'))

months = ['2025-08', '2025-09', '2025-10', '2025-11', '2025-12', '2026-01', '2026-02', '2026-03', '2026-04', '2026-05']
for m in months:
    print(f"=== {m} ===")
    for iv in d['intervals']:
        s, e = iv['start'], iv['end']
        if s.startswith(m) or e.startswith(m):
            print(f"  {s} to {e}: {iv['custodian']} | {iv['reason']}")