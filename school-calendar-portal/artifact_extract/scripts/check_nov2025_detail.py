import json
from datetime import date, timedelta

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

# Check Nov 25-30
for d in [date(2025, 11, 25), date(2025, 11, 26), date(2025, 11, 27), date(2025, 11, 28), date(2025, 11, 29), date(2025, 11, 30), date(2025, 12, 1)]:
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

# Also check Mom 2nd/4th weekends
print('\n--- Mom 2nd/4th weekends in Nov 2025 ---')
for iv in ivs:
    if iv['custodian'] == 'mom' and 'weekend' in iv['reason']:
        sd = date.fromisoformat(iv['start'])
        ed = date.fromisoformat(iv['end'])
        if sd.month == 11 or ed.month == 11 or (sd.month == 10 and ed.month == 11):
            print(f'{iv["start"]} - {iv["end"]}: mom / {iv["reason"]}')

print('\n--- All Nov 2025 intervals ---')
for iv in ivs:
    sd = date.fromisoformat(iv['start'])
    ed = date.fromisoformat(iv['end'])
    if (sd.year == 2025 and sd.month == 11) or (ed.year == 2025 and ed.month == 11):
        print(f'{iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')