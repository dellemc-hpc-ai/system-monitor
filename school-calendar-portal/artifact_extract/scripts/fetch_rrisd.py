import sys, os, urllib.request, ssl, re
sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal')
from src.calendar_fetcher_parser.api_crawler import fetch_web_page

url = 'https://roundrockisd.org/o/rrisd/page/calendars'
dest = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_calendar_page.html'
ok = fetch_web_page(url, dest)
print('Fetch ok:', ok)
if ok:
    size = os.path.getsize(dest)
    print('Size:', size)
    content = open(dest, encoding='utf-8', errors='ignore').read()
    links = re.findall(r'href="(https?://[^"]+(?:\.pdf|\.ics)[^"]*)"', content, re.I)
    print('PDF/ICS links:', links[:20])
    links2 = re.findall(r'href="([^"]+)"', content)
    cal_links = [l for l in links2 if 'calendar' in l.lower() or 'cal' in l.lower()]
    print('Calendar links:', cal_links[:20])
else:
    print('Fetch failed')
