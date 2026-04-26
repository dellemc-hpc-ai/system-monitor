import json
from datetime import date

ivs = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'))['intervals']

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/check_intervals_around_jan9.txt', 'w', encoding='utf-8')

# Find intervals around Jan 8-12, 2026
for iv in ivs:
    start = date.fromisoformat(iv['start'])
    if date(2026,1,5) <= start <= date(2026,1,15):
        out.write(f"{iv['start']} to {iv['end']}: {iv['custodian']}/{iv['reason']}\n")

out.close()
print("Done")