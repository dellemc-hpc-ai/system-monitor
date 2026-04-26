import sys, urllib.request, json, ssl, hashlib

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Fetch GitHub Pages HTML
url = 'https://hanyunfan.github.io/school-calendar-portal/custody_school_calendar.html'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
    gh_content = r.read()
    gh_hash = hashlib.sha1(gh_content).hexdigest()
sys.stdout.buffer.write(f'GitHub Pages HTML hash: {gh_hash}\n'.encode('utf-8'))

# Fetch local HTML
local_path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/output/custody_school_calendar.html'
with open(local_path, 'rb') as f:
    local_content = f.read()
    local_hash = hashlib.sha1(local_content).hexdigest()
sys.stdout.buffer.write(f'Local HTML hash: {local_hash}\n'.encode('utf-8'))

# Fetch GitHub raw HTML (master branch)
url2 = 'https://raw.githubusercontent.com/hanyunfan/school-calendar-portal/master/output/custody_school_calendar.html'
req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req2, timeout=15, context=ctx) as r:
    raw_content = r.read()
    raw_hash = hashlib.sha1(raw_content).hexdigest()
sys.stdout.buffer.write(f'GitHub raw HTML hash: {raw_hash}\n'.encode('utf-8'))

# Check Oct 23 in all three
for label, content in [('GitHub Pages', gh_content.decode('utf-8','ignore')), ('Local', local_content.decode('utf-8','ignore')), ('GitHub raw', raw_content.decode('utf-8','ignore'))]:
    idx = content.find('2026-10-23')
    if idx >= 0:
        sys.stdout.buffer.write(f'{label} - Oct 23: {content[idx-60:idx+80]}\n'.encode('utf-8'))