"""
Debug: extract August school days directly from the calendar grid text.
August 2025 starts on Friday. Let me verify by parsing the grid text.
"""
import pdfplumber

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    tables = page.extract_tables()

# Table[0][8][1] = band 1 calendar text
grid = tables[0][8][1]
print("Grid text lines:")
for i, line in enumerate(grid.strip().split('\n')):
    nums = [n for n in line.split() if n.isdigit()]
    print(f"  row {i}: {line!r} -> numbers: {nums}")