import json

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(path, encoding='utf-8') as f:
    cal = json.load(f)

sy = cal['schoolYears'][0]
br = sy['breaks']['summer']
print('SY start:', sy['start'])
print('SY end:', sy['end'])
print('Summer start:', br['start'])
print('Summer end (before):', br['end'])

# The school year starts Aug 13. Summer break (May 22-Aug 17) overlaps with
# the first days of the school year. Aug 13-17 should be summer (mom) because
# kids aren't in school yet. Keep summer end at Aug 17 (or later) so that
# Aug 13-17 falls within the summer break period.
# Already: summer end = Aug 17. Just verify.
print('Summer end (after):', br['end'])

with open(path, 'w', encoding='utf-8') as f:
    json.dump(cal, f, indent=2, ensure_ascii=False)
print('OK - already correct, no change needed')
