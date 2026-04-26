# Search for Oct 2026 events in the HTML
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_calendar_page.html', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find October 2026 area
idx = content.find('2026')
print(f"First '2026' at: {idx}")

# Look around it
if idx >= 0:
    print(content[idx-200:idx+500])
