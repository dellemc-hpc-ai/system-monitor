import sys, urllib.request, ssl, hashlib

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# GitHub raw at new commit
url = 'https://raw.githubusercontent.com/hanyunfan/school-calendar-portal/48136ae/output/custody_school_calendar.html'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
    content = r.read()
    h = hashlib.sha1(content).hexdigest()
sys.stdout.buffer.write(f'GitHub raw @48136ae hash: {h}\n'.encode('utf-8'))

c = content.decode('utf-8', 'ignore')
idx = c.find('2026-10-23')
if idx >= 0:
    sys.stdout.buffer.write(f'Oct 23: {c[idx-60:idx+80]}\n'.encode('utf-8'))