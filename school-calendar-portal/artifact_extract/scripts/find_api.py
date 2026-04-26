import re

content = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_calendar_page.html', encoding='utf-8', errors='ignore').read()

# Look for API endpoints in JS or data attributes
api_patterns = [
    r'api["\']?\s*:\s*["\']([^"\']+)["\']',
    r'endpoint["\']?\s*:\s*["\']([^"\']+)["\']',
    r'baseUrl["\']?\s*:\s*["\']([^"\']+)["\']',
    r'fetch\(["\']([^"\']+)["\']',
    r'ajax\(["\']([^"\']+)["\']',
    r'xhr\.open\(["\'][^"\']+["\'],\s*["\']([^"\']+)["\']',
    r'ics["\']?\s*:\s*["\']([^"\']+\.ics[^"\']*)["\']',
    r'calendar["\']?\s*:\s*["\']([^"\']+\.ics[^"\']*)["\']',
    r'feed["\']?\s*:\s*["\']([^"\']+\.ics[^"\']*)["\']',
]
for pat in api_patterns:
    found = re.findall(pat, content, re.I)
    if found:
        print(f'Pattern: {pat}')
        for f in found[:5]:
            print(f'  {f}')

# Also look for data-src or data-url
data_urls = re.findall(r'data-(?:src|url|href)=["\']([^"\']+)["\']', content, re.I)
print('Data URLs:', data_urls[:10])

# Look for any Google Calendar link
gcal = re.findall(r'google.*?calendar.*?href=["\']([^"\']+)["\']', content, re.I)
print('Google calendar:', gcal[:5])

# Look for webcal (ICS) links
webcal = re.findall(r'webcal://[^\s"\'<>]+', content)
print('Webcal:', webcal[:5])

# Look for any link with 'ics' or 'feed'
ics_related = re.findall(r'href=["\']([^"\']*(?:ics|feed|subscribe)[^"\']*)["\']', content, re.I)
print('ICS related:', ics_related[:10])
