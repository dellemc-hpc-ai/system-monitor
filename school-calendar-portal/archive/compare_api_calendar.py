import sys, urllib.request, json, ssl
from datetime import datetime

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

api_holidays = {}
for e in all_events:
    start = e.get('start_at','')
    if not start:
        continue
    dt = datetime.fromisoformat(start.replace('Z','')).replace(tzinfo=None)
    title = e.get('title','')
    is_holiday = any(k in title.lower() for k in [
        'student holiday', 'student & staff', 'no school', 'staff dev',
        'labor day', 'memorial day', 'juneteenth', 'thanksgiving',
        'christmas', 'good friday', 'spring break', 'fall break',
        'winter break', 'summer break', 'indigenous', 'columbus',
        'mlk', 'presidents', 'lunar new year', 'diwali', 'eid',
        'yom kippur', 'rosh hashanah', 'holiday'
    ])
    if is_holiday:
        api_holidays[dt.strftime('%Y-%m-%d')] = title

cal_path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(cal_path, 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

cal_holidays = {}
for yr in cal.get('schoolYears', []):
    for d in yr.get('noschoolDays', []):
        cal_holidays[d['date']] = d['label']['en']

sy1_start = datetime(2025,8,13)
sy1_end = datetime(2026,5,21)
sy2_start = datetime(2026,8,18)
sy2_end = datetime(2027,5,27)

missing = []
for d_str in sorted(api_holidays.keys()):
    d = datetime.strptime(d_str, '%Y-%m-%d')
    in_sy1 = sy1_start <= d <= sy1_end
    in_sy2 = sy2_start <= d <= sy2_end
    if in_sy1 or in_sy2:
        if d_str not in cal_holidays:
            missing.append((d_str, api_holidays[d_str]))

sys.stdout.buffer.write(b'MISSING FROM CALENDAR:\n')
for d, t in missing:
    sys.stdout.buffer.write(f'{d}: {t}\n'.encode('utf-8'))
sys.stdout.buffer.write(f'Total missing: {len(missing)}\n'.encode('utf-8'))

extra = []
for d_str in sorted(cal_holidays.keys()):
    d = datetime.strptime(d_str, '%Y-%m-%d')
    in_sy1 = sy1_start <= d <= sy1_end
    in_sy2 = sy2_start <= d <= sy2_end
    if in_sy1 or in_sy2:
        if d_str not in api_holidays:
            extra.append((d_str, cal_holidays[d_str]))

sys.stdout.buffer.write(b'\nEXTRA IN CALENDAR:\n')
for d, t in extra:
    sys.stdout.buffer.write(f'{d}: {t}\n'.encode('utf-8'))
sys.stdout.buffer.write(f'Total extra: {len(extra)}\n'.encode('utf-8'))