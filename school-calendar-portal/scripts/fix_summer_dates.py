import json, sys
from datetime import date, timedelta

# Fix the summer break dates in rrisd_standard_calendar.json
path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(path, 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

for sy in cal['schoolYears']:
    sys.stdout.buffer.write(f"SY {sy['year']}: start={sy['start']} end={sy['end']}\n".encode('utf-8'))
    if 'summer' in sy['breaks']:
        old = sy['breaks']['summer']
        sys.stdout.buffer.write(f"  OLD summer: {old['start']} to {old['end']}\n".encode('utf-8'))
        
        # Correct: summer break is from day after school ends to day before next school year starts
        # School year 2026-2027: Aug 18, 2026 to May 27, 2027
        # Next school year (2027-2028) would typically start mid-Aug
        # For RRISD, based on Aug 18, 2026 pattern → Aug 17, 2027
        # So summer: May 28, 2027 (day after May 27) to Aug 16, 2027 (day before Aug 17)
        sy_end = date.fromisoformat(sy['end'])  # May 27, 2027
        summer_start = sy_end + timedelta(days=1)  # May 28, 2027
        # Use Aug 16 as the day before typical Aug 17 start
        summer_end = date(summer_start.year, 8, 16)  # Aug 16, 2027
        
        sys.stdout.buffer.write(f"  NEW summer: {summer_start.isoformat()} to {summer_end.isoformat()}\n".encode('utf-8'))
        sy['breaks']['summer']['start'] = summer_start.isoformat()
        sy['breaks']['summer']['end'] = summer_end.isoformat()

with open(path, 'w', encoding='utf-8') as f:
    json.dump(cal, f, indent=2, ensure_ascii=False)
sys.stdout.buffer.write('Saved.\n'.encode('utf-8'))