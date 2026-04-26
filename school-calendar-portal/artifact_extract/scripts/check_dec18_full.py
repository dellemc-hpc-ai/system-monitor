import json, bisect
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

# Check Dec 18 2025
target = date(2025, 12, 18)
starts = [date.fromisoformat(iv['start']) for iv in ivs]
idx = bisect.bisect_right(starts, target) - 1
if idx >= 0:
    iv = ivs[idx]
    s, e = date.fromisoformat(iv['start']), date.fromisoformat(iv['end'])
    if s <= target <= e:
        print(f'Dec 18 2025: {iv["custodian"]} / {iv["reason"]} (interval: {iv["start"]}-{iv["end"]})')
    else:
        print(f'Dec 18 2025: gap')

# Check Christmas intervals for both years
print('\n--- Christmas intervals ---')
for iv in ivs:
    if 'christmas' in iv['reason']:
        print(iv['start'], '-', iv['end'], iv['custodian'], '/', iv['reason'])

print('\n--- Analysis ---')
print('2025 is ODD year')
print('2026 is EVEN year')
print()
print('Code rule (from comment): even year -> Dad first half, odd year -> Mom first half')
print()
print('For 2025-2026 (odd year, ends in 2026): Dad first half')
print('For 2026-2027 (even year, ends in 2027): Mom first half')
print()
print('But 2026 is even year - so which rule applies to Dec 18 2025?')
print('The date is Dec 18 2025 (calendar year 2025, odd)')
print('The school year is 2025-2026 (ends in 2026, even)')
print('The Christmas break starts Dec 18 2025 (in calendar year 2025)')
print('Which year determines odd/even for the split?')
print()
print('If using CALENDAR YEAR of Dec 18 (2025, odd): Dad first half')
print('If using SCHOOL YEAR (2025-2026, even): Mom first half')
print()
print('Data shows 2025-2026 Christmas: Dad first half')
print('This suggests the code uses calendar year 2025 (odd) -> Dad first half')
print('But 2026 Christmas also shows Dad first half (should be Mom if even year)')
print()
print('Check 2026-2027 Christmas data:')
for iv in ivs:
    if '2026-12-18' <= iv['start'] <= '2027-01-05' and 'christmas' in iv['reason']:
        print(iv['start'], '-', iv['end'], iv['custodian'], '/', iv['reason'])