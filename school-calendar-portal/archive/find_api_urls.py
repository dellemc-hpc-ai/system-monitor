import re, json

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_calendar_page.html', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find API URLs
urls = re.findall(r'https?://[^\s"<>]+', content)
for u in urls:
    if any(k in u.lower() for k in ['api', 'json', 'event', 'calendar']):
        print(u)

# Also look for JSON data blocks
json_blocks = re.findall(r'window\.__.*?(\{.*?\})', content, re.DOTALL)
if json_blocks:
    for b in json_blocks[:3]:
        print('JSON block:', b[:200])

# Look for any embedded JSON with school event data
scripts_with_data = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
for s in scripts_with_data:
    if 'october' in s.lower() or '2026' in s:
        print('Script with 2026/october:', s[:300])
        print('---')
