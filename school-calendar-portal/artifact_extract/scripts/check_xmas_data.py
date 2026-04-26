import json
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

print('=== RRISD Calendar Data ===')
for sy in cal['schoolYears']:
    print(f'\n--- {sy["year"]} ---')
    print(f'School: {sy["start"]} to {sy["end"]}')
    xmas = sy['breaks'].get('christmas', {})
    tg = sy['breaks'].get('thanksgiving', {})

    # Find last day of school before Christmas
    school_end = date.fromisoformat(sy['end'])
    print(f'School ends: {school_end} ({["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][school_end.weekday()]})')

    # Check what day Dec 18/19 is in the school year
    xmas_start = date.fromisoformat(xmas['start'])
    xmas_end = date.fromisoformat(xmas['end'])
    print(f'Christmas break: {xmas["start"]} to {xmas["end"]}')

    # Find days around Christmas
    for d in [xmas_start, xmas_start + __import__('datetime').timedelta(days=-1)]:
        dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]
        in_school = sy['start'] <= str(d) <= sy['end']
        print(f'  {d} ({dow}): in school year? {in_school}')

    print(f'\n  Last school day before Christmas: {xmas_start + __import__("datetime").timedelta(days=-1)}')

    tg_start = date.fromisoformat(tg['start'])
    tg_end = date.fromisoformat(tg['end'])
    print(f'Thanksgiving break: {tg["start"]} to {tg["end"]}')
    print(f'  Last school day before Thanksgiving: {tg_start + __import__("datetime").timedelta(days=-1)}')