import pdfplumber, re

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    notes = pdf.pages[0].extract_tables()[0][9][1]

print('Full notes text:')
print(repr(notes))
print()

# Find all date patterns
print('All date occurrences:')
for m in re.finditer(r'(\d+):', notes):
    print(f'  pos {m.start():3d}: {m.group(1)!r:>3} -> {notes[m.start():m.start()+60]!r}')
