import json

base = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal'
with open(base + '/output/custody_school_calendar.html', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Extract ESPO intervals
espo_start = content.find('ESPO_INTERVALS =') + len('ESPO_INTERVALS =')
espo_arr_start = content.find('[', espo_start)
depth = 0
end = espo_arr_start
for i, c in enumerate(content[espo_arr_start:]):
    if c == '[': depth += 1
    elif c == ']':
        depth -= 1
        if depth == 0:
            end = espo_arr_start + i + 1
            break
arr_str = content[espo_arr_start:end]
intervals = json.loads(arr_str)

# Now let's do the EXACT same thing the JS does for April 3, 2026
# cellDate = new Date(2026, 3, 3)  -> April 3, 2026 (year=2026, month=3 because 0-indexed, day=3)
# fmtDate(cellDate) -> cellDate.toISOString().slice(0, 10) -> '2026-04-03'
# queryCustodian('2026-04-03')

# JS Date comparison:
# new Date('2026-04-03') -> April 3, 2026 in LOCAL time
# For interval [Apr 3, Apr 5], s = new Date('2026-04-03'), e = new Date('2026-04-05')
# s <= target (Apr 3 <= Apr 3) TRUE
# target <= e (Apr 3 <= Apr 5) TRUE

# But wait - new Date('2026-04-03') in local time could be different from UTC
# If timezone is UTC-5 (CST), new Date('2026-04-03') is Apr 3 00:00 CST = Apr 3 05:00 UTC
# new Date(iv.start) is Apr 3 00:00 UTC = Apr 2 19:00 CST
# So Apr 3 00:00 UTC <= Apr 3 00:00 UTC might be FALSE!

# Actually the issue might be the OPPOSITE direction - let me check the timezone issue
import datetime

target = datetime.datetime(2026, 4, 3, 0, 0, 0)  # This is local time
# But in JS, new Date('2026-04-03') parses as UTC

# The critical question: when JS does new Date('2026-04-03') and compares with new Date('2026-04-03'),
# does it use UTC or local time?

# Let me check by simulating:
# For Apr 4 (Saturday):
# target = new Date('2026-04-04') -> Apr 4 00:00 UTC
# For interval 2026-04-03 to 2026-04-05:
# s = new Date('2026-04-03') -> Apr 3 00:00 UTC
# e = new Date('2026-04-05') -> Apr 5 00:00 UTC
# Check: Apr 3 00:00 <= Apr 4 00:00 <= Apr 5 00:00 -> TRUE

# So the comparison should work...

# But what if the interval is actually [2026-04-03, 2026-04-04] for some reason?
# Then Apr 4 (Sat) would be in the interval
# Let me check what intervals actually cover Sat/Sun

from datetime import date as date_type

print("Checking April 2026 weekend days:")
for day in [3, 4, 5, 10, 11, 12]:
    d = f'2026-04-{day:02d}'
    wd = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][date_type.fromisoformat(d).weekday()]
    
    # What does JS query return?
    target_d = date_type.fromisoformat(d)
    result_custodian = None
    result_reason = None
    for iv in intervals:
        s = date_type.fromisoformat(iv['start'])
        e = date_type.fromisoformat(iv['end'])
        if s <= target_d <= e:
            result_custodian = iv['custodian']
            result_reason = iv['reason']
            break
    
    print(f"  {d} ({wd}): {result_custodian} | {result_reason}")

# Now let me check if maybe there's a second interval overriding
print()
print("All intervals that contain April 4 (Sat):")
target_d = date_type(2026, 4, 4)
for iv in intervals:
    s = date_type.fromisoformat(iv['start'])
    e = date_type.fromisoformat(iv['end'])
    if s <= target_d <= e:
        print(f"  {iv['start']} to {iv['end']}: {iv['custodian']} | {iv['reason']}")

print()
print("All intervals that contain April 5 (Sun):")
target_d = date_type(2026, 4, 5)
for iv in intervals:
    s = date_type.fromisoformat(iv['start'])
    e = date_type.fromisoformat(iv['end'])
    if s <= target_d <= e:
        print(f"  {iv['start']} to {iv['end']}: {iv['custodian']} | {iv['reason']}")