"""Verify Oct 9 and Oct 19 ICS raw data and current noschool_days list."""

import os, sys
BASE = r'C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal'
ICS_PATH = os.path.join(BASE, 'data', 'raw', 'rrisd_google_calendar.ics')
CAL_PATH = os.path.join(BASE, 'data', 'processed', 'rrisd_standard_calendar.json')

# 1. Read raw ICS events for Oct 9 and Oct 19
with open(ICS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

print("=" * 60)
print("RAW ICS EVENTS")
print("=" * 60)

in_event = False
for line in content.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
    if 'BEGIN:VEVENT' in line:
        in_event = True
        event_lines = []
    if in_event:
        event_lines.append(line.rstrip())
        if 'END:VEVENT' in line:
            event_text = '\n'.join(event_lines)
            if any(d in event_text for d in ('20261009', '20261012', '20261019')):
                print(f"\n--- Event ---")
                for l in event_lines:
                    if l.startswith(('DTSTART', 'DTEND', 'SUMMARY', 'DESCRIPTION')):
                        print(f"  {l}")
            in_event = False

print()

# 2. Show noschool_days in standard calendar
import json
with open(CAL_PATH, 'r', encoding='utf-8') as f:
    cal = json.load(f)

print("=" * 60)
print("CURRENT noschool_days in rrisd_standard_calendar.json")
print("=" * 60)
for sy in cal['schoolYears']:
    oct_days = [n for n in sy.get('noschool_days', []) if '2026-10' in n['date']]
    if oct_days:
        print(f"\nSY {sy['year']}:")
        for n in oct_days:
            print(f"  {n['date']}  =>  {n['label']['en']}")

# 3. is_noschool result
sys.path.insert(0, os.path.join(BASE, 'src'))
from calendar_fetcher_parser.fetch_rrisd_ics import is_noschool

print()
print("=" * 60)
print("is_noschool() RESULTS")
print("=" * 60)
test_cases = [
    ('Student Holiday/Staff Development', ''),
    ('YOU Day! Student & Staff Holiday', ''),
    ('Columbus Day', ''),
    ('End of 1st nine weeks', ''),
    ('YOU Day', ''),
    ('Staff Development Day', ''),
]
for summary, desc in test_cases:
    result = is_noschool(summary, desc)
    print(f"  is_noschool({summary!r}) = {result}")
