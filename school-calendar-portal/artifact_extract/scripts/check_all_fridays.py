import urllib.request, json, ssl
from datetime import datetime, timezone

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

all_events = []
for page in range(1, 30):
    url = f'https://thrillshare.com/api/v4/o/27049/cms/events?page_no={page}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            data = json.loads(r.read())
        evs = data.get('events', [])
        if not evs:
            break
        all_events.extend(evs)
    except:
        break

results = []
for e in all_events:
    start = e.get('start_at','')
    if not start:
        continue
    dt = datetime.fromisoformat(start.replace('Z','')).replace(tzinfo=None)
    title = e.get('title','')

    is_friday = (dt.weekday() == 4)
    is_student_holiday = any(k in title.lower() for k in ['student holiday', 'student & staff', 'no school', 'staff dev'])

    sy1 = datetime(2025,8,13) <= dt <= datetime(2026,5,21)
    sy2 = datetime(2026,8,18) <= dt <= datetime(2027,5,27)

    if is_friday and is_student_holiday and (sy1 or sy2):
        sy = 'sy1' if sy1 else 'sy2'
        results.append((dt.strftime('%Y-%m-%d'), dt.strftime('%A'), title, sy))

results.sort()
for d, day, title, sy in results:
    print(f'{d} ({day}) [{sy}]: {title}')

# Now cross-reference with current calendar data
import json as j
cal_path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(cal_path, 'r', encoding='utf-8-sig') as f:
    cal = j.load(f)

all_noschool = {}
for yr in cal.get('schoolYears', []):
    for d in yr.get('noschoolDays', []):
        all_noschool[d['date']] = d['label']['en']

print('\n=== Cross-reference with current calendar ===')
for d, day, title, sy in results:
    status = 'IN CALENDAR' if d in all_noschool else 'MISSING FROM CALENDAR'
    print(f'{d}: {status} | {title}')