# Search for October 2026 events in the raw HTML
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_calendar_page.html', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Search for oct 2026 patterns
import re

# Find all oct 9 / oct 12 in the content
for pattern in ['October 9', 'Oct 9', 'october 9', '10/9/2026', '10-09-2026', 'Indigenous', 'Columbus', 'Fall Break', 'fall break']:
    idx = content.find(pattern)
    if idx >= 0:
        print(f"Found '{pattern}' at {idx}:")
        print(content[max(0,idx-100):idx+200])
        print()
