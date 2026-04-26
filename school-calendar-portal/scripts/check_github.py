import urllib.request
url = 'https://hanyunfan.github.io/school-calendar-portal/custody_school_calendar.html'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'})
with urllib.request.urlopen(req, timeout=15) as resp:
    content = resp.read().decode('utf-8', errors='replace')
print('GitHub Pages size:', len(content))
# Check for the fix
print('for-loop at:', content.find('for (const m of monthsToShow)'))
print('old forEach at:', content.find('monthsToShow.forEach'))
print('monthsToShow at:', content.find('monthsToShow'))
# Check last git commit time
