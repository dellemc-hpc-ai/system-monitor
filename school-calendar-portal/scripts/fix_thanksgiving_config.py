import re
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/run_full_process.py', encoding='utf-8') as f:
    content = f.read()
content = content.replace('"thanksgiving": {"odd_year_parent": "dad", "even_year_parent": "mom", "split_offset": 2}', '"thanksgiving": {"odd_year_parent": "dad", "even_year_parent": "mom"}')
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/run_full_process.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('done')
