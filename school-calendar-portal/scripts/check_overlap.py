import json, bisect
from datetime import date

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/espo_intervals.json', 'r', encoding='utf-8-sig') as f:
    ivs = json.load(f)

# Check overlaps
print('=== Overlapping intervals ===')
for i in range(len(ivs)):
    for j in range(i+1, len(ivs)):
        s1, e1 = date.fromisoformat(ivs[i]['start']), date.fromisoformat(ivs[i]['end'])
        s2, e2 = date.fromisoformat(ivs[j]['start']), date.fromisoformat(ivs[j]['end'])
        if s1 <= e2 and s2 <= e1:
            print(f"OVERLAP: {ivs[i]['start']}-{ivs[i]['end']} ({ivs[i]['custodian']}/{ivs[i]['reason']}) vs {ivs[j]['start']}-{ivs[j]['end']} ({ivs[j]['custodian']}/{ivs[j]['reason']})")

print('\n=== Query Nov 29 and Nov 30 ===')
starts = [date.fromisoformat(iv['start']) for iv in ivs]
for target in [date(2025,11,29), date(2025,11,30)]:
    idx = bisect.bisect_right(starts, target) - 1
    if idx >= 0:
        iv = ivs[idx]
        s, e = date.fromisoformat(iv['start']), date.fromisoformat(iv['end'])
        if s <= target <= e:
            print(f'{target}: {iv["custodian"]} / {iv["reason"]} (interval: {iv["start"]}-{iv["end"]})')
        else:
            print(f'{target}: NO MATCH (idx={idx}, interval: {iv["start"]}-{iv["end"]})')
    else:
        print(f'{target}: NO INTERVAL')