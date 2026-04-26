import re

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src/custody_calculator.py'
content = open(path, encoding='utf-8').read()

old = '        # Start from May 22 of the prior calendar year to capture pre-school gap\n        first_sy_start = all_starts[0]\n        d = date(first_sy_start.year - 1, 5, 22)'
new = '        # Start from May 22 two years back to capture all gaps (including pre-instruction\n        # days like Aug 13-17 when teachers report but students haven\'t arrived)\n        first_sy_start = all_starts[0]\n        d = date(first_sy_start.year - 2, 5, 22)'

if old not in content:
    print("OLD NOT FOUND")
    idx = content.find('def compute_intervals')
    print(repr(content[idx:idx+800]))
else:
    content = content.replace(old, new, 1)
    open(path, 'w', encoding='utf-8').write(content)
    print("Done")
