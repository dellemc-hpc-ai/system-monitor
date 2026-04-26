from datetime import date, timedelta
import calendar

c = calendar.Calendar()
fridays = sorted([date(2026, 4, day[0]) for day in c.itermonthdays2(2026, 4) if day[0] != 0 and day[1] == 4])
print("April 2026 Fridays:")
for i, f in enumerate(fridays, 1):
    print(f"  Friday #{i}: {f} ({f.strftime('%A')})")

print()
print("August 2025 Fridays:")
fridays_aug = sorted([date(2025, 8, day[0]) for day in c.itermonthdays2(2025, 8) if day[0] != 0 and day[1] == 4])
for i, f in enumerate(fridays_aug, 1):
    print(f"  Friday #{i}: {f}")

print()
print("=== Thanksgiving 2025 Thu-Fri-Sat-Sun ===")
import json
d = json.load(open(r'C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal\data\processed\espo_intervals.json'))
for iv in d['intervals']:
    if '2025-11' in iv['start'] or '2025-11' in iv['end']:
        print(f"{iv['start']} to {iv['end']}: {iv['custodian']} | {iv['reason']}")