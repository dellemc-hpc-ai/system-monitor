import json, sys
from datetime import date, timedelta

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(path, 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

sys.stdout.buffer.write(f"School years: {[sy['year'] for sy in cal['schoolYears']]}\n".encode('utf-8'))

# Correct summer dates per statute: ends day before next school year starts
# 2025-2026: school Aug 13 2025 - May 21 2026. Summer: May 22 - Aug 12 2026 (day before Aug 13 2026)
# 2026-2027: school Aug 18 2026 - May 27 2027. Summer: May 28 - Aug 16 2027 (day before Aug 17 2027)
CORRECT_SUMMER = {
    '2025-2026': ('2026-05-22', '2026-08-12'),
    '2026-2027': ('2027-05-28', '2027-08-16'),
}

for sy in cal['schoolYears']:
    yr = sy['year']
    if yr in CORRECT_SUMMER:
        start_correct, end_correct = CORRECT_SUMMER[yr]
        current = sy['breaks']['summer']
        if current['start'] != start_correct or current['end'] != end_correct:
            sys.stdout.buffer.write(f"Fixing {yr} summer: {current['start']}-{current['end']} -> {start_correct}-{end_correct}\n".encode('utf-8'))
            current['start'] = start_correct
            current['end'] = end_correct
        else:
            sys.stdout.buffer.write(f"{yr} summer already correct: {start_correct}-{end_correct}\n".encode('utf-8'))

with open(path, 'w', encoding='utf-8') as f:
    json.dump(cal, f, indent=2, ensure_ascii=False)
sys.stdout.buffer.write(b"Calendar fixed.\n")