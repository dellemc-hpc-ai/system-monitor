import json
from datetime import date, timedelta
import calendar as calmod

ivs = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json'))['intervals']
cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

def find(d):
    for iv in ivs:
        if iv['start'] <= d.isoformat() <= iv['end']:
            return iv['custodian'], iv['reason']
    return None, None

def _is_noschool_day_NEW(d):
    """Updated version that checks both noschool_days AND breaks"""
    for sy in cal['schoolYears']:
        sy_start = date.fromisoformat(sy['year'][:4] + '-08-01')
        sy_end = date.fromisoformat(sy['year'][5:] + '-07-31')
        if not (sy_start <= d <= sy_end):
            continue
        noschool = {date.fromisoformat(n['date']) for n in sy.get('noschool_days', [])}
        if d in noschool:
            return True
        for br_name, br in sy.get('breaks', {}).items():
            br_start = date.fromisoformat(br['start'])
            br_end = date.fromisoformat(br['end'])
            if br_start <= d <= br_end:
                return True
    return False

out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/check_jan10.txt', 'w', encoding='utf-8')

# Check Jan 9-13, 2026 in detail
for d in [date(2026,1,9), date(2026,1,10), date(2026,1,11), date(2026,1,12), date(2026,1,13)]:
    c, r = find(d)
    is_ns = _is_noschool_day_NEW(d)
    out.write(f"{d} ({d.strftime('%a')}): is_noschool={is_ns} -> {c}/{r}\n")

out.write("\n=== Jan 2026 calendar check ===\n")
# What day of the week is Jan 1, 2026?
jan1 = date(2026, 1, 1)
out.write(f"Jan 1, 2026 = {jan1.strftime('%A')}\n")
for day in range(1, 14):
    d = date(2026, 1, day)
    out.write(f"Jan {day}: {d.strftime('%A')}\n")

out.write("\n=== All Fridays in Jan 2026 ===\n")
c = calmod.Calendar()
for entry in c.itermonthdays2(2026, 1):
    if entry[0] != 0 and entry[1] == 4:
        d = date(2026, 1, entry[0])
        c2, r2 = find(d)
        is_ns = _is_noschool_day_NEW(d)
        fridays = [date(2026, 1, e[0]) for e in c.itermonthdays2(2026, 1) if e[0] != 0 and e[1] == 4]
        fri_rank = sorted(fridays).index(d) + 1
        out.write(f"{d}: {d.strftime('%A')}, rank={fri_rank}, is_noschool={is_ns}, result={c2}/{r2}\n")

out.close()
print("Done")