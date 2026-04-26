import re

# Read the HTML page to find JS bundle URLs
content = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_calendar_page.html', encoding='utf-8', errors='ignore').read()

# Find JS bundle URLs
js_bundles = re.findall(r'src="(/[^"<>]*\.js[^"<>]*)"', content)
print('JS bundles found:', len(js_bundles))
for j in js_bundles[:5]:
    print(' ', j)

# Find any data or config JSON
json_configs = re.findall(r'(?:data|config|settings)\s*[=:]\s*({[^}<]{50,500}})', content)
print('JSON configs:', json_configs[:3])

# Look for any JSON data embedded
json_data = re.findall(r'"(https?://[^"]*\.(?:json|ics)[^"]*)"', content)
print('JSON/ICS URLs:', json_data[:10])
