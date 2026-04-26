import sys, re

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/tx_custody_laws.md', encoding='utf-8') as f:
    content = f.read()

# Find §153.314 Holiday Possession section - it's buried in the auto-generated file
# The actual statute text starts with "The following provisions govern possession..."
idx = content.find('The following provisions govern possession')
if idx < 0:
    idx = content.find('possessory conservator shall have possession')
sys.stdout.write(f'Statute text found at: {idx}\n')

if idx >= 0:
    snippet = content[idx:idx+5000]
    # Clean up HTML artifacts for display
    clean = re.sub(r'<[^>]+>', '', snippet)
    sys.stdout.write(clean[:3000])