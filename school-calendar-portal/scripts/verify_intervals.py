import json
from datetime import date as dd

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', encoding='utf-8') as f:
    data = json.load(f)

intervals = data['intervals']

checks = [
    '2025-08-13',  # pre-school summer -> mom
    '2025-09-05',  # 1st Friday -> dad
    '2025-11-24',  # thanksgiving Mon -> dad
    '2025-11-28',  # thanksgiving Fri -> dad
    '2025-12-19',  # christmas first half -> dad
    '2025-12-29',  # christmas second half -> mom
    '2026-03-16',  # spring break -> dad
    '2026-05-10',  # mothers day -> mom
    '2026-06-21',  # fathers day -> dad
    '2026-07-01',  # summer possessory -> dad
    '2026-07-15',  # summer possessory -> dad
    '2026-07-31',  # summer remainder -> mom
    '2026-08-12',  # summer remainder -> mom
]

for ds in checks:
    d = dd.fromisoformat(ds)
    for iv in intervals:
        s = dd.fromisoformat(iv['start'])
        e = dd.fromisoformat(iv['end'])
        if s <= d <= e:
            print(f'{ds}: {iv["custodian"]} / {iv["reason"]}')
            break
    else:
        print(f'{ds}: NOT FOUND')
