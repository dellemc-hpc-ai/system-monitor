import re

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src/custody_calculator.py'
content = open(path, encoding='utf-8').read()

old = '''        intervals = []
        d = all_starts[0]
        end_d = all_ends[-1]

        while d <= end_d:'''

new = '''        intervals = []
        # Start from May 22 two years before to capture pre-instruction gap days
        first_sy_start = all_starts[0]
        d = date(first_sy_start.year - 2, 5, 22)
        end_d = all_ends[-1]

        while d <= end_d:'''

if old not in content:
    print("OLD NOT FOUND")
else:
    content = content.replace(old, new, 1)
    open(path, 'w', encoding='utf-8').write(content)
    print("Done")
