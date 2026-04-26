import json, bisect
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

starts = [date.fromisoformat(iv['start']) for iv in ivs]
for target in [date(2025,12,17), date(2025,12,18), date(2025,12,19), date(2025,12,28), date(2025,12,29)]:
    idx = bisect.bisect_right(starts, target) - 1
    if idx >= 0:
        iv = ivs[idx]
        s, e = date.fromisoformat(iv['start']), date.fromisoformat(iv['end'])
        if s <= target <= e:
            dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][target.weekday()]
            print(f'{target} ({dow}): {iv["custodian"]} / {iv["reason"]}')
        else:
            print(f'{target}: gap')

print('\n--- Christmas intervals ---')
for iv in ivs:
    if 'christmas' in iv['reason']:
        print(iv['start'], '-', iv['end'], iv['custodian'], '/', iv['reason'])

print('\n--- What day is Dec 18 2025? ---')
d = date(2025, 12, 18)
dow = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]
print(f'Dec 18 2025 is a {dow}')
print(f'Christmas break starts: Dec 19')
print(f'Dec 18 is the day BEFORE Christmas break')
print(f'Dec 18 should be regular school day (or noschool if applicable)')
print()
print('If Dec 18 is NOT in Christmas break, it should follow normal ESPO pattern:')
print('2025 is ODD year -> Thu/Fri/Sat/Sun of 1st weekend -> Dad')
print('1st Friday of December 2025: Dec 5')
print('So Dec 18 (4th Friday) should be Dad in odd year -> dad espo_thursday')
print()
print('Wait - that might be CORRECT!')
print('Dec 18 2025 = Thursday, odd year -> dad gets Thursday -> dad espo_thursday')
print()
print('But what if Dec 18 IS supposed to be in Christmas break?')
print('Christmas break 2025: Dec 19 - Jan 5')
print('So Dec 18 is explicitly NOT in Christmas break')
print()
print('Maybe the issue is: Christmas break should START on Dec 18?')
print('If Christmas break starts Dec 18, then Dec 18 would be part of Christmas, not regular school')
print('And the first half for 2025 (odd year) would be Mom or Dad?')