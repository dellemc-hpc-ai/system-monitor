import re

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/pdf/rrisd_2025-2026.pdf', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find calendar-related links
links = re.findall(r'href=["\']([^"\']*calendar[^"\']*)["\']', content, re.I)
print('Calendar links:', links[:20])

# Also look for .ics links
ics_links = re.findall(r'href=["\']([^"\']*\.ics[^"\']*)["\']', content, re.I)
print('ICS links:', ics_links[:10])

# Search for any feed/calendar URLs
feed_links = re.findall(r'href=["\']([^"\']*(?:feed|agenda|schedule|cal)[^"\']*)["\']', content, re.I)
print('Feed/schedule links:', feed_links[:10])
