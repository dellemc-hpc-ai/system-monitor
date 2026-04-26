import json
from datetime import date, timedelta

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

# Check Nov 2025
for d in [date(2025, 11, 24), date(2025, 11, 25), date(2025, 11, 26), date(2025, 11, 27), date(2025, 11, 28), date(2025, 11, 29), date(2025, 11, 30)]:
    dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]
    iv_found = None
    for iv in ivs:
        sd = date.fromisoformat(iv['start'])
        ed = date.fromisoformat(iv['end'])
        if sd <= d <= ed:
            iv_found = iv
            break
    if iv_found:
        print(f'{d} ({dow}): {iv_found["custodian"]} / {iv_found["reason"]}')
    else:
        print(f'{d} ({dow}): NO INTERVAL')

print('\n--- Thanksgiving break in calendar ---')
for sy in cal['schoolYears']:
    if sy['year'] == '2025-2026':
        tg = sy['breaks'].get('thanksgiving')
        if tg:
            print(f"2025-2026 Thanksgiving: {tg['start']} to {tg['end']}")

print('\n--- First day back after Thanksgiving ---')
# What date do students go back?
for sy in cal['schoolYears']:
    if sy['year'] == '2025-2026':
        print(f"School end of 2025-2026: {sy['end']}")
        # Thanksgiving ends day before first day back
        # So we can infer: day after Thanksgiving end = first day of school after break
        tg_end = date.fromisoformat(sy['breaks']['thanksgiving']['end'])
        print(f"Day after break ends (first day back): {tg_end + timedelta(days=1)}")