import os
os.chdir('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal')
import subprocess
result = subprocess.run(['python', 'main.py'], capture_output=True, text=True, cwd='.')
print(result.stdout)
print(result.stderr)