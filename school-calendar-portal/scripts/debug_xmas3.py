import json
from datetime import date, timedelta

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_calendar_page.html', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

print('=== Searching raw HTML for Dec 19/18 in Christmas context ===')
import re

# Look for Christmas/Winter break dates in raw HTML
matches = re.findall(r'.{0,50}(?:christmas|winter.*break|dec\s*1[89]).{0,50}', content, re.I)
for m in matches[:20]:
    print(repr(m))
    print()

# Also check what day Dec 19 2025 is
d = date(2025, 12, 19)
print(f'Dec 19 2025: {d.strftime("%A")}')
print(f'Dec 18 2025: {date(2025, 12, 18).strftime("%A")}')

# Check if Dec 19 is a noschool day in the calendar
print('\n=== Checking noschool days ===')
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

for sy in cal['schoolYears']:
    if sy['year'] == '2025-2026':
        print('Noschool days in 2025:')
        for nd in sy.get('noschool_days', []):
            nd_d = date.fromisoformat(nd['date'])
            if nd_d.year == 2025:
                print(f'  {nd["date"]}: {nd["label"]}')