import json
from datetime import date, timedelta

# Load school calendar
cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))

# Get all no-school Fridays with their rank
out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/noschool_analysis.txt', 'w', encoding='utf-8')

import calendar
for sy in cal['schoolYears']:
    year_str = sy['year']
    noschool = {date.fromisoformat(n['date']) for n in sy.get('noschool_days', [])}
    breaks_noschool = set()
    for bname, bdata in sy.get('breaks', {}).items():
        # Break days are school holidays too
        start = date.fromisoformat(bdata['start'])
        end = date.fromisoformat(bdata['end'])
        cur = start
        while cur <= end:
            if cur not in breaks_noschool:
                breaks_noschool.add(cur)
            cur += timedelta(days=1)

    # Find no-school Fridays
    all_noschool = noschool | breaks_noschool
    for year in [int(year_str[:4]), int(year_str[5:])]:
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    d = date(year, month, day)
                except:
                    continue
                if d.weekday() == 4 and d in all_noschool:
                    # Calculate Friday rank
                    fridays = []
                    m = d.month
                    y = d.year
                    c = calendar.Calendar()
                    for entry in c.itermonthdays2(y, m):
                        if entry[0] != 0 and entry[1] == 4:
                            fridays.append(date(y, m, entry[0]))
                    fridays = sorted(fridays)
                    if d in fridays:
                        rank = fridays.index(d) + 1
                        in_break = d in breaks_noschool
                        is_odd = d.year % 2 == 1
                        out.write(f"{d} ({d.strftime('%a')}): {rank}th Friday, in_break={in_break}, odd_year={is_odd}\n")

out.close()
print("Done")