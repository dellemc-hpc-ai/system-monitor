import json, bisect
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

starts = [date.fromisoformat(iv['start']) for iv in ivs]
target = date(2025, 12, 18)
idx = bisect.bisect_right(starts, target) - 1
if idx >= 0:
    iv = ivs[idx]
    s, e = date.fromisoformat(iv['start']), date.fromisoformat(iv['end'])
    if s <= target <= e:
        print(f'{target}: {iv["custodian"]} / {iv["reason"]} (interval: {iv["start"]}-{iv["end"]})')
    else:
        print(f'{target}: gap (interval: {iv["start"]}-{iv["end"]})')

print('\n--- Dec 2025 intervals ---')
for iv in ivs:
    if '2025-12-01' <= iv['start'] <= '2025-12-31':
        print(iv['start'], '-', iv['end'], iv['custodian'], '/', iv['reason'])
    elif '2025-11-30' <= iv['end'] <= '2025-12-31':
        print(iv['start'], '-', iv['end'], iv['custodian'], '/', iv['reason'])

print('\n--- Christmas rule for 2025 ---')
# Odd year -> Dad first half
# 2025 is odd year
# Christmas: Dec 19 - Jan 5
# Split at Dec 29 (per §153.314: "afternoon of December 28" or midnight Dec 29)
print("2025 is odd year -> Dad gets first half")
print("Christmas 2025: Dec 19 - Jan 5")
print("First half (Dad): Dec 19 - Dec 28")
print("Second half (Mom): Dec 29 - Jan 5")
print()
print("But what's the interval for Dec 18?")
print("Dec 18 is BEFORE Christmas break starts (Dec 19)")
print("So Dec 18 should be regular school day or Thanksgiving...")
print("Actually Dec 18 2025 is a Thursday - check if it is regular school or something else")