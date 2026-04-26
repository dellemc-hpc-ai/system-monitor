import json

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(path, encoding='utf-8') as f:
    cal = json.load(f)

sy = cal['schoolYears'][0]
print('Before: SY start:', sy['start'], '| summer end:', sy['breaks']['summer']['end'])

# The school year officially starts Aug 13, but teachers work Aug 13-17
# while students start Aug 18. For custody purposes (kids in school?),
# shift SY start to Aug 18 so Aug 13-17 falls in the summer gap.
# summer_2025-2026 = May 22, 2025 - Aug 17, 2025 (prior summer, in 2024-2025 entry)
# summer_2025-2026 (in this entry) = May 22, 2026 - Aug 17, 2026 (after school ends)
# So Aug 13-17, 2025 is in the gap. Shift SY start to Aug 18.
sy['start'] = '2026-08-18'

# Wait - that shifts it to 2026. Let me reconsider.
# Actually the right fix: school year 2025-2026 should start Aug 18 (first student day)
# not Aug 13 (teacher day). So:
sy['start'] = '2025-08-18'
print('After:  SY start:', sy['start'], '| summer end:', sy['breaks']['summer']['end'])

with open(path, 'w', encoding='utf-8') as f:
    json.dump(cal, f, indent=2, ensure_ascii=False)
print('Saved')
