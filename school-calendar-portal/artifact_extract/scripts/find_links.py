import re

content = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_calendar_page.html', encoding='utf-8', errors='ignore').read()
links = re.findall(r'href="(https?://[^"]+)"', content)
internal = re.findall(r'href="(/[^"]+)"', content)
print('External links:')
for l in links[:20]:
    print(' ', l)
print()
print('Internal links with calendar:')
for l in internal:
    if 'calendar' in l.lower() or 'cal' in l.lower():
        print(' ', l)
