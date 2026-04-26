import json

# Check if local file and committed file are different
proj = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal'

local = json.load(open(f'{proj}/data/processed/espo_intervals.json'))
import subprocess
committed = subprocess.check_output(
    ['git', 'show', 'HEAD:data/processed/espo_intervals.json'],
    cwd=proj
).decode('utf-8')
import io
committed_data = json.loads(committed)

# Find April 10 in both
print("=== LOCAL ===")
for iv in local['intervals']:
    s, e = iv['start'], iv['end']
    if '2026-04-10' in s or '2026-04-10' in e:
        print(iv)

print("\n=== COMMITTED ===")
for iv in committed_data['intervals']:
    s, e = iv['start'], iv['end']
    if '2026-04-10' in s or '2026-04-10' in e:
        print(iv)