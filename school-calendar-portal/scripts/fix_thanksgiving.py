import json, sys
from datetime import date, timedelta

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(path, 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

for sy in cal['schoolYears']:
    tg = sy['breaks'].get('thanksgiving')
    if tg:
        sys.stdout.buffer.write(f'{sy["year"]} Thanksgiving: {tg["start"]} to {tg["end"]}\n'.encode('utf-8'))
        tg_end = date.fromisoformat(tg['end'])
        sys.stdout.buffer.write(f'  Day after break ends (first day back): {tg_end + timedelta(days=1)}\n'.encode('utf-8'))
        # Fix: Thanksgiving is day before first day students return to school
        # RRISD: students return on Dec 1 2025 and Nov 30 2026
        if sy['year'] == '2025-2026' and tg['end'] != '2025-11-29':
            sys.stdout.buffer.write(f'  Fixing 2025-2026: Nov 28 -> Nov 29\n'.encode('utf-8'))
            tg['end'] = '2025-11-29'
        elif sy['year'] == '2026-2027' and tg['end'] != '2026-11-29':
            sys.stdout.buffer.write(f'  Fixing 2026-2027: Nov 27 -> Nov 29\n'.encode('utf-8'))
            tg['end'] = '2026-11-29'

with open(path, 'w', encoding='utf-8') as f:
    json.dump(cal, f, indent=2, ensure_ascii=False)
sys.stdout.buffer.write(b"Done\n")