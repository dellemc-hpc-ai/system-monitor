import json, bisect
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

print('=== Current Christmas intervals ===')
for iv in ivs:
    if 'christmas' in iv['reason']:
        print(f'  {iv["start"]} - {iv["end"]}: {iv["custodian"]} / {iv["reason"]}')

print()
print('=== Dec 28 2025 specifics ===')
target = date(2025, 12, 28)
dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][target.weekday()]
print(f'Dec 28 2025 is a {dow}')
print(f'Christmas break 2025: Dec 19 - Jan 5')
print()

print('=== TX §153.314 analysis ===')
print('Statute: "from the afternoon of December 28 until January 1"')
print('Possessory conservator (Dad) gets Dec 28 afternoon onwards in EVEN years')
print('In ODD years (2025), Mom gets first half, Dad gets second half')
print()

print('=== Current code logic (line ~185) ===')
print('  split_date = Dec 28 (midnight, whole day)')
print('  first_parent = "dad" if is_even else "mom"')
print('  Interval 1: start_d to split_date  -> first_parent')
print('  Interval 2: split_date+1 to end_d  -> second_parent')
print()
print('For 2025 (odd year):')
print('  is_even = False, first_parent = mom, second_parent = dad')
print('  Interval 1: Dec 19 to Dec 28 -> mom')
print('  Interval 2: Dec 29 to Jan 5 -> dad')
print()
print('=== The Dec 28 issue ===')
print('§153.314 says Dad gets Dec 28 FROM AFTERNOON (noon onward)')
print('So Dec 28 morning = first half, Dec 28 afternoon = second half')
print('But our code gives ALL of Dec 28 to first_parent (mom for odd year)')
print()
print('Dec 28 morning in odd year 2025: mom (christmas_first_half)')
print('Dec 28 afternoon in odd year 2025: should be dad (second_parent) per statute')
print('But code gives Dec 28 (all day) to mom (first_parent)')
print()
print('=== The fundamental problem ===')
print('We only have DATE resolution (whole days), no time-of-day')
print('§153.314 intends a TIME split on Dec 28, not a DATE split')
print()
print('Possible fixes:')
print('A. Keep split at Dec 28, ignore afternoon nuance (current behavior, inexact)')
print('B. Change split to Dec 29 (Dad gets Dec 29+, Mom gets Dec 19-28)')
print('   - Odd year 2025: Dad gets Dec 29+ (not Dec 28 afternoon)')
print('   - Even year 2026: Mom gets Dec 29+ (Dad gets Dec 19-28 first half)')
print()
print('=== Current output for Dec 28 2025 ===')
starts = [date.fromisoformat(iv['start']) for iv in ivs]
idx = bisect.bisect_right(starts, target) - 1
if idx >= 0:
    iv = ivs[idx]
    s, e = date.fromisoformat(iv['start']), date.fromisoformat(iv['end'])
    if s <= target <= e:
        print(f'  {target}: {iv["custodian"]} / {iv["reason"]}')
        print(f'  Expected per §153.314 (odd year): Dec 28 afternoon = dad')
        print(f'  Actual: ALL of Dec 28 = {iv["custodian"]}')
        print(f'  --> mom gets Dec 28 all day (morning is correct, afternoon should be dad)')
    else:
        print(f'  {target}: gap')

print()
print('=== Alternative: split at Dec 29 ===')
print('For odd year (2025):')
print('  first_half: Dec 19 - Dec 28 -> mom')
print('  second_half: Dec 29 - Jan 5 -> dad')
print('  Dec 28 all day = mom (first half)')
print('  Dec 29+ = dad (second half)')
print('  --> Dad misses Dec 28 afternoon, but close approximation')
print()
print('For even year (2026):')
print('  first_half: Dec 18 - Dec 28 -> dad')
print('  second_half: Dec 29 - Jan 5 -> mom')
print('  --> Dad gets Dec 18-28 all day (including Dec 28 afternoon as statute intends)')