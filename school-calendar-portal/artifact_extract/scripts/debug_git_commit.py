import sys, subprocess, os, tempfile, hashlib

os.chdir('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal')
sys.path.insert(0, 'src')

print('CWD after chdir:', os.getcwd())

from static_web_generator.html_builder import get_git_commit, HTMLBuilder

# Check get_git_commit
commit = get_git_commit()
print('get_git_commit():', commit)

# Also check via subprocess directly
result = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).strip()
print('subprocess git rev-parse:', result)

# Check the template
from static_web_generator.html_builder import HTML_TEMPLATE
idx = HTML_TEMPLATE.find('commit:')
if idx >= 0:
    print('Template:', HTML_TEMPLATE[idx:idx+30])

# Check what HTMLBuilder.build actually does
import inspect
src = inspect.getsource(HTMLBuilder.build)
print('build() source (first 500 chars):')
print(src[:500])

# Now generate and check
ivs = [{'start':'2026-10-23','end':'2026-10-23','custodian':'mom','reason':'regular_school_day'}]
b = HTMLBuilder('RRISD', ivs, [])
with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
    tmp = f.name
b.build(tmp)
with open(tmp, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
idx2 = content.find('commit:')
print('Generated HTML footer:', content[idx2:idx2+25])
print('Generated HTML hash:', hashlib.sha1(content.encode('utf-8')).hexdigest())
print('Generated HTML size:', len(content))

os.unlink(tmp)