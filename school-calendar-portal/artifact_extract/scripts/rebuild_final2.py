import sys, os, json, hashlib

os.chdir('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal')
sys.path.insert(0, 'src')

from custody_interval_calculator.interval_generator import CustodyIntervalGenerator, load_calendar
from static_web_generator.html_builder import HTMLBuilder, HTML_TEMPLATE, I18N, get_git_commit

print('Working in:', os.getcwd())

path = 'data/processed/rrisd_standard_calendar.json'
cal = load_calendar(path)
gen = CustodyIntervalGenerator(cal, mode='espo')
ivs = gen.generate()
ivs_data = ivs.dump()

# Save intervals
ivs_path = 'data/processed/espo_intervals.json'
with open(ivs_path, 'w', encoding='utf-8') as f:
    json.dump(ivs_data, f, indent=2, ensure_ascii=False)
print(f'Saved {len(ivs_data)} intervals')

# Delete existing HTML files
for f in ['custody_school_calendar.html', 'output/custody_school_calendar.html']:
    if os.path.exists(f):
        os.unlink(f)
        print(f'Deleted: {f}')

# Build root HTML
commit = get_git_commit()
print('Using commit:', commit)

html = HTML_TEMPLATE.format(
    district='RRISD',
    title=I18N["en"]["title"],
    dad=I18N["en"]["dad"],
    mom=I18N["en"]["mom"],
    commit_hash=commit,
    espo_intervals_json=json.dumps(ivs_data, ensure_ascii=False),
    spo_intervals_json=json.dumps(ivs_data, ensure_ascii=False),
    i18n_json=json.dumps(I18N, ensure_ascii=False)
)
with open('custody_school_calendar.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Generated: custody_school_calendar.html')

# Build output HTML
os.makedirs('output', exist_ok=True)
HTMLBuilder('RRISD', ivs_data, ivs_data).build('output/custody_school_calendar.html')
print('Generated: output/custody_school_calendar.html')

# Verify
for f in ['custody_school_calendar.html', 'output/custody_school_calendar.html']:
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        content = fp.read()
    h = hashlib.sha1(content.encode('utf-8')).hexdigest()
    idx = content.find('commit:')
    footer = content[idx:idx+20] if idx >= 0 else 'NOT FOUND'
    print(f'{f}: hash={h}, footer={footer}')