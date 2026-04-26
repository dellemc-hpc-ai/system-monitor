import json
from datetime import date, timedelta

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

# Build interval set
active = {}
for iv in ivs:
    d = date.fromisoformat(iv['start'])
    end = date.fromisoformat(iv['end'])
    while d <= end:
        active[d.isoformat()] = iv['custodian']
        d += timedelta(days=1)

# Check Oct 2026 Saturdays and Sundays
print('=== Oct 2026 weekends ===')
d = date(2026, 10, 1)
while d <= date(2026, 10, 31):
    if d.weekday() in (5, 6):
        val = active.get(d.isoformat())
        print(f'{d.strftime("%a %Y-%m-%d")}: {val if val else "WHITE (no interval)"}')
    d += timedelta(days=1)

# Also check May 2027
print('\n=== May 2027 weekends ===')
d = date(2027, 5, 1)
while d <= date(2027, 5, 31):
    if d.weekday() in (5, 6):
        val = active.get(d.isoformat())
        print(f'{d.strftime("%a %Y-%m-%d")}: {val if val else "WHITE (no interval)"}')
    d += timedelta(days=1)

# Check 2nd/4th weekends explicitly
print('\n=== 2nd/4th weekend analysis Oct 2026 ===')
# Find all Fridays and their positions
fridays_in_oct = []
d = date(2026, 10, 1)
while d <= date(2026, 10, 31):
    if d.weekday() == 4:
        fridays_in_oct.append(d)
    d += timedelta(days=1)
print(f'Fridays in Oct 2026: {[f.day for f in fridays_in_oct]}')
for i, fri in enumerate(fridays_in_oct):
    sat = fri + timedelta(days=1)
    sun = fri + timedelta(days=2)
    fc = active.get(fri.isoformat(), 'WHITE')
    sc = active.get(sat.isoformat(), 'WHITE')
    nc = active.get(sun.isoformat(), 'WHITE')
    print(f'Weekend {i+1} (Fri {fri.day}): Fri={fc}, Sat={sc}, Sun={nc}')