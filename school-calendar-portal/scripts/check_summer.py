import json, sys

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'
with open(path, 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

print('=== May-August 2026 ===')
for iv in ivs:
    if '2026-05' <= iv['start'] <= '2026-08-31':
        print(iv['start'], iv['custodian'], iv['reason'])

print('\n=== July 2026 ===')
for iv in ivs:
    if iv['start'].startswith('2026-07'):
        print(iv['start'], iv['custodian'], iv['reason'])

print('\n=== Aug 2026 ===')
for iv in ivs:
    if iv['start'].startswith('2026-08'):
        print(iv['start'], iv['custodian'], iv['reason'])