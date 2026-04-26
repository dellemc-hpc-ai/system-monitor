import json, sys

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(path, 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

for sy in cal['schoolYears']:
    sys.stdout.buffer.write(f"SY {sy['year']}: start={sy['start']}, end={sy['end']}\n".encode('utf-8'))
    for name, br in sy['breaks'].items():
        sys.stdout.buffer.write(f"  {name}: {br['start']} to {br['end']}\n".encode('utf-8'))

# Fix summer dates
fixes_applied = []
for sy in cal['schoolYears']:
    if sy['year'] == '2025-2026':
        old = sy['breaks']['summer']
        if old['start'] != '2026-05-22' or old['end'] != '2026-08-12':
            sy['breaks']['summer']['start'] = '2026-05-22'
            sy['breaks']['summer']['end'] = '2026-08-12'
            fixes_applied.append(f"2025-2026 summer: {old['start']}-{old['end']} -> 2026-05-22 to 2026-08-12")
    elif sy['year'] == '2026-2027':
        old = sy['breaks']['summer']
        if old['end'] != '2027-08-16':
            sy['breaks']['summer']['end'] = '2027-08-16'
            fixes_applied.append(f"2026-2027 summer end: {old['end']} -> 2027-08-16")

if fixes_applied:
    for f in fixes_applied:
        sys.stdout.buffer.write(f"FIX: {f}\n".encode('utf-8'))
else:
    sys.stdout.buffer.write(b"No summer fixes needed\n")

with open(path, 'w', encoding='utf-8') as f:
    json.dump(cal, f, indent=2, ensure_ascii=False)
sys.stdout.buffer.write(b"Done\n")